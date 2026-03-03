from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from core.validators import validate_cpf as validate_cpf_core
from .models import ManifestationCategory, Manifestation, ManifestationUpdate, Attachment, SatisfactionSurvey, WorkOrder
from intelligence.serializers import NLPAnalysisSerializer
import os
import re

User = get_user_model()


class ManifestationCategorySerializer(serializers.ModelSerializer):
    """
    Serializer básico para categorias de manifestações
    """
    full_path = serializers.SerializerMethodField()

    class Meta:
        model = ManifestationCategory
        fields = ['id', 'name', 'slug', 'full_path', 'sla_hours', 'is_active', 'default_sector']
        read_only_fields = ['id', 'slug']

    def get_full_path(self, obj):
        """Retorna o caminho completo da categoria incluindo pais"""
        return obj.get_full_path()


class ManifestationCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para criação de manifestações (usado por cidadãos)
    Campos limitados e protocolo/status gerados automaticamente
    Suporta identificação do cidadão (soft auth) e upload de anexos
    """
    category = serializers.PrimaryKeyRelatedField(
        queryset=ManifestationCategory.objects.filter(is_active=True),
        required=False,
        allow_null=True
    )
    
    # Campos opcionais para identificação do cidadão
    citizen_name = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        write_only=True,
        help_text='Nome do cidadão (opcional)'
    )
    citizen_email = serializers.EmailField(
        required=False,
        allow_blank=True,
        write_only=True,
        help_text='Email do cidadão (opcional)'
    )
    citizen_cpf = serializers.CharField(
        max_length=14,
        required=False,
        allow_blank=True,
        write_only=True,
        help_text='CPF do cidadão (obrigatório se não anônimo)'
    )
    citizen_phone = serializers.CharField(
        max_length=20,
        required=False,
        allow_blank=True,
        write_only=True,
        help_text='Celular do cidadão (opcional, para WhatsApp)'
    )
    citizen_correction = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True,
        help_text='Observação adicional do cidadão caso discorde da análise da IA'
    )
    
    # Campo para upload de múltiplos arquivos
    files = serializers.ListField(
        child=serializers.FileField(),
        required=False,
        allow_empty=True,
        write_only=True,
        help_text='Lista de arquivos anexos (imagens ou PDF, máximo 5MB cada)'
    )
    file_descriptions = serializers.ListField(
        child=serializers.CharField(max_length=255, allow_blank=True, required=False),
        required=False,
        allow_empty=True,
        write_only=True,
        help_text='Descrições opcionais para cada arquivo (mesma ordem de files)'
    )
    
    def to_internal_value(self, data):
        """
        Processa os dados antes da validação, garantindo que arquivos sejam buscados de request.FILES
        """
        # Buscar arquivos diretamente de request.FILES se disponível
        request = self.context.get('request')
        if request and hasattr(request, 'FILES'):
            # Se arquivos vieram via FormData, buscar de request.FILES
            files_list = []
            if 'files' in request.FILES:
                files_list = list(request.FILES.getlist('files'))
            elif 'files[]' in request.FILES:
                files_list = list(request.FILES.getlist('files[]'))
            
            # Criar uma cópia mutável de data se necessário
            if files_list or 'file_descriptions' in data or hasattr(request.data, 'getlist'):
                if hasattr(data, '_mutable'):
                    data = data.copy()
                elif isinstance(data, dict):
                    data = data.copy()
                else:
                    # Se for QueryDict, converter para dict mutável
                    data = dict(data)
            
            if files_list:
                data['files'] = files_list
                
                # Processar descrições de request.data se disponível
                file_descriptions_list = []
                if hasattr(request.data, 'getlist'):
                    file_descriptions_list = request.data.getlist('file_descriptions', [])
                elif 'file_descriptions' in data:
                    if isinstance(data['file_descriptions'], list):
                        file_descriptions_list = data['file_descriptions']
                    elif isinstance(data['file_descriptions'], str):
                        import json
                        try:
                            file_descriptions_list = json.loads(data['file_descriptions'])
                        except:
                            file_descriptions_list = []
                
                # Garantir que file_descriptions seja uma lista de strings válidas
                # com o mesmo tamanho de files_list (preencher com strings vazias se necessário)
                if file_descriptions_list:
                    # Converter para strings válidas
                    file_descriptions_list = [
                        str(desc).strip() if desc else '' 
                        for desc in file_descriptions_list
                    ]
                else:
                    # Se não houver descrições, criar lista vazia do tamanho dos arquivos
                    file_descriptions_list = [''] * len(files_list)
                
                # Garantir que tenha o mesmo tamanho de files_list
                while len(file_descriptions_list) < len(files_list):
                    file_descriptions_list.append('')
                
                data['file_descriptions'] = file_descriptions_list[:len(files_list)]
        
        return super().to_internal_value(data)

    class Meta:
        model = Manifestation
        fields = [
            'description',
            'category',
            'location_address',
            'latitude',
            'longitude',
            'is_anonymous',
            'origin',
            'citizen_name',
            'citizen_email',
            'citizen_cpf',
            'citizen_phone',
            'citizen_correction',
            'files',
            'file_descriptions',
        ]
        extra_kwargs = {
            'description': {'required': True},
            'location_address': {'required': False, 'allow_blank': True},
            'latitude': {'required': False, 'allow_null': True},
            'longitude': {'required': False, 'allow_null': True},
            'is_anonymous': {'default': False},
            'origin': {'default': Manifestation.ORIGIN_WEB},
        }

    def validate_citizen_cpf(self, value):
        """Validação matemática do CPF (dígitos verificadores)."""
        if not value or not value.strip():
            return value
        try:
            normalized = validate_cpf_core(value)
            # Devolver no formato 000.000.000-00 para consistência (opcional)
            return normalized
        except DjangoValidationError as e:
            raise serializers.ValidationError("CPF inválido. Verifique os números.")

    def validate(self, data):
        """Validação customizada"""
        # Se latitude ou longitude fornecida, ambas devem estar presentes
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        if (latitude is not None and longitude is None) or \
           (latitude is None and longitude is not None):
            raise serializers.ValidationError(
                "Latitude e longitude devem ser fornecidas juntas."
            )
        
        is_anonymous = data.get('is_anonymous', False)
        citizen_name = data.get('citizen_name', '').strip()
        citizen_email = data.get('citizen_email', '').strip()
        citizen_cpf_raw = data.get('citizen_cpf', '').strip()
        citizen_cpf = re.sub(r'[^\d]', '', citizen_cpf_raw) if citizen_cpf_raw else ''
        
        # Ouvidor exige CPF quando o cidadão não é anônimo
        if not is_anonymous:
            if not citizen_cpf or len(citizen_cpf) != 11:
                raise serializers.ValidationError(
                    {"citizen_cpf": "CPF é obrigatório. Informe um CPF válido."}
                )
            try:
                validate_cpf_core(citizen_cpf_raw or citizen_cpf)
            except DjangoValidationError:
                raise serializers.ValidationError(
                    {"citizen_cpf": "CPF inválido. Verifique os números."}
                )
            # Normalizar para 11 dígitos no payload
            data['citizen_cpf'] = re.sub(r'[^\d]', '', citizen_cpf_raw)[:11]
        
        return data

    def create(self, validated_data):
        """Cria manifestação com status inicial e protocolo automático"""
        import re
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        # Status inicial sempre é WAITING_TRIAGE
        validated_data['status'] = Manifestation.STATUS_WAITING_TRIAGE
        
        # Remover campos do cidadão do validated_data (não são campos do modelo Manifestation)
        citizen_name = validated_data.pop('citizen_name', '').strip()
        citizen_email = validated_data.pop('citizen_email', '').strip()
        citizen_cpf = re.sub(r'[^\d]', '', validated_data.pop('citizen_cpf', '') or '')[:11]
        citizen_phone = validated_data.pop('citizen_phone', '').strip() or None
        citizen_correction = validated_data.pop('citizen_correction', '').strip() or None
        files = validated_data.pop('files', [])
        file_descriptions = validated_data.pop('file_descriptions', [])
        is_anonymous = validated_data.get('is_anonymous', False)
        
        # CORREÇÃO CRÍTICA: Se há CPF válido, não pode ser anônimo
        if citizen_cpf and len(citizen_cpf) == 11:
            is_anonymous = False
            validated_data['is_anonymous'] = False
        
        # Se houver correção do cidadão, adicionar ao description ou salvar separadamente
        if citizen_correction:
            validated_data['citizen_correction'] = citizen_correction
        
        # Se usuário autenticado, associar ao cidadão
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['citizen'] = request.user
        elif not is_anonymous and (citizen_name or citizen_email or citizen_cpf):
            # Soft Auth: Criar ou vincular usuário automaticamente
            user = None
            
            # CPF já normalizado em validate(); garantir 11 dígitos
            if citizen_cpf:
                citizen_cpf = (re.sub(r'[^\d]', '', citizen_cpf) or '')[:11]
            
            # Tentar encontrar usuário existente por CPF ou Email
            if citizen_cpf:
                user = User.objects.filter(cpf=citizen_cpf).first()
            
            if not user and citizen_email:
                user = User.objects.filter(email=citizen_email).first()
            
            # Se não encontrou, criar novo usuário temporário
            if not user:
                # Gerar username único baseado em email ou CPF
                if citizen_email:
                    username = citizen_email.split('@')[0]
                elif citizen_cpf:
                    username = f'user_{citizen_cpf[-6:]}'
                else:
                    username = f'user_{citizen_name.lower().replace(" ", "_")[:20]}'
                
                # Garantir username único
                base_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f'{base_username}_{counter}'
                    counter += 1
                
                # Criar usuário temporário (sem senha)
                user = User.objects.create(
                    username=username,
                    email=citizen_email if citizen_email else None,
                    cpf=citizen_cpf if citizen_cpf else None,
                    full_name=citizen_name if citizen_name else None,
                    phone=citizen_phone,
                    is_temporary=True,
                    is_active=True,
                )
            else:
                # Atualizar dados do usuário existente se necessário
                updated = False
                if citizen_name and not user.full_name:
                    user.full_name = citizen_name
                    updated = True
                if citizen_email and not user.email:
                    user.email = citizen_email
                    updated = True
                if citizen_cpf and not user.cpf:
                    user.cpf = citizen_cpf
                    updated = True
                if citizen_phone and not user.phone:
                    user.phone = citizen_phone
                    updated = True
                if updated:
                    user.save()
            
            validated_data['citizen'] = user
        
        # Origin padrão se não fornecido
        if 'origin' not in validated_data:
            validated_data['origin'] = Manifestation.ORIGIN_WEB
        
        # Criar a manifestação
        manifestation = super().create(validated_data)
        
        # Criar anexos se houver arquivos
        request = self.context.get('request')
        uploaded_by = request.user if request and request.user.is_authenticated else None
        
        if files:
            for index, file in enumerate(files):
                # Validar arquivo usando o validador
                from .models import validate_file_upload
                from django.core.exceptions import ValidationError as DjangoValidationError
                try:
                    validate_file_upload(file)
                except DjangoValidationError as e:
                    # Se validação falhar, deletar a manifestação criada e relançar erro
                    manifestation.delete()
                    raise serializers.ValidationError({'files': str(e)})
                except Exception as e:
                    # Outros erros
                    manifestation.delete()
                    raise serializers.ValidationError({'files': f'Erro ao validar arquivo: {str(e)}'})
                
                # Obter descrição do arquivo (pode ser string vazia, converter para None)
                description = None
                if index < len(file_descriptions) and file_descriptions[index]:
                    desc = file_descriptions[index]
                    if isinstance(desc, str) and desc.strip():
                        description = desc.strip()
                    elif desc:  # Se não for string vazia
                        description = str(desc).strip() if str(desc).strip() else None
                Attachment.objects.create(
                    manifestation=manifestation,
                    file=file,
                    description=description,
                    uploaded_by=uploaded_by
                )
        
        return manifestation


class ManifestationUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para andamentos/atualizações de manifestações
    """
    updated_by_name = serializers.SerializerMethodField()
    new_status_display = serializers.SerializerMethodField()

    class Meta:
        model = ManifestationUpdate
        fields = [
            'id',
            'internal_note',
            'public_note',
            'new_status',
            'new_status_display',
            'updated_by',
            'updated_by_name',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_updated_by_name(self, obj):
        """Retorna o nome do usuário que fez a atualização"""
        if obj.updated_by:
            return obj.updated_by.get_full_name() or obj.updated_by.username
        return None

    def get_new_status_display(self, obj):
        """Retorna o display name do status"""
        return obj.get_new_status_display()


class AttachmentSerializer(serializers.ModelSerializer):
    """
    Serializer para anexos de manifestações
    """
    uploaded_by_name = serializers.SerializerMethodField()
    file_type_display = serializers.CharField(source='get_file_type_display', read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Attachment
        fields = [
            'id',
            'file',
            'file_url',
            'filename',
            'description',
            'file_size',
            'mime_type',
            'file_type',
            'file_type_display',
            'uploaded_by',
            'uploaded_by_name',
            'created_at',
        ]
        read_only_fields = ['id', 'filename', 'file_size', 'mime_type', 'file_type', 'created_at']
    
    def get_file_url(self, obj):
        """Retorna a URL completa do arquivo (usa API_PUBLIC_BASE_URL se definido, para evitar link quebrado atrás de proxy)."""
        if not obj.file:
            return None
        from django.conf import settings
        base = getattr(settings, 'API_PUBLIC_BASE_URL', '').rstrip('/')
        if base:
            return f"{base}{obj.file.url}"
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.file.url)
        return obj.file.url

    def get_uploaded_by_name(self, obj):
        """Retorna o nome do usuário que fez o upload"""
        if obj.uploaded_by:
            return obj.uploaded_by.get_full_name() or obj.uploaded_by.username
        return None


class SatisfactionSurveySerializer(serializers.ModelSerializer):
    """Serializer para avaliação de satisfação (rating 1-5 + comentário opcional)."""

    class Meta:
        model = SatisfactionSurvey
        fields = ['rating', 'comment']
        extra_kwargs = {
            'rating': {'min_value': 1, 'max_value': 5},
            'comment': {'required': False, 'allow_blank': True},
        }

    def create(self, validated_data):
        manifestation = self.context.get('manifestation')
        if not manifestation:
            raise serializers.ValidationError('Manifestação é obrigatória.')
        return SatisfactionSurvey.objects.create(manifestation=manifestation, **validated_data)


class ManifestationDetailSerializer(serializers.ModelSerializer):
    """
    Serializer completo para detalhes da manifestação (usado por gestores)
    Inclui análise NLP aninhada e informações completas
    """
    citizen_name = serializers.SerializerMethodField()
    resolved_by_name = serializers.SerializerMethodField()
    category_detail = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    origin_display = serializers.CharField(source='get_origin_display', read_only=True)
    
    # Nested serializers
    nlp_analysis = NLPAnalysisSerializer(read_only=True)
    updates = ManifestationUpdateSerializer(many=True, read_only=True)
    attachments = AttachmentSerializer(many=True, read_only=True)
    satisfaction_survey = SatisfactionSurveySerializer(read_only=True)
    engagement_count = serializers.SerializerMethodField()
    potential_duplicate_id = serializers.SerializerMethodField()
    related_manifestations = serializers.SerializerMethodField()
    related_group_id = serializers.IntegerField(read_only=True, allow_null=True)
    is_primary = serializers.BooleanField(read_only=True)

    class Meta:
        model = Manifestation
        fields = [
            'id',
            'protocol',
            'citizen',
            'citizen_name',
            'description',
            'status',
            'status_display',
            'origin',
            'origin_display',
            'location_address',
            'latitude',
            'longitude',
            'is_anonymous',
            'category',
            'category_detail',
            'resolved_at',
            'resolved_by',
            'resolved_by_name',
            'created_at',
            'updated_at',
            'engagement_count',
            'potential_duplicate_id',
            'related_manifestations',
            'related_group_id',
            'is_primary',
            # Nested data
            'nlp_analysis',
            'updates',
            'attachments',
            'satisfaction_survey',
        ]
        read_only_fields = [
            'id',
            'protocol',
            'created_at',
            'updated_at',
            'resolved_at',
        ]

    def get_category_detail(self, obj):
        """
        Retorna a categoria manual se existir, caso contrário retorna a categoria sugerida pela IA
        """
        # Prioridade 1: Categoria manual vinculada
        if obj.category:
            return ManifestationCategorySerializer(obj.category).data
        
        # Prioridade 2: Categoria sugerida pela IA (se análise existir)
        if hasattr(obj, 'nlp_analysis') and obj.nlp_analysis and obj.nlp_analysis.suggested_category:
            return ManifestationCategorySerializer(obj.nlp_analysis.suggested_category).data
        
        return None

    def get_citizen_name(self, obj):
        """Retorna o nome do cidadão (se não for anônimo)"""
        if obj.is_anonymous or not obj.citizen:
            return None
        return obj.citizen.get_full_name() or obj.citizen.username

    def get_resolved_by_name(self, obj):
        """Retorna o nome de quem resolveu"""
        if obj.resolved_by:
            return obj.resolved_by.get_full_name() or obj.resolved_by.username
        return None

    def get_engagement_count(self, obj):
        if obj.is_primary:
            return 1 + obj.related_manifestations.count()
        if obj.related_group_id:
            return obj.related_group.related_manifestations.count() + 1
        return 1

    def get_potential_duplicate_id(self, obj):
        if obj.potential_duplicate_id:
            return str(obj.potential_duplicate_id)
        return None

    def get_related_manifestations(self, obj):
        """
        Retorna lista de manifestações relacionadas (filhas se for pai, ou irmãs se for filha).
        """
        if obj.is_primary:
            # Se for pai, retornar todas as filhas
            return [
                {
                    'id': str(m.id),
                    'protocol': m.protocol,
                    'description': m.description,
                    'created_at': m.created_at.isoformat(),
                }
                for m in obj.related_manifestations.all()
            ]
        elif obj.related_group_id:
            # Se for filha, retornar irmãs (outras filhas do mesmo pai)
            parent = obj.related_group
            if parent:
                return [
                    {
                        'id': str(m.id),
                        'protocol': m.protocol,
                        'description': m.description,
                        'created_at': m.created_at.isoformat(),
                    }
                    for m in parent.related_manifestations.exclude(id=obj.id)
                ]
        return []


class ManifestationUpdatePublicSerializer(serializers.ModelSerializer):
    """
    Serializer público para andamentos (visível ao cidadão)
    Retorna apenas public_note, não inclui internal_note
    """
    new_status_display = serializers.CharField(source='get_new_status_display', read_only=True)
    
    class Meta:
        model = ManifestationUpdate
        fields = [
            'id',
            'public_note',
            'new_status',
            'new_status_display',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class TrackManifestationSerializer(serializers.ModelSerializer):
    """
    Serializer público para rastreio de manifestação por protocolo
    Retorna apenas dados seguros, sem informações sensíveis do cidadão
    """
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    category_detail = serializers.SerializerMethodField()
    nlp_summary = serializers.SerializerMethodField()
    nlp_urgency = serializers.SerializerMethodField()
    updates = ManifestationUpdatePublicSerializer(many=True, read_only=True)
    attachments_preview = serializers.SerializerMethodField()
    sla_info = serializers.SerializerMethodField()
    already_rated = serializers.SerializerMethodField()
    
    class Meta:
        model = Manifestation
        fields = [
            'protocol',
            'status',
            'status_display',
            'description',
            'category_detail',
            'nlp_summary',
            'nlp_urgency',
            'location_address',
            'created_at',
            'resolved_at',
            'updates',
            'attachments_preview',
            'sla_info',
            'already_rated',
        ]
        read_only_fields = ['protocol', 'created_at', 'resolved_at']
    
    def get_category_detail(self, obj):
        """Retorna categoria manual ou sugerida pela IA (com default_sector para pré-preenchimento)"""
        cat = obj.category or (
            obj.nlp_analysis.suggested_category
            if hasattr(obj, 'nlp_analysis') and obj.nlp_analysis else None
        )
        if not cat:
            return None
        return {
            'id': str(cat.id),
            'name': cat.name,
            'sla_hours': cat.sla_hours,
            'default_sector': getattr(cat, 'default_sector', None),
        }
    
    def get_nlp_summary(self, obj):
        """Retorna resumo da IA se disponível"""
        if hasattr(obj, 'nlp_analysis') and obj.nlp_analysis:
            return obj.nlp_analysis.summary
        return None
    
    def get_nlp_urgency(self, obj):
        """Retorna nível de urgência da IA"""
        if hasattr(obj, 'nlp_analysis') and obj.nlp_analysis:
            urgency_labels = {
                1: 'Baixa',
                2: 'Média',
                3: 'Alta',
                4: 'Muito Alta',
                5: 'Crítica',
            }
            return {
                'level': obj.nlp_analysis.urgency_level,
                'label': urgency_labels.get(obj.nlp_analysis.urgency_level, 'Desconhecido'),
            }
        return None
    
    def get_attachments_preview(self, obj):
        """Retorna preview dos anexos (apenas imagens)"""
        attachments = obj.attachments.filter(file_type='IMAGE')[:4]  # Máximo 4 imagens
        request = self.context.get('request')
        result = []
        for att in attachments:
            url = att.file.url
            if request:
                from django.conf import settings
                base = getattr(settings, 'API_PUBLIC_BASE_URL', '').rstrip('/')
                if base:
                    url = f"{base}{att.file.url}"
                else:
                    url = request.build_absolute_uri(att.file.url)
            result.append({
                'id': str(att.id),
                'file_url': url,
                'filename': att.filename,
            })
        return result
    
    def get_sla_info(self, obj):
        """Retorna informações de SLA"""
        category = obj.category or (obj.nlp_analysis.suggested_category if hasattr(obj, 'nlp_analysis') and obj.nlp_analysis else None)
        if category and category.sla_hours:
            from django.utils import timezone
            from datetime import timedelta
            deadline = obj.created_at + timedelta(hours=category.sla_hours)
            is_overdue = timezone.now() > deadline and obj.status not in [Manifestation.STATUS_RESOLVED, Manifestation.STATUS_CLOSED]
            return {
                'sla_hours': category.sla_hours,
                'deadline': deadline,
                'is_overdue': is_overdue,
            }
        return None

    def get_already_rated(self, obj):
        """True se o cidadão já enviou avaliação de satisfação."""
        return hasattr(obj, 'satisfaction_survey') and obj.satisfaction_survey is not None


class ManifestationListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listagem de manifestações (inclui engagement_count e dados para inbox admin).
    """
    category_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    citizen_name = serializers.SerializerMethodField()
    has_nlp_analysis = serializers.SerializerMethodField()
    engagement_count = serializers.SerializerMethodField()
    urgency_level = serializers.SerializerMethodField()
    sentiment_score = serializers.SerializerMethodField()
    potential_duplicate_id = serializers.SerializerMethodField()
    nlp_summary = serializers.SerializerMethodField()

    class Meta:
        model = Manifestation
        fields = [
            'id',
            'protocol',
            'description',
            'nlp_summary',
            'status',
            'status_display',
            'category',
            'category_name',
            'citizen_name',
            'is_anonymous',
            'origin',
            'created_at',
            'has_nlp_analysis',
            'engagement_count',
            'urgency_level',
            'sentiment_score',
            'potential_duplicate_id',
        ]

    def get_category_name(self, obj):
        """Retorna o nome da categoria (manual ou sugerida pela IA)"""
        if obj.category:
            return obj.category.name
        if hasattr(obj, 'nlp_analysis') and obj.nlp_analysis and obj.nlp_analysis.suggested_category:
            return obj.nlp_analysis.suggested_category.name
        return None

    def get_citizen_name(self, obj):
        """Retorna o nome do cidadão (se não for anônimo)"""
        if obj.is_anonymous or not obj.citizen:
            return None
        return obj.citizen.get_full_name() or obj.citizen.username

    def get_has_nlp_analysis(self, obj):
        """Verifica se existe análise NLP"""
        return hasattr(obj, 'nlp_analysis')

    def get_engagement_count(self, obj):
        """
        Volume de reclamações: se for "Pai" (is_primary), retorna 1 + filhos.
        Se for única ou filha, retorna 1 (ou o tamanho do grupo quando for pai).
        """
        if obj.is_primary:
            return 1 + obj.related_manifestations.count()
        if obj.related_group_id:
            # Filha: contar 1 + irmãos + pai
            return obj.related_group.related_manifestations.count() + 1
        return 1

    def get_urgency_level(self, obj):
        """Nível de urgência da IA (1-5) para triagem."""
        if hasattr(obj, 'nlp_analysis') and obj.nlp_analysis:
            return obj.nlp_analysis.urgency_level
        return None

    def get_sentiment_score(self, obj):
        """Score de sentimento da IA (-1 a 1) para triagem."""
        if hasattr(obj, 'nlp_analysis') and obj.nlp_analysis:
            return obj.nlp_analysis.sentiment_score
        return None

    def get_potential_duplicate_id(self, obj):
        """ID da manifestação sugerida como duplicata (cluster)."""
        if obj.potential_duplicate_id:
            return str(obj.potential_duplicate_id)
        return None

    def get_nlp_summary(self, obj):
        """Resumo técnico da IA para card no board setorial."""
        if hasattr(obj, 'nlp_analysis') and obj.nlp_analysis and obj.nlp_analysis.summary:
            return (obj.nlp_analysis.summary or '')[:300]
        return None


# --- WorkOrder (Ordem de Serviço) - Board Setorial ---


class WorkOrderManifestationBriefSerializer(serializers.ModelSerializer):
    """Resumo de uma manifestação dentro de uma OS (para card/modal)."""
    protocol = serializers.CharField(read_only=True)
    engagement_count = serializers.SerializerMethodField()
    nlp_summary = serializers.SerializerMethodField()
    location_address = serializers.CharField(read_only=True)
    urgency_level = serializers.SerializerMethodField()
    latitude = serializers.DecimalField(max_digits=10, decimal_places=8, read_only=True, allow_null=True)
    longitude = serializers.DecimalField(max_digits=11, decimal_places=8, read_only=True, allow_null=True)

    class Meta:
        model = Manifestation
        fields = [
            'id', 'protocol', 'description', 'location_address', 
            'engagement_count', 'nlp_summary', 'urgency_level',
            'latitude', 'longitude'
        ]

    def get_engagement_count(self, obj):
        if obj.is_primary:
            return 1 + obj.related_manifestations.count()
        if obj.related_group_id:
            return obj.related_group.related_manifestations.count() + 1
        return 1

    def get_nlp_summary(self, obj):
        if hasattr(obj, 'nlp_analysis') and obj.nlp_analysis:
            return (obj.nlp_analysis.summary or '')[:200]
        return None

    def get_urgency_level(self, obj):
        """Nível de urgência da IA (1-5) para ordenação no Kanban."""
        if hasattr(obj, 'nlp_analysis') and obj.nlp_analysis:
            return obj.nlp_analysis.urgency_level
        return None


class WorkOrderSerializer(serializers.ModelSerializer):
    """Serializer para listagem e detalhe de OS no Kanban."""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    team_leader_name = serializers.SerializerMethodField()
    manifestation_count = serializers.SerializerMethodField()
    technical_summary = serializers.SerializerMethodField()
    heat_count = serializers.SerializerMethodField()
    manifestations = WorkOrderManifestationBriefSerializer(many=True, read_only=True)

    class Meta:
        model = WorkOrder
        fields = [
            'id', 'sector', 'status', 'status_display', 'team_leader', 'team_leader_name',
            'block_reason', 'scheduled_date', 'created_at',
            'manifestation_count', 'technical_summary', 'heat_count',
            'manifestations',
        ]
        read_only_fields = ['id', 'created_at', 'sector']

    def get_team_leader_name(self, obj):
        if obj.team_leader:
            return obj.team_leader.get_full_name() or obj.team_leader.username
        return None

    def get_manifestation_count(self, obj):
        return obj.manifestations.count()

    def get_technical_summary(self, obj):
        first = obj.manifestations.select_related('nlp_analysis').first()
        if first and hasattr(first, 'nlp_analysis') and first.nlp_analysis and first.nlp_analysis.summary:
            return first.nlp_analysis.summary[:300]
        first_desc = obj.manifestations.values_list('description', flat=True).first()
        return (first_desc or '')[:300]

    def get_heat_count(self, obj):
        total = 0
        for m in obj.manifestations.all():
            if m.is_primary:
                total += 1 + m.related_manifestations.count()
            elif m.related_group_id:
                total += m.related_group.related_manifestations.count() + 1
            else:
                total += 1
        return total


class WorkOrderCreateSerializer(serializers.ModelSerializer):
    """Criação de OS a partir de manifestações (ex.: arrastar da Entrada para Cronograma)."""
    manifestation_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        help_text='IDs das manifestações a agrupar nesta OS',
    )

    class Meta:
        model = WorkOrder
        fields = ['sector', 'team_leader', 'scheduled_date', 'manifestation_ids']

    def create(self, validated_data):
        manifestation_ids = validated_data.pop('manifestation_ids', [])
        sector = validated_data.get('sector')
        if not sector:
            raise serializers.ValidationError({'sector': 'Setor é obrigatório.'})
        work_order = WorkOrder.objects.create(
            sector=sector,
            status=WorkOrder.STATUS_SCHEDULED,
            **{k: v for k, v in validated_data.items() if k in ('team_leader', 'scheduled_date')}
        )
        if manifestation_ids:
            Manifestation.objects.filter(id__in=manifestation_ids).update(work_order=work_order)
        return work_order
