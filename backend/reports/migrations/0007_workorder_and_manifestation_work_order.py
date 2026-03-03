# Generated manually: WorkOrder model + Manifestation.work_order FK

import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0006_populate_default_sector'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='WorkOrder',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Data de Atualização')),
                ('sector', models.CharField(db_index=True, help_text='Ex: Obras, Iluminação, Saúde, Trânsito', max_length=100, verbose_name='Setor')),
                ('status', models.CharField(choices=[('scheduled', 'Cronograma'), ('in_progress', 'Em Rua'), ('blocked', 'Bloqueado'), ('done', 'Concluído')], db_index=True, default='scheduled', max_length=20, verbose_name='Status')),
                ('block_reason', models.TextField(blank=True, help_text='Preenchido quando status = Bloqueado (ex: Setor incorreto, Falta orçamento)', null=True, verbose_name='Motivo do bloqueio')),
                ('scheduled_date', models.DateField(blank=True, null=True, verbose_name='Data prevista')),
                ('team_leader', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='work_orders_led', to=settings.AUTH_USER_MODEL, verbose_name='Responsável / Líder de equipe')),
            ],
            options={
                'verbose_name': 'Ordem de Serviço',
                'verbose_name_plural': 'Ordens de Serviço',
                'db_table': 'work_orders',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddField(
            model_name='manifestation',
            name='work_order',
            field=models.ForeignKey(blank=True, help_text='OS à qual esta manifestação foi agrupada para execução', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='manifestations', to='reports.workorder', verbose_name='Ordem de Serviço'),
        ),
        migrations.AddIndex(
            model_name='workorder',
            index=models.Index(fields=['sector'], name='work_orders_sector_idx'),
        ),
        migrations.AddIndex(
            model_name='workorder',
            index=models.Index(fields=['status'], name='work_orders_status_idx'),
        ),
        migrations.AddIndex(
            model_name='workorder',
            index=models.Index(fields=['scheduled_date'], name='work_orders_scheduled_idx'),
        ),
    ]
