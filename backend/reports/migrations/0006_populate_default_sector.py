# Data migration: popular default_sector nas categorias existentes

from django.db import migrations


def set_default_sectors(apps, schema_editor):
    ManifestationCategory = apps.get_model('reports', 'ManifestationCategory')
    # Mapeamento sugerido por nome/slug; ajuste conforme suas categorias reais
    sector_map = {
        'obras': 'OBRAS',
        'infraestrutura': 'OBRAS',
        'buraco': 'OBRAS',
        'asfalto': 'OBRAS',
        'iluminacao': 'OBRAS',
        'saude': 'SAUDE',
        'saúde': 'SAUDE',
        'hospital': 'SAUDE',
        'zeladoria': 'ZELADORIA',
        'limpeza': 'ZELADORIA',
        'lixo': 'ZELADORIA',
        'transporte': 'TRANSPORTE',
        'onibus': 'TRANSPORTE',
        'educacao': 'EDUCACAO',
        'educação': 'EDUCACAO',
        'escola': 'EDUCACAO',
        'seguranca': 'SEGURANCA',
        'segurança': 'SEGURANCA',
        'policia': 'SEGURANCA',
        'meio-ambiente': 'MEIO_AMBIENTE',
        'outros': None,  # Triagem manual
    }
    for cat in ManifestationCategory.objects.all():
        slug_lower = (cat.slug or '').strip().lower()
        name_lower = (cat.name or '').strip().lower()
        sector = None
        for key, val in sector_map.items():
            if key in slug_lower or key in name_lower:
                sector = val
                break
        if sector:
            cat.default_sector = sector
            cat.save(update_fields=['default_sector'])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0005_manifestationcategory_default_sector'),
    ]

    operations = [
        migrations.RunPython(set_default_sectors, noop),
    ]
