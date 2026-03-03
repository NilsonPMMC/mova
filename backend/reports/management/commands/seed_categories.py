from django.core.management.base import BaseCommand
from reports.models import ManifestationCategory


class Command(BaseCommand):
    help = 'Popula categorias iniciais com SLAs reais'

    def handle(self, *args, **options):
        categories_data = [
            {
                'name': 'Iluminação Pública',
                'slug': 'iluminacao-publica',
                'sla_hours': 48,
                'description': 'Problemas relacionados à iluminação pública, lâmpadas queimadas, postes sem luz, etc.'
            },
            {
                'name': 'Buraco em Via/Pavimentação',
                'slug': 'buraco-pavimentacao',
                'sla_hours': 120,
                'description': 'Buracos em ruas, calçadas danificadas, problemas de pavimentação'
            },
            {
                'name': 'Saúde/Falta de Médico',
                'slug': 'saude-medico',
                'sla_hours': 24,
                'description': 'Problemas relacionados à saúde pública, falta de médicos, atendimento em unidades de saúde'
            },
            {
                'name': 'Coleta de Lixo',
                'slug': 'coleta-lixo',
                'sla_hours': 24,
                'description': 'Problemas com coleta de lixo, lixeiras cheias, falta de coleta'
            },
            {
                'name': 'Zeladoria',
                'slug': 'zeladoria',
                'sla_hours': 72,
                'description': 'Limpeza de vias públicas, capina, poda de árvores'
            },
            {
                'name': 'Trânsito',
                'slug': 'transito',
                'sla_hours': 48,
                'description': 'Sinalização de trânsito, semáforos, faixas de pedestre'
            },
            {
                'name': 'Segurança',
                'slug': 'seguranca',
                'sla_hours': 12,
                'description': 'Problemas de segurança pública, iluminação em áreas perigosas'
            },
            {
                'name': 'Meio Ambiente',
                'slug': 'meio-ambiente',
                'sla_hours': 96,
                'description': 'Questões ambientais, poluição, áreas verdes'
            },
        ]

        created_count = 0
        updated_count = 0

        for cat_data in categories_data:
            category, created = ManifestationCategory.objects.update_or_create(
                slug=cat_data['slug'],
                defaults={
                    'name': cat_data['name'],
                    'sla_hours': cat_data['sla_hours'],
                    'description': cat_data.get('description', ''),
                    'is_active': True,
                }
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Criada categoria: {category.name} (SLA: {category.sla_hours}h)')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'↻ Atualizada categoria: {category.name} (SLA: {category.sla_hours}h)')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Processo concluído! Criadas: {created_count}, Atualizadas: {updated_count}'
            )
        )
