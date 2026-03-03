"""
Migração para adicionar campo embedding ao modelo Manifestation.
Usa Google Gemini API (models/gemini-embedding-001) com 3072 dimensões.

Nota: Índice HNSW não foi criado porque o pgvector limita HNSW a 2000 dimensões.
Com 3072 dimensões a busca usa sequential scan; para grandes volumes considere
reduzir dimensões (ex.: PCA) ou aguardar suporte a mais dimensões no pgvector.
"""
from django.db import migrations
import pgvector.django


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0008_rename_work_orders_sector_idx_work_orders_sector_92fbce_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='manifestation',
            name='embedding',
            field=pgvector.django.VectorField(
                dimensions=3072,
                blank=True,
                help_text='Vetor de embedding gerado automaticamente via signal para busca semântica (3072 dimensões)',
                null=True,
                verbose_name='Embedding Vetorial'
            ),
        ),
    ]
