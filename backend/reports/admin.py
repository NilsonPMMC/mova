from django.contrib import admin
from .models import ManifestationCategory, Manifestation, ManifestationUpdate, Attachment, SatisfactionSurvey, WorkOrder


@admin.register(ManifestationCategory)
class ManifestationCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'is_active', 'sla_hours', 'created_at')
    list_filter = ('is_active', 'parent', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Manifestation)
class ManifestationAdmin(admin.ModelAdmin):
    list_display = ('protocol', 'description_short', 'status', 'origin', 'is_anonymous', 'created_at', 'citizen')
    list_filter = ('status', 'origin', 'is_anonymous', 'category', 'created_at')
    search_fields = ('protocol', 'description', 'location_address')
    readonly_fields = ('protocol', 'created_at', 'updated_at', 'resolved_at')
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
