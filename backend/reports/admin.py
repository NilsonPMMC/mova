from django.contrib import admin
from .models import (
    ManifestationCategory,
    ServicePartner,
    ServiceSchedule,
    Manifestation,
    ManifestationUpdate,
    Attachment,
    SatisfactionSurvey,
    WorkOrder,
)


@admin.register(ManifestationCategory)
class ManifestationCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'is_active', 'is_smart_service', 'sla_hours', 'default_sector', 'created_at')
    list_filter = ('is_active', 'is_smart_service', 'parent', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ServicePartner)
class ServicePartnerAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'address')


@admin.register(ServiceSchedule)
class ServiceScheduleAdmin(admin.ModelAdmin):
    list_display = ('partner', 'date', 'time_slot', 'total_slots', 'booked_slots', 'available_slots', 'is_active')
    list_filter = ('partner', 'date', 'is_active')
    search_fields = ('partner__name',)
    raw_id_fields = ('partner',)


@admin.register(Manifestation)
class ManifestationAdmin(admin.ModelAdmin):
    list_display = (
        'protocol',
        'description_short',
        'status',
        'origin',
        'is_anonymous',
        'has_embedding',
        'has_service_data',
        'created_at',
        'citizen',
    )
    list_filter = ('status', 'origin', 'is_anonymous', 'category', 'created_at')
    search_fields = ('protocol', 'description', 'location_address')
    readonly_fields = ('protocol', 'embedding_status', 'created_at', 'updated_at', 'resolved_at')
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('protocol', 'citizen', 'description', 'is_anonymous')
        }),
        ('Classificação', {
            'fields': ('category', 'status', 'origin')
        }),
        ('Localização', {
            'fields': ('location_address', 'latitude', 'longitude')
        }),
        ('Campos consumidos pela IA', {
            'description': 'Dados preenchidos ou gerados pela análise de IA (embedding, service_data).',
            'fields': ('embedding_status', 'service_data', 'service_schedule'),
        }),
        ('Resolução', {
            'fields': ('resolved_at', 'resolved_by')
        }),
        ('Duplicidade / Agrupamento', {
            'fields': ('related_group', 'is_primary', 'potential_duplicate', 'work_order')
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def description_short(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Descrição'

    def has_embedding(self, obj):
        if obj.embedding is None:
            return False
        try:
            return len(obj.embedding) > 0
        except (TypeError, ValueError):
            return False
    has_embedding.boolean = True
    has_embedding.short_description = 'Embedding'

    def has_service_data(self, obj):
        return bool(obj.service_data and isinstance(obj.service_data, dict) and len(obj.service_data) > 0)
    has_service_data.boolean = True
    has_service_data.short_description = 'Service Data'

    def embedding_status(self, obj):
        if obj.embedding is None:
            return 'Não'
        try:
            dim = len(obj.embedding)
            return f'Sim ({dim} dim)' if dim > 0 else 'Não'
        except (TypeError, ValueError):
            return 'Não'
    embedding_status.short_description = 'Embedding'


@admin.register(ManifestationUpdate)
class ManifestationUpdateAdmin(admin.ModelAdmin):
    list_display = ('manifestation', 'new_status', 'has_public_note', 'has_internal_note', 'updated_by', 'created_at')
    list_filter = ('new_status', 'created_at')
    search_fields = ('manifestation__protocol', 'internal_note', 'public_note')
    readonly_fields = ('created_at', 'updated_at')
    
    def has_public_note(self, obj):
        return bool(obj.public_note)
    has_public_note.boolean = True
    has_public_note.short_description = 'Tem Nota Pública'
    
    def has_internal_note(self, obj):
        return bool(obj.internal_note)
    has_internal_note.boolean = True
    has_internal_note.short_description = 'Tem Nota Interna'


@admin.register(SatisfactionSurvey)
class SatisfactionSurveyAdmin(admin.ModelAdmin):
    list_display = ('manifestation', 'rating', 'has_comment', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('manifestation__protocol', 'comment')
    readonly_fields = ('created_at', 'updated_at')

    def has_comment(self, obj):
        return bool(obj.comment)
    has_comment.boolean = True
    has_comment.short_description = 'Tem Comentário'


@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'sector', 'status', 'team_leader', 'scheduled_date', 'manifestation_count_display', 'created_at')
    list_filter = ('sector', 'status', 'created_at')
    search_fields = ('sector', 'block_reason')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('team_leader',)

    def manifestation_count_display(self, obj):
        return obj.manifestations.count()
    manifestation_count_display.short_description = 'Manifestações'


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('filename', 'manifestation', 'file_type', 'file_size', 'mime_type', 'uploaded_by', 'created_at')
    list_filter = ('file_type', 'mime_type', 'created_at')
    search_fields = ('filename', 'description', 'manifestation__protocol')
    readonly_fields = ('created_at', 'updated_at', 'filename', 'file_size', 'mime_type', 'file_type')
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('manifestation', 'file', 'description')
        }),
        ('Metadados', {
            'fields': ('filename', 'file_type', 'file_size', 'mime_type', 'uploaded_by')
        }),
        ('Datas', {
            'fields': ('created_at', 'updated_at')
        }),
    )
