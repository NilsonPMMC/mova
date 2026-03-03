# Generated manually: Modelo TesteVetorial para busca vetorial com OpenAI API
# Dimensões: 1536 (text-embedding-3-small)

from django.db import migrations, models
import pgvector.django


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_enable_pgvector'),
    ]

    operations = [
        migrations.CreateModel(
            name='TesteVetorial',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=200, verbose_name='Nome')),
                ('embedding', pgvector.django.VectorField(dimensions=1536, verbose_name='Embedding Vetorial')),
            ],
            options={
                'verbose_name': 'Teste Vetorial',
                'verbose_name_plural': 'Testes Vetoriais',
                'db_table': 'teste_vetorial',
                'ordering': ['nome'],
            },
        ),
    ]
