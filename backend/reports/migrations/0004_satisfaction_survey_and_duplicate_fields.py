# Generated manually for SatisfactionSurvey and duplicate/group fields

import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0003_attachment_description_attachment_file_type_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='manifestation',
            name='related_group',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='related_manifestations',
                to='reports.manifestation',
                verbose_name='Grupo Relacionado (Pai)',
            ),
        ),
        migrations.AddField(
            model_name='manifestation',
            name='is_primary',
            field=models.BooleanField(default=False, verbose_name='É Primária'),
        ),
        migrations.AddField(
            model_name='manifestation',
            name='potential_duplicate',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='potential_duplicates_of',
                to='reports.manifestation',
                verbose_name='Possível Duplicata De',
            ),
        ),
        migrations.CreateModel(
            name='SatisfactionSurvey',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Data de Atualização')),
                ('rating', models.PositiveSmallIntegerField(help_text='Nota de 1 a 5', verbose_name='Nota')),
                ('comment', models.TextField(blank=True, help_text='Deseja adicionar algo? (opcional)', null=True, verbose_name='Comentário')),
                ('manifestation', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='satisfaction_survey', to='reports.manifestation', verbose_name='Manifestação')),
            ],
            options={
                'verbose_name': 'Avaliação de Satisfação',
                'verbose_name_plural': 'Avaliações de Satisfação',
                'db_table': 'satisfaction_surveys',
            },
        ),
        migrations.AddConstraint(
            model_name='satisfactionsurvey',
            constraint=models.CheckConstraint(check=models.Q(('rating__gte', 1), ('rating__lte', 5)), name='satisfaction_rating_range'),
        ),
    ]
