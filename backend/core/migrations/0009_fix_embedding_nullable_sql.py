"""
Migração SQL direta para tornar o campo embedding nullable.
A migração 0008 não removeu a constraint NOT NULL do banco, então fazemos via SQL.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_teste_vetorial_embedding_nullable'),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE teste_vetorial ALTER COLUMN embedding DROP NOT NULL;",
            reverse_sql="ALTER TABLE teste_vetorial ALTER COLUMN embedding SET NOT NULL;",
        ),
    ]
