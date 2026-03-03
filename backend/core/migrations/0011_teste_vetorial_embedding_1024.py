# Migração: altera dimensão do embedding de 3072 para 1024 (Gabinete AI Kernel / mxbai-embed-large).
# No pgvector não é possível ALTER COLUMN para mudar dimensão; é necessário DROP + ADD.

from django.db import migrations
from pgvector.django import VectorField


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_user_sector'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name='testevetorial',
                    name='embedding',
                    field=VectorField(
                        dimensions=1024,
                        null=True,
                        blank=True,
                        verbose_name='Embedding Vetorial',
                        help_text='Gerado automaticamente via signal',
                    ),
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        "ALTER TABLE teste_vetorial DROP COLUMN IF EXISTS embedding; "
                        "ALTER TABLE teste_vetorial ADD COLUMN embedding vector(1024) NULL;"
                    ),
                    reverse_sql=(
                        "ALTER TABLE teste_vetorial DROP COLUMN IF EXISTS embedding; "
                        "ALTER TABLE teste_vetorial ADD COLUMN embedding vector(3072) NULL;"
                    ),
                ),
            ],
        ),
    ]
