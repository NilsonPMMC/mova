# Generated manually: add default_sector to ManifestationCategory

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0004_satisfaction_survey_and_duplicate_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='manifestationcategory',
            name='default_sector',
            field=models.CharField(
                blank=True,
                help_text='Setor para despacho automático (ex: OBRAS, SAÚDE, ZELADORIA). Vazio = triagem manual.',
                max_length=100,
                null=True,
                verbose_name='Setor padrão',
            ),
        ),
    ]
