"""
Management command para popular o banco com dados realistas de teste.
Valida Dashboards: Inbox (triagem), Kanban (setorial), Clusters.

Como rodar (no diretório do backend, com o ambiente ativado):
  python manage.py populate_system              # adiciona dados sem apagar o que já existe
  python manage.py populate_system --clean     # apaga manifestações, OS e categorias e recria tudo

Após rodar:
  - Login: admin@localhost / admin
  - Inbox (/admin/inbox): cluster Av. Japão (alta urgência), reclamação confusa (Outros)
  - Kanban ILUMINACAO (/sector?setor=ILUMINACAO ou select ILUMINACAO): 5 lâmpadas encaminhadas
  - Kanban OBRAS: 2 OS em Bloqueado com motivo "Aguardando Chuva Parar"

Nota: Este script usa vetores mock (numpy.random.rand) para não gastar cota da API do Google.
O signal de geração automática de embeddings é desativado durante a execução.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from django.db.models.signals import post_save
from datetime import timedelta
from decimal import Decimal
import numpy as np

# Mogi das Cruzes - coordenadas reais (centro e arredores)
MOGI_CENTER_LAT = Decimal('-23.52')
MOGI_CENTER_LON = Decimal('-46.18')
AV_JAPAO_LAT = Decimal('-23.521500')
AV_JAPAO_LON = Decimal('-46.192000')

# Bairros / pontos para lâmpadas (pequenas variações aleatórias em torno do centro)
LAMP_COORDS = [
    (Decimal('-23.518000'), Decimal('-46.185000')),  # Centro
    (Decimal('-23.528000'), Decimal('-46.195000')),  # Sul
    (Decimal('-23.515000'), Decimal('-46.178000')),  # Leste
    (Decimal('-23.530000'), Decimal('-46.182000')),  # Oeste
    (Decimal('-23.525000'), Decimal('-46.200000')),  # Sudoeste
]

# Dimensões do embedding (Google Gemini)
EMBEDDING_DIMENSIONS = 3072

NOMES_ESTATICOS = [
    'Maria Silva', 'João Santos', 'Ana Oliveira', 'Pedro Souza', 'Carla Lima',
    'Roberto Costa', 'Fernanda Alves', 'Lucas Pereira', 'Juliana Rocha', 'Marcos Ferreira',
    'Patricia Dias', 'Ricardo Nunes', 'Camila Martins', 'Bruno Carvalho', 'Amanda Ribeiro',
]


class Command(BaseCommand):
    help = 'Popula o sistema com dados de teste (Inbox, Kanban, Clusters). Use --clean para apagar antes.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Apaga manifestações, OS e categorias antes de criar os dados.',
        )

    def _generate_mock_embedding(self, text=None, seed=None):
        """
        Gera um vetor mock de 3072 dimensões usando numpy.random.
        Se seed for fornecido, usa para gerar vetores similares para textos relacionados.
        """
        if seed is not None:
            np.random.seed(seed)
        # Gerar vetor aleatório normalizado (valores entre -1 e 1)
        vector = np.random.rand(EMBEDDING_DIMENSIONS).astype(np.float32) * 2 - 1
        return vector.tolist()

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()
        from reports.models import Manifestation, ManifestationCategory, WorkOrder
        from reports.signals import generate_embedding_for_manifestation
        from intelligence.models import NLPAnalysis

        # Desconectar signal de geração de embedding para usar vetores mock
        post_save.disconnect(generate_embedding_for_manifestation, sender=Manifestation)
        self.stdout.write('  Signal de geração de embedding desativado (usando vetores mock).')

        try:
            if options['clean']:
                self._clean(User, Manifestation, ManifestationCategory, WorkOrder, NLPAnalysis)

            self._ensure_superuser(User)
            categories = self._create_categories(ManifestationCategory)

            self._scenario_1_cluster(Manifestation, NLPAnalysis, categories)
            self._scenario_2_despacho_automatico(Manifestation, NLPAnalysis, categories)
            self._scenario_3_incerteza(Manifestation, NLPAnalysis, categories)
            self._scenario_4_bloqueio(Manifestation, NLPAnalysis, WorkOrder, categories)

            self.stdout.write(self.style.SUCCESS('População concluída. Valide Inbox, Kanban e Clusters.'))
        finally:
            # Reconectar signal ao final
            post_save.connect(generate_embedding_for_manifestation, sender=Manifestation)
            self.stdout.write('  Signal de geração de embedding reativado.')

    def _clean(self, User, Manifestation, ManifestationCategory, WorkOrder, NLPAnalysis):
        self.stdout.write('Limpando dados...')
        WorkOrder.objects.all().delete()
        Manifestation.objects.all().delete()  # cascade: NLPAnalysis, updates, attachments, etc.
        ManifestationCategory.objects.all().delete()
        self.stdout.write('  WorkOrder, Manifestation e ManifestationCategory removidos.')

    def _ensure_superuser(self, User):
        if User.objects.filter(username='admin').exists() or User.objects.filter(email='admin@localhost').exists():
            self.stdout.write('  Superuser admin já existe.')
            return
        user = User.objects.create_user(
            username='admin',
            email='admin@localhost',
            password='admin',
            is_superuser=True,
            is_staff=True,
            full_name='Administrador',
        )
        self.stdout.write(self.style.SUCCESS('  Superuser criado: admin@localhost / admin'))

    def _create_categories(self, ManifestationCategory):
        data = [
            {'name': 'Infraestrutura', 'slug': 'infraestrutura', 'default_sector': 'OBRAS', 'sla_hours': 120},
            {'name': 'Iluminação Pública', 'slug': 'iluminacao-publica', 'default_sector': 'ILUMINACAO', 'sla_hours': 48},
            {'name': 'Saúde / Dengue', 'slug': 'saude-dengue', 'default_sector': 'SAUDE', 'sla_hours': 24},
            {'name': 'Trânsito', 'slug': 'transito', 'default_sector': 'MOBILIDADE', 'sla_hours': 24},
            {'name': 'Outros', 'slug': 'outros', 'default_sector': None, 'sla_hours': 72},
        ]
        categories = {}
        for d in data:
            cat, _ = ManifestationCategory.objects.get_or_create(
                slug=d['slug'],
                defaults={
                    'name': d['name'],
                    'default_sector': d.get('default_sector'),
                    'sla_hours': d['sla_hours'],
                    'is_active': True,
                },
            )
            categories[d['slug']] = cat
        self.stdout.write('  Categorias Mogi (Infraestrutura, Iluminação, Saúde, Trânsito, Outros) criadas/verificadas.')
        return categories

    def _scenario_1_cluster(self, Manifestation, NLPAnalysis, categories):
        """Cluster crítico: 1 pai + 15 filhas, Av. Japão, urgência 5, WAITING_TRIAGE."""
        cat = categories['infraestrutura']
        desc_pai = 'Buraco na Avenida Japão altura do 1500'
        
        # Gerar embedding mock para o pai (seed fixo para consistência)
        embedding_pai = self._generate_mock_embedding(seed=100)
        
        # Criar pai (is_primary=True)
        pai = Manifestation.objects.create(
            description=desc_pai,
            status=Manifestation.STATUS_WAITING_TRIAGE,
            origin=Manifestation.ORIGIN_WEB,
            location_address='Av. Japão, 1500 - Mogi das Cruzes',
            latitude=AV_JAPAO_LAT,
            longitude=AV_JAPAO_LON,
            is_anonymous=False,
            category=None,
            is_primary=True,
            embedding=embedding_pai,  # Vetor mock
        )
        NLPAnalysis.objects.create(
            manifestation=pai,
            sentiment_score=-0.9,
            urgency_level=5,
            suggested_category=cat,
            summary='Buraco em via principal; alto risco.',
            intent=NLPAnalysis.INTENT_COMPLAINT,
            keywords=['buraco', 'avenida japão', 'acidente'],
        )
        
        # Filhas (15 textos variados, coordenadas próximas, potential_duplicate apontando para pai)
        variacoes = [
            'Cratera na Japão',
            'Buraco enorme aqui',
            'Buraco perigoso na Av. Japão 1500',
            'Mesmo buraco na Av. Japão 1500, já denunciei.',
            'Buraco na altura do 1500 na Av. Japão.',
            'Outro registro do buraco perigoso na Av. Japão.',
            'Av. Japão nº 1500 - buraco grande.',
            'Quero reforçar a reclamação do buraco na Av. Japão.',
            'Buraco na Avenida Japão, perto do 1500.',
            'Mesmo local, buraco ainda sem conserto.',
            'Av. Japão 1500 - perigo para motos.',
            'Buraco na altura do 1500, Av. Japão.',
            'Mais uma reclamação do buraco na Av. Japão.',
            'Avenida Japão, buraco perigoso 1500.',
            'Buraco na Av. Japão, número 1500.',
        ]
        
        for i, desc in enumerate(variacoes):
            # Gerar embedding similar ao pai (seed próximo para similaridade semântica)
            np.random.seed(100 + i)
            embedding_filha = self._generate_mock_embedding(seed=100 + i)
            
            # Pequenas variações geográficas determinísticas (dentro do box de ~100m)
            lat_offset = Decimal(str(np.random.uniform(-0.0005, 0.0005)))
            lon_offset = Decimal(str(np.random.uniform(-0.0005, 0.0005)))
            
            filha = Manifestation.objects.create(
                description=desc,
                status=Manifestation.STATUS_WAITING_TRIAGE,
                origin=Manifestation.ORIGIN_WEB,
                location_address='Av. Japão, 1500 - Mogi das Cruzes',
                latitude=AV_JAPAO_LAT + lat_offset,
                longitude=AV_JAPAO_LON + lon_offset,
                is_anonymous=False,
                category=None,
                related_group=pai,
                is_primary=False,
                potential_duplicate=pai,  # Vínculo de duplicidade
                embedding=embedding_filha,  # Vetor mock similar
            )
            NLPAnalysis.objects.create(
                manifestation=filha,
                sentiment_score=-0.9,
                urgency_level=5,
                suggested_category=cat,
                summary='Buraco Av. Japão; mesma localização.',
                intent=NLPAnalysis.INTENT_COMPLAINT,
                keywords=['buraco', 'avenida japão'],
            )
        
        # Datas retroativas (SLA estourado)
        dias_atras = timezone.now() - timedelta(days=6)
        ids_cluster = [pai.pk] + list(Manifestation.objects.filter(related_group=pai).values_list('pk', flat=True))
        Manifestation.objects.filter(pk__in=ids_cluster).update(created_at=dias_atras)
        self.stdout.write('  Cenário 1: Cluster crítico Av. Japão (1 pai + 15 filhas, WAITING_TRIAGE).')

    def _scenario_2_despacho_automatico(self, Manifestation, NLPAnalysis, categories):
        """5 reclamações lâmpada apagada, FORWARDED, setor ILUMINACAO."""
        cat = categories['iluminacao-publica']
        enderecos = [
            'Rua Coronel Souza Franco, 200 - Centro',
            'Rua Dr. Corrêa, 450 - Vila Natal',
            'Av. Cândido Xavier, 1200 - Jardim Armênia',
            'Rua dos Expedicionários, 80 - Vila Lavínia',
            'Praça da República, 15 - Centro',
        ]
        for i, end in enumerate(enderecos):
            lat, lon = LAMP_COORDS[i]
            # Gerar embedding mock para lâmpadas (seed similar para textos similares)
            embedding = self._generate_mock_embedding(seed=200 + i)
            
            m = Manifestation.objects.create(
                description=f'Lâmpada Apagada em {end}. Escuro à noite.',
                status=Manifestation.STATUS_FORWARDED,
                origin=Manifestation.ORIGIN_WEB,
                location_address=end,
                latitude=lat,
                longitude=lon,
                is_anonymous=False,
                category=cat,
                embedding=embedding,  # Vetor mock
            )
            NLPAnalysis.objects.create(
                manifestation=m,
                sentiment_score=-0.3,
                urgency_level=2,
                suggested_category=cat,
                summary=f'Lâmpada queimada - {end}.',
                intent=NLPAnalysis.INTENT_COMPLAINT,
                raw_ai_response={'parsed_json': {'confidence': 0.92}},
            )
        self.stdout.write('  Cenário 2: 5 reclamações Iluminação (FORWARDED, Kanban ILUMINACAO).')

    def _scenario_3_incerteza(self, Manifestation, NLPAnalysis, categories):
        """3 reclamações confusas, categoria Outros, urgência 3, WAITING_TRIAGE."""
        cat_outros = categories['outros']
        textos_confusos = [
            'Barulho e lixo',
            'Barulho do bar misturado com lixo na calçada e o ônibus não passa. '
            'Não sei se é secretaria de obras, meio ambiente ou transporte. '
            'O bar joga garrafa na rua, a calçada fica suja e o 101 nunca vem no horário.',
            'Problema na rua mas não sei qual setor resolve. Tem barulho, lixo e buraco.',
        ]
        
        for i, texto in enumerate(textos_confusos):
            # Gerar embedding mock único para cada texto confuso
            np.random.seed(300 + i)
            embedding = self._generate_mock_embedding(seed=300 + i)
            
            # Pequenas variações geográficas determinísticas no centro
            lat_offset = Decimal(str(np.random.uniform(-0.001, 0.001)))
            lon_offset = Decimal(str(np.random.uniform(-0.001, 0.001)))
            
            m = Manifestation.objects.create(
                description=texto,
                status=Manifestation.STATUS_WAITING_TRIAGE,
                origin=Manifestation.ORIGIN_WEB,
                location_address=f'Rua das Flores, {300 + i} - Centro, Mogi das Cruzes',
                latitude=MOGI_CENTER_LAT + lat_offset,
                longitude=MOGI_CENTER_LON + lon_offset,
                is_anonymous=False,
                category=None,
                embedding=embedding,  # Vetor mock
            )
            NLPAnalysis.objects.create(
                manifestation=m,
                sentiment_score=-0.5,
                urgency_level=3,
                suggested_category=cat_outros,
                summary='Múltiplos problemas: barulho, lixo, ônibus. Categoria indefinida.',
                intent=NLPAnalysis.INTENT_COMPLAINT,
                keywords=['bar', 'lixo', 'ônibus', 'calçada'],
            )
        self.stdout.write('  Cenário 3: Incerteza (3 manifestações Outros, WAITING_TRIAGE).')

    def _scenario_4_bloqueio(self, Manifestation, NLPAnalysis, WorkOrder, categories):
        """2 manifestações encaminhadas para OBRAS, WorkOrders BLOCKED."""
        cat = categories['infraestrutura']
        
        manifestacoes_obras = [
            {
                'description': 'Asfalto esburacado na Rua das Palmeiras, 500. Já faz 2 meses.',
                'address': 'Rua das Palmeiras, 500 - Mogi das Cruzes',
                'lat': Decimal('-23.519000'),
                'lon': Decimal('-46.190000'),
            },
            {
                'description': 'Buraco grande na Rua dos Ipês, 200. Precisa de reparo urgente.',
                'address': 'Rua dos Ipês, 200 - Mogi das Cruzes',
                'lat': Decimal('-23.520000'),
                'lon': Decimal('-46.191000'),
            },
        ]
        
        for i, dados in enumerate(manifestacoes_obras):
            # Gerar embedding mock
            embedding = self._generate_mock_embedding(seed=400 + i)
            
            m = Manifestation.objects.create(
                description=dados['description'],
                status=Manifestation.STATUS_FORWARDED,
                origin=Manifestation.ORIGIN_WEB,
                location_address=dados['address'],
                latitude=dados['lat'],
                longitude=dados['lon'],
                is_anonymous=False,
                category=cat,
                embedding=embedding,  # Vetor mock
            )
            NLPAnalysis.objects.create(
                manifestation=m,
                sentiment_score=-0.7,
                urgency_level=4,
                suggested_category=cat,
                summary='Asfalto esburacado; aguardando intervenção.',
                intent=NLPAnalysis.INTENT_COMPLAINT,
            )
            
            # Criar WorkOrder bloqueada
            wo = WorkOrder.objects.create(
                sector='OBRAS',
                status=WorkOrder.STATUS_BLOCKED,
                block_reason='Aguardando Chuva Parar',
                scheduled_date=(timezone.now() + timedelta(days=30)).date(),
            )
            m.work_order = wo
            m.save(update_fields=['work_order'])
        
        self.stdout.write('  Cenário 4: Bloqueio (2 OS OBRAS em BLOCKED).')
