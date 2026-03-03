from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, TesteVetorial


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'username', 'full_name', 'cpf', 'sector', 'is_temporary', 'is_staff', 'is_superuser', 'is_active', 'created_at')
    list_filter = ('is_staff', 'is_active', 'is_temporary', 'sector', 'created_at')
    search_fields = ('email', 'username', 'full_name', 'cpf', 'first_name', 'last_name')
    ordering = ('-created_at',)
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informações Pessoais', {'fields': ('full_name', 'first_name', 'last_name', 'email', 'cpf', 'phone')}),
        ('Setor de Trabalho', {'fields': ('sector',), 'description': 'Setor para controle de acesso no Board de Execução'}),
        ('Permissões', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Status', {'fields': ('is_temporary',)}),
        ('Datas Importantes', {'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')}),
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(TesteVetorial)
class TesteVetorialAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome')
    search_fields = ('nome',)
    readonly_fields = ('id',)
