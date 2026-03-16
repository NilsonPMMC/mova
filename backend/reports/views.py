import logging
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q
from pgvector.django import L2Distance, CosineDistance
from core.services.vector_service import VectorService
from intelligence.services import haversine_distance_meters
from .models import Manifestation, ManifestationCategory, ManifestationUpdate, Attachment, SatisfactionSurvey, WorkOrder, ServicePartner
from intelligence.models import NLPAnalysis

logger = logging.getLogger(__name__)
from .serializers import (
    ManifestationCreateSerializer,
    ManifestationDetailSerializer,
    ManifestationListSerializer,
    ManifestationCategorySerializer,
    ManifestationUpdateSerializer,
    AttachmentSerializer,
    TrackManifestationSerializer,
    SatisfactionSurveySerializer,
    WorkOrderSerializer,
    WorkOrderCreateSerializer,
    ServicePartnerSerializer,
)


class ManifestationViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar manifestações
    
    Permissões:
    - create (POST): AllowAny - Cidadão anônimo pode criar
    - list, retrieve, update, destroy: IsAuthenticated - Apenas funcionários
    """
    queryset = Manifestation.objects.select_related(
        'citizen',
        'category',
        'resolved_by',
        'potential_duplicate',
    ).prefetch_related(
        'updates',
        'attachments',
        'nlp_analysis',
        'related_manifestations',
        'related_group',
    ).all()
    
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        """
        Retorna o serializer apropriado baseado na action
        """
        if self.action == 'create':
            return ManifestationCreateSerializer
        elif self.action == 'list':
            return ManifestationListSerializer
        else:
            return ManifestationDetailSerializer

    def get_permissions(self):
        """
        Permissões dinâmicas:
        - create: AllowAny (qualquer um pode criar manifestação)
        - by_protocol: AllowAny (cidadão pode buscar por protocolo)
        - track: AllowAny (rastreio público por protocolo)
        - mine: AllowAny (listagem por CPF no MVP)
        - analyze_draft: AllowAny (cidadão pode analisar rascunho)
        - outros: IsAuthenticated (apenas funcionários autenticados)
        """
        if self.action in ['create', 'by_protocol', 'analyze_draft', 'track', 'mine', 'rate']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def partial_update(self, request, *args, **kwargs):
        """
        Validação extra de integridade de status:
        manifestações já concluídas (RESOLVED/CLOSED) não podem regredir de status
        via PATCH genérico. Para isso, deve existir um fluxo explícito de reabertura.
        """
        instance = self.get_object()
        current_status = instance.status
        new_status = request.data.get('status')

        if (
            new_status
            and new_status != current_status
            and current_status in [Manifestation.STATUS_RESOLVED, Manifestation.STATUS_CLOSED]
        ):
            return Response(
                {'detail': 'Manifestações concluídas não podem ser movidas. Utilize a função de reabertura se necessário.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return super().partial_update(request, *args, **kwargs)

    def get_queryset(self):
        """
        Filtros customizados para listagem
        """
        queryset = self.queryset
        if self.action == 'list':
            queryset = queryset.prefetch_related('related_manifestations', 'related_group')

        # Controle de acesso por setor
        user = self.request.user
        if user.is_authenticated:
            # Superadmin pode ver tudo (mas pode filtrar via query param)
            if not user.is_superuser and user.sector:
                # Usuário comum: apenas manifestações do seu setor E já despachadas
                queryset = queryset.filter(
                    category__default_sector__iexact=user.sector,
                ).exclude(status=Manifestation.STATUS_WAITING_TRIAGE)
            # Se superadmin e tem query param sector, aplicar filtro
            elif user.is_superuser:
                sector_param = self.request.query_params.get('sector', None)
                if sector_param:
                    queryset = queryset.filter(
                        category__default_sector__iexact=sector_param.strip()
                    )

        # Filtros opcionais via query params
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filtro para mostrar apenas manifestações principais (pais) no inbox
        # Exclui duplicatas (filhas) que têm related_group_id preenchido
        only_primary = self.request.query_params.get('only_primary', 'false').lower() == 'true'
        if only_primary:
            queryset = queryset.filter(
                Q(is_primary=True) | Q(related_group__isnull=True)
            )
        
        # Entrada do board setorial: encaminhadas para o setor, ainda sem OS
        forwarded_sector = self.request.query_params.get('forwarded_sector', None)
        if forwarded_sector:
            queryset = queryset.filter(
                status=Manifestation.STATUS_FORWARDED,
                category__default_sector__iexact=forwarded_sector.strip(),
                work_order__isnull=True,
            )
        
        category_filter = self.request.query_params.get('category', None)
        if category_filter:
            queryset = queryset.filter(category_id=category_filter)
        
        origin_filter = self.request.query_params.get('origin', None)
        if origin_filter:
            queryset = queryset.filter(origin=origin_filter)
        
        # Busca por protocolo ou descrição
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(protocol__icontains=search) |
                Q(description__icontains=search) |
                Q(location_address__icontains=search)
            )
        
        # Ordenação
        ordering = self.request.query_params.get('ordering', '-created_at')
        if ordering:
            queryset = queryset.order_by(ordering)
        
        return queryset

    def create(self, request, *args, **kwargs):
        """
        Cria uma nova manifestação
        Permite criação anônima (AllowAny)
        Suporta upload de arquivos via multipart/form-data
        """
        # Montar payload explícito a partir de POST e FILES para evitar
        # problemas de parsing (Content-Type, boundary, ListField de arquivos)
        if request.content_type and 'multipart' in request.content_type and request.FILES:
            files_list = list(request.FILES.getlist('files') or request.FILES.getlist('files[]'))
            post_data = getattr(request, 'POST', None) or request.data
            if hasattr(post_data, 'getlist'):
                file_descriptions_list = list(post_data.getlist('file_descriptions', []))
            else:
                fd = post_data.get('file_descriptions', [])
                file_descriptions_list = fd if isinstance(fd, list) else [fd] if fd else []
            file_descriptions_list = [str(d).strip() if d is not None else '' for d in file_descriptions_list]
            while len(file_descriptions_list) < len(files_list):
                file_descriptions_list.append('')
            file_descriptions_list = file_descriptions_list[: len(files_list)]
            # Copiar campos do formulário (um valor por chave, exceto files/file_descriptions)
            data = {}
            if hasattr(post_data, 'keys'):
                for key in post_data.keys():
                    if key in ('files', 'file_descriptions'):
                        continue
                    data[key] = post_data.get(key)
            data['files'] = files_list
            data['file_descriptions'] = file_descriptions_list
        else:
            raw = request.data
            data = raw.copy() if hasattr(raw, 'copy') and callable(getattr(raw, 'copy')) else (dict(raw) if hasattr(raw, 'keys') else {})
            if not isinstance(data, dict):
                data = {}

        serializer = self.get_serializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        detail_serializer = ManifestationDetailSerializer(instance, context={'request': request})
        return Response(
            detail_serializer.data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def add_update(self, request, pk=None):
        """
        Adiciona um andamento/atualização à manifestação
        """
        manifestation = self.get_object()
        serializer = ManifestationUpdateSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        # Atualizar status da manifestação se fornecido
        new_status = serializer.validated_data.get('new_status')
        if new_status:
            manifestation.status = new_status
            manifestation.save()
        
        # Criar o andamento
        update = serializer.save(
            manifestation=manifestation,
            updated_by=request.user
        )
        
        return Response(
            ManifestationUpdateSerializer(update).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def resolve(self, request, pk=None):
        """
        Marca uma manifestação como resolvida
        """
        manifestation = self.get_object()
        manifestation.status = Manifestation.STATUS_RESOLVED
        manifestation.resolved_by = request.user
        from django.utils import timezone
        manifestation.resolved_at = timezone.now()
        manifestation.save()
        
        serializer = self.get_serializer(manifestation)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def close(self, request, pk=None):
        """
        Encerra uma manifestação
        """
        manifestation = self.get_object()
        manifestation.status = Manifestation.STATUS_CLOSED
        manifestation.save()
        
        serializer = self.get_serializer(manifestation)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny], url_path='by-protocol/(?P<protocol>[^/.]+)')
    def by_protocol(self, request, protocol=None):
        """
        Busca manifestação por protocolo (público para cidadão acompanhar)
        """
        try:
            manifestation = Manifestation.objects.select_related(
                'citizen',
                'category',
                'resolved_by'
            ).prefetch_related(
                'updates',
                'attachments'
            ).get(protocol=protocol)
            
            serializer = ManifestationDetailSerializer(manifestation)
            return Response(serializer.data)
        except Manifestation.DoesNotExist:
            return Response(
                {'error': 'Manifestação não encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny], url_path='track/(?P<protocol>[^/.]+)')
    def track(self, request, protocol=None):
        """
        Endpoint público para rastreio de manifestação por protocolo
        Retorna apenas dados seguros, sem informações sensíveis
        """
        try:
            manifestation = Manifestation.objects.select_related(
                'category',
                'satisfaction_survey',
                'nlp_analysis',
            ).prefetch_related(
                'updates',
                'attachments',
            ).get(protocol=protocol)
            
            serializer = TrackManifestationSerializer(manifestation, context={'request': request})
            return Response(serializer.data)
        except Manifestation.DoesNotExist:
            return Response(
                {'error': 'Protocolo não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated], url_path='finish')
    def finish(self, request, pk=None):
        """
        Conclui uma manifestação (e todas as filhas se for cluster).
        Recebe: solution_note (obrigatório), solution_photo (opcional).
        Atualiza status para RESOLVED.
        """
        manifestation = self.get_object()
        
        # Validar permissão: usuário deve ser do setor ou superadmin
        user = request.user
        if not user.is_superuser:
            if not user.sector or manifestation.category is None:
                return Response(
                    {'detail': 'Você não tem permissão para concluir esta manifestação.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            if manifestation.category.default_sector and \
               manifestation.category.default_sector.upper() != user.sector.upper():
                return Response(
                    {'detail': 'Você não tem permissão para concluir manifestações deste setor.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        solution_note = request.data.get('solution_note', '').strip()
        if not solution_note:
            return Response(
                {'detail': 'solution_note é obrigatório.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        solution_photo = request.FILES.get('solution_photo', None)
        
        try:
            from django.utils import timezone
            
            # Atualizar manifestação principal
            manifestation.status = Manifestation.STATUS_RESOLVED
            manifestation.resolved_by = user
            manifestation.resolved_at = timezone.now()
            manifestation.save(update_fields=['status', 'resolved_by', 'resolved_at'])
            
            # Criar atualização com nota de solução
            ManifestationUpdate.objects.create(
                manifestation=manifestation,
                new_status=Manifestation.STATUS_RESOLVED,
                public_note=f'Situação resolvida: {solution_note}',
                internal_note=f'Solução aplicada por {user.get_full_name() or user.username}',
                updated_by=user,
            )
            
            # Se for manifestação "Pai" (cluster), atualizar todas as filhas também
            if manifestation.is_primary:
                children = manifestation.related_manifestations.all()
                for child in children:
                    child.status = Manifestation.STATUS_RESOLVED
                    child.resolved_by = user
                    child.resolved_at = timezone.now()
                    child.save(update_fields=['status', 'resolved_by', 'resolved_at'])
                    
                    # Criar atualização para cada filha
                    ManifestationUpdate.objects.create(
                        manifestation=child,
                        new_status=Manifestation.STATUS_RESOLVED,
                        public_note=f'Situação resolvida: {solution_note}',
                        internal_note=f'Solução aplicada por {user.get_full_name() or user.username} (agrupada com {manifestation.protocol})',
                        updated_by=user,
                    )
            
            # Se houver foto, criar anexo
            if solution_photo:
                Attachment.objects.create(
                    manifestation=manifestation,
                    file=solution_photo,
                    description='Foto da solução aplicada',
                    uploaded_by=user,
                )
            
            # Retornar detalhes atualizados
            serializer = ManifestationDetailSerializer(manifestation, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f'Erro ao concluir manifestação {manifestation.protocol}: {str(e)}', exc_info=True)
            return Response(
                {'detail': f'Erro ao concluir manifestação: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny], url_path='mine')
    def mine(self, request):
        """
        Lista manifestações de um cidadão por CPF (MVP - temporário)
        Em produção, será substituído por autenticação JWT
        """
        cpf = request.query_params.get('cpf', '').strip()
        if not cpf:
            return Response(
                {'error': 'Parâmetro "cpf" é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Limpar CPF (remover pontos e traços)
        import re
        cpf_clean = re.sub(r'[^\d]', '', cpf)
        
        # Buscar usuário por CPF
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            user = User.objects.get(cpf=cpf_clean)
            manifestations = Manifestation.objects.filter(
                citizen=user
            ).select_related(
                'category'
            ).order_by('-created_at')
            
            serializer = ManifestationListSerializer(manifestations, many=True)
            return Response({
                'count': manifestations.count(),
                'results': serializer.data
            })
        except User.DoesNotExist:
            return Response({
                'count': 0,
                'results': []
            })
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated], url_path='search_similar')
    def search_similar(self, request):
        """
        Busca semântica: encontra manifestações similares usando embeddings.
        
        Input:
        {
            "text": "texto da nova reclamação",
            "limit": 5 (opcional, padrão 5),
            "distance_type": "cosine" ou "l2" (opcional, padrão "cosine")
        }
        
        Output:
        {
            "query_text": "...",
            "results": [
                {
                    "id": "...",
                    "protocol": "...",
                    "description": "...",
                    "similarity_score": 0.95,
                    "distance": 0.05,
                    "status": "...",
                    "created_at": "..."
                },
                ...
            ]
        }
        """
        text = request.data.get('text', '').strip()
        if not text:
            return Response(
                {'error': 'Campo "text" é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        limit = int(request.data.get('limit', 5))
        distance_type = request.data.get('distance_type', 'cosine').lower()
        
        if distance_type not in ['cosine', 'l2']:
            return Response(
                {'error': 'distance_type deve ser "cosine" ou "l2"'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Gerar embedding do texto de busca
            vector_service = VectorService()
            query_embedding = vector_service.get_embedding(text)
            
            # Buscar manifestações similares usando pgvector
            queryset = Manifestation.objects.filter(
                embedding__isnull=False  # Apenas manifestações com embedding
            )
            
            # Aplicar distância (Cosseno ou L2)
            if distance_type == 'cosine':
                queryset = queryset.annotate(
                    distance=CosineDistance('embedding', query_embedding)
                ).order_by('distance')[:limit]
            else:  # L2
                queryset = queryset.annotate(
                    distance=L2Distance('embedding', query_embedding)
                ).order_by('distance')[:limit]
            
            # Preparar resultados
            results = []
            for manifestation in queryset:
                distance_value = float(manifestation.distance)
                # Calcular score de similaridade (1 - distance para cosseno, ou inverso para L2)
                if distance_type == 'cosine':
                    similarity_score = 1.0 - distance_value  # Cosseno: menor distância = maior similaridade
                else:
                    # Para L2, normalizar (assumindo distância máxima de ~2.0)
                    similarity_score = max(0.0, 1.0 - (distance_value / 2.0))
                
                results.append({
                    'id': str(manifestation.id),
                    'protocol': manifestation.protocol,
                    'description': manifestation.description[:200] + '...' if len(manifestation.description) > 200 else manifestation.description,
                    'similarity_score': round(similarity_score, 4),
                    'distance': round(distance_value, 6),
                    'status': manifestation.status,
                    'status_display': manifestation.get_status_display(),
                    'created_at': manifestation.created_at.isoformat(),
                    'category': manifestation.category.name if manifestation.category else None,
                })
            
            return Response({
                'query_text': text,
                'distance_type': distance_type,
                'limit': limit,
                'count': len(results),
                'results': results
            })
            
        except Exception as e:
            import traceback
            logger.error(f"Erro na busca semântica: {str(e)}\n{traceback.format_exc()}")
            return Response(
                {'error': f'Erro ao realizar busca semântica: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated], url_path='search_similar')
    def search_similar(self, request):
        """
        Busca semântica: encontra manifestações similares usando embeddings.
        
        Input:
        {
            "text": "texto da nova reclamação",
            "limit": 5 (opcional, padrão 5),
            "distance_type": "cosine" ou "l2" (opcional, padrão "cosine")
        }
        
        Output:
        {
            "query_text": "...",
            "results": [
                {
                    "id": "...",
                    "protocol": "...",
                    "description": "...",
                    "similarity_score": 0.95,
                    "distance": 0.05,
                    "status": "...",
                    "created_at": "..."
                },
                ...
            ]
        }
        """
        text = request.data.get('text', '').strip()
        if not text:
            return Response(
                {'error': 'Campo "text" é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        limit = int(request.data.get('limit', 5))
        distance_type = request.data.get('distance_type', 'cosine').lower()
        
        if distance_type not in ['cosine', 'l2']:
            return Response(
                {'error': 'distance_type deve ser "cosine" ou "l2"'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Gerar embedding do texto de busca
            vector_service = VectorService()
            query_embedding = vector_service.get_embedding(text)
            
            # Buscar manifestações similares usando pgvector
            queryset = Manifestation.objects.filter(
                embedding__isnull=False  # Apenas manifestações com embedding
            )
            
            # Aplicar distância (Cosseno ou L2)
            if distance_type == 'cosine':
                queryset = queryset.annotate(
                    distance=CosineDistance('embedding', query_embedding)
                ).order_by('distance')[:limit]
            else:  # L2
                queryset = queryset.annotate(
                    distance=L2Distance('embedding', query_embedding)
                ).order_by('distance')[:limit]
            
            # Preparar resultados
            results = []
            for manifestation in queryset:
                distance_value = float(manifestation.distance)
                # Calcular score de similaridade (1 - distance para cosseno, ou inverso para L2)
                if distance_type == 'cosine':
                    similarity_score = 1.0 - distance_value  # Cosseno: menor distância = maior similaridade
                else:
                    # Para L2, normalizar (assumindo distância máxima de ~2.0)
                    similarity_score = max(0.0, 1.0 - (distance_value / 2.0))
                
                results.append({
                    'id': str(manifestation.id),
                    'protocol': manifestation.protocol,
                    'description': manifestation.description[:200] + '...' if len(manifestation.description) > 200 else manifestation.description,
                    'similarity_score': round(similarity_score, 4),
                    'distance': round(distance_value, 6),
                    'status': manifestation.status,
                    'status_display': manifestation.get_status_display(),
                    'created_at': manifestation.created_at.isoformat(),
                    'category': manifestation.category.name if manifestation.category else None,
                })
            
            return Response({
                'query_text': text,
                'distance_type': distance_type,
                'limit': limit,
                'count': len(results),
                'results': results
            })
            
        except Exception as e:
            import traceback
            logger.error(f"Erro na busca semântica: {str(e)}\n{traceback.format_exc()}")
            return Response(
                {'error': f'Erro ao realizar busca semântica: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny], url_path='rate/(?P<protocol>[^/.]+)')
    def rate(self, request, protocol=None):
        """
        Avaliação de satisfação (rating 1-5 + comentário opcional).
        Só aceita se a manifestação estiver com status RESOLVED.
        """
        try:
            manifestation = Manifestation.objects.get(protocol=protocol)
        except Manifestation.DoesNotExist:
            return Response(
                {'error': 'Protocolo não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        if manifestation.status != Manifestation.STATUS_RESOLVED:
            return Response(
                {'error': 'Só é possível avaliar manifestações já resolvidas.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if hasattr(manifestation, 'satisfaction_survey') and manifestation.satisfaction_survey:
            return Response(
                {'error': 'Esta manifestação já foi avaliada.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = SatisfactionSurveySerializer(
            data=request.data,
            context={'manifestation': manifestation}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny], url_path='analyze_draft')
    def analyze_draft(self, request):
        """
        Endpoint para pré-análise de texto sem salvar no banco.
        Retorna análise da IA para o usuário validar antes de criar a manifestação.
        """
        from rest_framework.response import Response
        from rest_framework import status
        from intelligence.services import LLMService
        
        description = request.data.get('description', '').strip()
        
        if not description:
            return Response(
                {'error': 'Campo "description" é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Chamar análise sem salvar no banco
        analysis_result = LLMService.analyze_text(
            text=description,
            save_to_db=False,
            manifestation_instance=None
        )
        
        if not analysis_result:
            return Response(
                {'error': 'Erro ao analisar texto. Tente novamente.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Preparar resposta formatada (inclui múltiplas demandas para cross-sell no frontend)
        # Enriquecer all_demands com SLA por demanda (quando possível)
        raw_all_demands = analysis_result.get('all_demands', []) or []
        enriched_all_demands = []
        for d in raw_all_demands:
            try:
                macro = (d or {}).get('macro_category') if isinstance(d, dict) else None
                detail = (d or {}).get('category_detail') if isinstance(d, dict) else None
                urgency = (d or {}).get('urgency_level') if isinstance(d, dict) else None
                specific_text = (d or {}).get('specific_text') if isinstance(d, dict) else None

                cat = None
                if macro:
                    cat = ManifestationCategory.objects.filter(
                        name__iexact=str(macro).strip(),
                        is_active=True,
                    ).first()

                enriched_all_demands.append({
                    'macro_category': str(macro).strip() if macro else '',
                    'category_detail': str(detail).strip() if detail else '',
                    'specific_text': str(specific_text).strip() if specific_text else '',
                    'urgency_level': urgency if isinstance(urgency, int) else analysis_result.get('urgency_level', 3),
                    'sla_hours': getattr(cat, 'sla_hours', None),
                })
            except Exception:
                # Nunca quebrar analyze_draft por enriquecimento
                continue

        response_data = {
            'summary': analysis_result.get('summary', ''),
            'intent': analysis_result.get('intent', 'COMPLAINT'),
            'intent_label': dict(NLPAnalysis.INTENT_CHOICES).get(analysis_result.get('intent', 'COMPLAINT'), 'Reclamação'),
            'suggested_category': None,
            'suggested_category_name': analysis_result.get('suggested_category_name', ''),
            'category': analysis_result.get('category', ''),
            'category_detail': analysis_result.get('category_detail', ''),
            'urgency_level': analysis_result.get('urgency_level', 3),
            'urgency_label': {
                1: 'Muito Baixa',
                2: 'Baixa',
                3: 'Média',
                4: 'Alta',
                5: 'Crítica'
            }.get(analysis_result.get('urgency_level', 3), 'Média'),
            'sentiment_score': analysis_result.get('sentiment_score', 0.0),
            'keywords': analysis_result.get('keywords', []),
            'has_multiple_demands': analysis_result.get('has_multiple_demands', False),
            'all_demands': analysis_result.get('all_demands', []),
            'all_demands_enriched': enriched_all_demands,
            'service_data': analysis_result.get('service_data'),
        }
        
        # Incluir dados da categoria se encontrada
        suggested_category = analysis_result.get('suggested_category')
        if suggested_category:
            from .serializers import ManifestationCategorySerializer
            response_data['suggested_category'] = ManifestationCategorySerializer(suggested_category).data
            response_data['sla_hours'] = suggested_category.sla_hours
        
        return Response(response_data, status=status.HTTP_200_OK)


class ManifestationCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet apenas para leitura de categorias
    """
    queryset = ManifestationCategory.objects.filter(is_active=True)
    serializer_class = ManifestationCategorySerializer
    permission_classes = [permissions.AllowAny]  # Categorias públicas para seleção

    def get_queryset(self):
        """
        Retorna apenas categorias ativas, opcionalmente filtradas por parent
        """
        queryset = self.queryset
        parent_id = self.request.query_params.get('parent', None)
        
        if parent_id:
            queryset = queryset.filter(parent_id=parent_id)
        else:
            # Por padrão, retorna apenas categorias raiz (sem parent)
            queryset = queryset.filter(parent__isnull=True)
        
        return queryset.order_by('name')


