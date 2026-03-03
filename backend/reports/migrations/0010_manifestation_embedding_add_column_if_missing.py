"""
Migração de correção: adiciona a coluna embedding à tabela manifestations
se ela não existir (caso a 0009 tenha sido marcada como aplicada sem criar a coluna).
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0009_add_embedding_to_manifestation'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'manifestations'
                      AND column_name = 'embedding'
                ) THEN
                    ALTER TABLE manifestations
                    ADD COLUMN embedding vector(3072) NULL;
                END IF;
            END $$;
            """,
            reverse_sql="ALTER TABLE manifestations DROP COLUMN IF EXISTS embedding;",
        ),
    ]
