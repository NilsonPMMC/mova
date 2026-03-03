"""
Migração para atualizar as dimensões do campo embedding de 1536 para 768.
Como não podemos alterar dimensões de um VectorField existente, 
vamos deletar e recriar a tabela.
"""
from django.db import migrations, models
import pgvector.django


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_teste_vetorial'),
    ]

    operations = [
        # Deletar a tabela antiga (com 1536 dimensões)
        migrations.DeleteModel(
            name='TesteVetorial',
        ),
        # Recriar com 768 dimensões (Google Gemini)
        migrations.CreateModel(
            name='TesteVetorial',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=200, verbose_name='Nome')),
                ('embedding', pgvector.django.VectorField(dimensions=768, verbose_name='Embedding Vetorial')),
            ],
            options={
                'verbose_name': 'Teste Vetorial',
                'verbose_name_plural': 'Testes Vetoriais',
                'db_table': 'teste_vetorial',
                'ordering': ['nome'],
            },
        ),
    ]
