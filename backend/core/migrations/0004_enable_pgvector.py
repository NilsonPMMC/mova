"""
Migração para habilitar a extensão pgvector no PostgreSQL.
Deve ser executada antes de criar tabelas com campos VectorField.
"""
from django.db import migrations
from pgvector.django import VectorExtension


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_user_cpf_user_full_name_user_is_temporary_and_more'),
    ]

    operations = [
        VectorExtension(),
    ]
