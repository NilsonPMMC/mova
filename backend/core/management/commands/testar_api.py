"""
Comando de teste para busca vetorial usando OpenAI API.
Testa a geração de embeddings e busca por similaridade.
"""
from django.core.management.base import BaseCommand
from core.models import TesteVetorial
from core.services.vector_service_api import VectorService
from pgvector.django import L2Distance, CosineDistance
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Testa busca vetorial com embeddings da OpenAI API'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Iniciando teste de busca vetorial com OpenAI API'))
        
        # Inicializar serviço
        try:
            vector_service = VectorService()
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ VectorService inicializado com modelo: {vector_service.get_model_name()} '
                    f'({vector_service.get_dimensions()} dimensões)'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erro ao inicializar VectorService: {str(e)}')
            )
            return
        
        # Limpar dados anteriores
        self.stdout.write('🧹 Limpando dados anteriores...')
        TesteVetorial.objects.all().delete()
        
        # Frase de teste
        frase_teste = "Buraco na rua"
        self.stdout.write(f'\n📝 Gerando embedding para: "{frase_teste}"')
        
        try:
            # Gerar embedding
            embedding_teste = vector_service.get_embedding(frase_teste)
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Embedding gerado: {len(embedding_teste)} dimensões'
                )
            )
            
            # Salvar no banco
            obj_teste = TesteVetorial.objects.create(
                nome=frase_teste,
                embedding=embedding_teste
            )
            self.stdout.write(
                self.style.SUCCESS(f'✅ Salvo no banco com ID: {obj_teste.id}')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erro ao gerar/salvar embedding: {str(e)}')
            )
            return
        
        # Buscar por similaridade
        frase_busca = "Problema asfáltico"
        self.stdout.write(f'\n🔍 Gerando embedding para busca: "{frase_busca}"')
        
        try:
            embedding_busca = vector_service.get_embedding(frase_busca)
            
            # Buscar usando distância L2 (Euclidiana)
            self.stdout.write('\n📊 Buscando por similaridade (L2 Distance)...')
            resultado_l2 = (
                TesteVetorial.objects
                .annotate(distance=L2Distance('embedding', embedding_busca))
                .order_by('distance')
                .first()
            )
            
            if resultado_l2:
                distancia_l2 = resultado_l2.distance
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Resultado encontrado: "{resultado_l2.nome}"\n'
                        f'   Distância L2: {distancia_l2:.4f}'
                    )
                )
            else:
                self.stdout.write(self.style.WARNING('⚠️ Nenhum resultado encontrado'))
            
            # Buscar usando distância Cosseno
            self.stdout.write('\n📊 Buscando por similaridade (Cosine Distance)...')
            resultado_cosine = (
                TesteVetorial.objects
                .annotate(distance=CosineDistance('embedding', embedding_busca))
                .order_by('distance')
                .first()
            )
            
            if resultado_cosine:
                distancia_cosine = resultado_cosine.distance
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Resultado encontrado: "{resultado_cosine.nome}"\n'
                        f'   Distância Cosseno: {distancia_cosine:.4f}'
                    )
                )
            else:
                self.stdout.write(self.style.WARNING('⚠️ Nenhum resultado encontrado'))
            
            # Análise de similaridade
            self.stdout.write('\n📈 Análise de Similaridade:')
            if resultado_l2 and resultado_cosine:
                # Distância cosseno: quanto menor, mais similar (0 = idêntico, 1 = oposto)
                # Para embeddings normalizados, cosseno é geralmente melhor
                similaridade_percent = (1 - distancia_cosine) * 100
                self.stdout.write(
                    f'   Similaridade: {similaridade_percent:.2f}%'
                )
                
                if similaridade_percent > 80:
                    self.stdout.write(
                        self.style.SUCCESS('   ✅ Alta similaridade semântica detectada!')
                    )
                elif similaridade_percent > 60:
                    self.stdout.write(
                        self.style.WARNING('   ⚠️ Similaridade moderada')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR('   ❌ Baixa similaridade')
                    )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erro ao buscar: {str(e)}')
            )
            import traceback
            self.stdout.write(traceback.format_exc())
            return
        
        self.stdout.write('\n' + self.style.SUCCESS('✨ Teste concluído com sucesso!'))
