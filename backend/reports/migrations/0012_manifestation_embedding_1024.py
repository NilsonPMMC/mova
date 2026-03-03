# Migração: altera dimensão do embedding de 3072 para 1024 (Gabinete AI Kernel / mxbai-embed-large).
# No pgvector não é possível ALTER COLUMN para mudar dimensão; é necessário DROP + ADD.

from django.db import migrations
from pgvector.django import VectorField


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0011_add_duplicate_forwarded_status'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name='manifestation',
                    name='embedding',
                    field=VectorField(
                        dimensions=1024,
                        null=True,
                        blank=True,
                        verbose_name='Embedding Vetorial',
                        help_text='Vetor de embedding gerado automaticamente via signal para busca semântica (1024 dimensões)',
                    ),
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        "ALTER TABLE manifestations DROP COLUMN IF EXISTS embedding; "
                        "ALTER TABLE manifestations ADD COLUMN embedding vector(1024) NULL;"
                    ),
                    reverse_sql=(
                        "ALTER TABLE manifestations DROP COLUMN IF EXISTS embedding; "
                        "ALTER TABLE manifestations ADD COLUMN embedding vector(3072) NULL;"
                    ),
                ),
            ],
        ),
    ]
