"""
Migração para atualizar as dimensões do campo embedding de 768 para 3072.
O modelo text-embedding-004 não está disponível na API Google AI Studio;
usamos gemini-embedding-001 que retorna 3072 dimensões.
Como não podemos alterar dimensões de um VectorField existente, deletamos e recriamos a tabela.
"""
from django.db import migrations, models
import pgvector.django


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_update_teste_vetorial_dimensions'),
    ]

    operations = [
        migrations.DeleteModel(
            name='TesteVetorial',
        ),
        migrations.CreateModel(
            name='TesteVetorial',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=200, verbose_name='Nome')),
                ('embedding', pgvector.django.VectorField(dimensions=3072, blank=True, help_text='Gerado automaticamente via signal', null=True, verbose_name='Embedding Vetorial')),
            ],
            options={
                'verbose_name': 'Teste Vetorial',
                'verbose_name_plural': 'Testes Vetoriais',
                'db_table': 'teste_vetorial',
                'ordering': ['nome'],
            },
        ),
    ]
