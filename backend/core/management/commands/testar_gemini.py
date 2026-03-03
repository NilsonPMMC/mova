"""
Comando de teste para busca vetorial usando Google Gemini API.
Testa a geração de embeddings e busca por similaridade.
"""
from django.core.management.base import BaseCommand
from core.models import TesteVetorial
from core.services.vector_service import VectorService
from pgvector.django import L2Distance, CosineDistance
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Testa busca vetorial com embeddings do Google Gemini API'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Iniciando teste de busca vetorial com Google Gemini API'))
        
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
        
        # Frases de teste
        frases_teste = [
            "Buraco na rua",
            "Consulta médica"
        ]
        
        self.stdout.write('\n📝 Gerando embeddings para as frases de teste...')
        
        objetos_criados = []
        
        for frase in frases_teste:
            try:
                # Gerar embedding
                embedding = vector_service.get_embedding(frase)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Embedding gerado para "{frase}": {len(embedding)} dimensões'
                    )
                )
                
                # Salvar no banco
                obj = TesteVetorial.objects.create(
                    nome=frase,
                    embedding=embedding
                )
                objetos_criados.append(obj)
                self.stdout.write(
                    self.style.SUCCESS(f'   Salvo no banco com ID: {obj.id}')
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Erro ao gerar/salvar embedding para "{frase}": {str(e)}')
                )
                return
        
        # Buscar por similaridade
        frase_busca = "Problema de asfalto"
        self.stdout.write(f'\n🔍 Gerando embedding para busca: "{frase_busca}"')
        
        try:
            embedding_busca = vector_service.get_embedding(frase_busca)
            self.stdout.write(
                self.style.SUCCESS(f'✅ Embedding de busca gerado: {len(embedding_busca)} dimensões')
            )
            
            # Buscar usando distância L2 (Euclidiana)
            self.stdout.write('\n📊 Buscando por similaridade (L2 Distance)...')
            resultados_l2 = (
                TesteVetorial.objects
                .annotate(distance=L2Distance('embedding', embedding_busca))
                .order_by('distance')
            )
            
            self.stdout.write('\n📋 Resultados ordenados por distância L2 (menor = mais similar):')
            for i, resultado in enumerate(resultados_l2, 1):
                distancia = resultado.distance
                self.stdout.write(
                    f'   {i}. "{resultado.nome}" - Distância: {distancia:.4f}'
                )
            
            # Buscar usando distância Cosseno
            self.stdout.write('\n📊 Buscando por similaridade (Cosine Distance)...')
            resultados_cosine = (
                TesteVetorial.objects
                .annotate(distance=CosineDistance('embedding', embedding_busca))
                .order_by('distance')
            )
            
            self.stdout.write('\n📋 Resultados ordenados por distância Cosseno (menor = mais similar):')
            for i, resultado in enumerate(resultados_cosine, 1):
                distancia = resultado.distance
                similaridade_percent = (1 - distancia) * 100
                self.stdout.write(
                    f'   {i}. "{resultado.nome}" - Distância: {distancia:.4f} '
                    f'(Similaridade: {similaridade_percent:.2f}%)'
                )
            
            # Análise do resultado mais próximo
            resultado_mais_proximo = resultados_cosine.first()
            if resultado_mais_proximo:
                distancia_minima = resultado_mais_proximo.distance
                similaridade = (1 - distancia_minima) * 100
                
                self.stdout.write('\n🎯 Análise do Resultado Mais Próximo:')
                self.stdout.write(
                    self.style.SUCCESS(
                        f'   Frase mais similar: "{resultado_mais_proximo.nome}"\n'
                        f'   Similaridade: {similaridade:.2f}%'
                    )
                )
                
                # Validação esperada: "Buraco na rua" deve ser mais similar que "Consulta médica"
                if resultado_mais_proximo.nome == "Buraco na rua":
                    self.stdout.write(
                        self.style.SUCCESS(
                            '\n✅ Teste PASSOU! "Buraco na rua" é mais similar a '
                            '"Problema de asfalto" do que "Consulta médica".'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            '\n⚠️ Resultado inesperado. Esperava-se que "Buraco na rua" '
                            'fosse mais similar a "Problema de asfalto".'
                        )
                    )
            else:
                self.stdout.write(self.style.WARNING('⚠️ Nenhum resultado encontrado'))
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erro ao buscar: {str(e)}')
            )
            import traceback
            self.stdout.write(traceback.format_exc())
            return
        
        self.stdout.write('\n' + self.style.SUCCESS('✨ Teste concluído com sucesso!'))
