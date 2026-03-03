"""
Migração para tornar o campo embedding nullable.
Permite salvar registros sem embedding inicialmente, que será gerado automaticamente via signal.
Usa SQL direto para garantir que a constraint NOT NULL seja removida do banco.
"""
from django.db import migrations
import pgvector.django


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_teste_vetorial_3072_dimensions'),
    ]

    operations = [
        # Primeiro, alterar a constraint no banco usando SQL direto
        migrations.RunSQL(
            sql="ALTER TABLE teste_vetorial ALTER COLUMN embedding DROP NOT NULL;",
            reverse_sql="ALTER TABLE teste_vetorial ALTER COLUMN embedding SET NOT NULL;",
        ),
        # Depois, atualizar o modelo Django para refletir a mudança
        migrations.AlterField(
            model_name='testevetorial',
            name='embedding',
            field=pgvector.django.VectorField(
                dimensions=3072,
                blank=True,
                help_text='Gerado automaticamente via signal',
                null=True,
                verbose_name='Embedding Vetorial'
            ),
        ),
    ]