class WorkOrderViewSet(viewsets.ModelViewSet):
    """
    Ordens de Serviço para o board setorial (Kanban).
    list: filtre por ?sector=OBRAS (obrigatório para o board).
    create: body { sector, manifestation_ids[], team_leader?, scheduled_date? }.
    partial_update: atualiza status, block_reason, team_leader, scheduled_date.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = WorkOrderSerializer

    def get_queryset(self):
        qs = WorkOrder.objects.prefetch_related(
            'manifestations',
            'manifestations__nlp_analysis',
            'manifestations__related_group',
        ).select_related('team_leader')
        
        # Controle de acesso por setor
        user = self.request.user
        if user.is_authenticated:
            if not user.is_superuser and user.sector:
                # Usuário comum: apenas OS do seu setor
                qs = qs.filter(sector__iexact=user.sector)
            elif user.is_superuser:
                # Superadmin: pode filtrar via query param
                sector = self.request.query_params.get('sector', '').strip()
                if sector:
                    qs = qs.filter(sector__iexact=sector)
        
        return qs.order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'create':
            return WorkOrderCreateSerializer
        return WorkOrderSerializer

    def perform_update(self, serializer):
        serializer.save()


class NearestPartnersView(APIView):
    """
    Retorna parceiros ordenados pela distância e filtrados por tipo de animal.
    Ex: /api/v1/reports/nearest-partners/?lat=-23.5&lon=-46.2&animal_type=Gato Fêmea
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        lat = request.query_params.get('lat')
        lon = request.query_params.get('lon')
        animal_type = request.query_params.get('animal_type')

        if not lat or not lon:
            return Response(
                {"detail": "Latitude e longitude são obrigatórias."},
                status=status.HTTP_400_BAD_REQUEST
            )

        partners = ServicePartner.objects.filter(is_active=True).prefetch_related('schedules')
        results = []

        for partner in partners:
            if animal_type and partner.accepted_types:
                accepted_lower = [str(t).lower().strip() for t in partner.accepted_types]
                if animal_type.lower().strip() not in accepted_lower:
                    continue

            distance = float('inf')
            if partner.latitude and partner.longitude:
                try:
                    distance = haversine_distance_meters(
                        float(lat), float(lon),
                        float(partner.latitude), float(partner.longitude)
                    )
                except (TypeError, ValueError):
                    pass

            partner.distance_meters = distance
            results.append(partner)

        results.sort(key=lambda x: x.distance_meters)
        serializer = ServicePartnerSerializer(results, many=True)
        return Response(serializer.data)
