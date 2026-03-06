from django.db import models
from django.db.models import F
from django.conf import settings
from django.utils.text import slugify
from pgvector.django import VectorField
from utils.models import TimeStampedModel


class ManifestationCategory(TimeStampedModel):
    """
    Categorias de manifestações com suporte a hierarquia (subcategorias)
    """
    name = models.CharField(max_length=200, verbose_name='Nome')
    slug = models.SlugField(max_length=200, unique=True, verbose_name='Slug')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    sla_hours = models.PositiveIntegerField(
        default=72,
        verbose_name='SLA (horas)',
        help_text='Tempo máximo em horas para resolução'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='Categoria Pai'
    )
    default_sector = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Setor padrão',
        help_text='Setor para despacho automático (ex: OBRAS, SAÚDE, ZELADORIA). Vazio = triagem manual.'
    )
    description = models.TextField(blank=True, null=True, verbose_name='Descrição')
    is_smart_service = models.BooleanField(
        default=False,
        verbose_name='É Serviço Inteligente?',
        help_text='Se True, aciona fluxos específicos no frontend (ex: formulário de castração)'
    )

    class Meta:
        db_table = 'manifestation_categories'
        verbose_name = 'Categoria de Manifestação'
        verbose_name_plural = 'Categorias de Manifestação'
        ordering = ['name']

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_full_path(self):
        """Retorna o caminho completo da categoria incluindo pais"""
        path = [self.name]
        parent = self.parent
        while parent:
            path.insert(0, parent.name)
            parent = parent.parent
        return ' > '.join(path)


class ServicePartner(models.Model):
    """Clínicas ou parceiros que executam serviços terceirizados (ex: Zoonoses)"""
    name = models.CharField(max_length=255, verbose_name="Nome da Clínica/Parceiro")
    address = models.CharField(max_length=255, verbose_name="Endereço Completo")
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    accepted_types = models.JSONField(
        default=list,
        blank=True,
        help_text='Ex: ["Cão Macho", "Cão Fêmea", "Gato Macho", "Gato Fêmea"]'
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'service_partners'
        verbose_name = 'Parceiro de Serviço'
        verbose_name_plural = 'Parceiros de Serviço'
        ordering = ['name']

    def __str__(self):
        return self.name


class ServiceSchedule(models.Model):
    """Agenda de vagas disponíveis por parceiro"""
    partner = models.ForeignKey(
        ServicePartner,
        on_delete=models.CASCADE,
        related_name='schedules'
    )
    date = models.DateField(verbose_name="Data do Atendimento")
    time_slot = models.CharField(max_length=50, verbose_name="Horário/Período (Ex: 08:00 - 12:00)")
    total_slots = models.IntegerField(default=10, verbose_name="Vagas Totais")
    booked_slots = models.IntegerField(default=0, verbose_name="Vagas Ocupadas")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'service_schedules'
        verbose_name = 'Agenda de Serviço'
        verbose_name_plural = 'Agendas de Serviço'
        ordering = ['date', 'time_slot']

    @property
    def available_slots(self):
        return max(0, self.total_slots - self.booked_slots)

    def __str__(self):
        return f"{self.partner.name} - {self.date} ({self.time_slot})"


class Manifestation(TimeStampedModel):
    """
    Modelo principal para manifestações/denúncias da ouvidoria
    """
    STATUS_WAITING_TRIAGE = 'waiting_triage'
    STATUS_IN_ANALYSIS = 'in_analysis'
    STATUS_FORWARDED = 'forwarded'
    STATUS_DUPLICATE_FORWARDED = 'duplicate_forwarded'
    STATUS_RESOLVED = 'resolved'
    STATUS_CLOSED = 'closed'

    STATUS_CHOICES = [
        (STATUS_WAITING_TRIAGE, 'Aguardando Triagem'),
        (STATUS_IN_ANALYSIS, 'Em Análise'),
        (STATUS_FORWARDED, 'Encaminhada'),
        (STATUS_DUPLICATE_FORWARDED, 'Duplicata Encaminhada'),
        (STATUS_RESOLVED, 'Resolvida'),
        (STATUS_CLOSED, 'Encerrada'),
    ]

    ORIGIN_APP = 'app'
    ORIGIN_WEB = 'web'
    ORIGIN_WHATSAPP = 'whatsapp'
    ORIGIN_PHONE = 'phone'

    ORIGIN_CHOICES = [
        (ORIGIN_APP, 'Aplicativo Mobile'),
        (ORIGIN_WEB, 'Portal Web'),
        (ORIGIN_WHATSAPP, 'WhatsApp'),
        (ORIGIN_PHONE, 'Telefone'),
    ]

    protocol = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name='Protocolo',
        help_text='Número de protocolo único gerado automaticamente'
    )
    citizen = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='manifestations',
        verbose_name='Cidadão'
    )
    description = models.TextField(verbose_name='Descrição')
    citizen_correction = models.TextField(
        blank=True,
        null=True,
        verbose_name='Correção do Cidadão',
        help_text='Observação adicional do cidadão caso discorde da análise da IA'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_WAITING_TRIAGE,
        verbose_name='Status'
    )
    origin = models.CharField(
        max_length=20,
        choices=ORIGIN_CHOICES,
        default=ORIGIN_WEB,
        verbose_name='Origem'
    )
    location_address = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='Endereço'
    )
    service_data = models.JSONField(
        verbose_name='Dados Específicos do Serviço',
        null=True,
        blank=True,
        help_text='Armazena dados flexíveis de formulários específicos (ex: dados do animal para castração, agenda, etc.)'
    )
    service_schedule = models.ForeignKey(
        ServiceSchedule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='manifestations',
        verbose_name='Agendamento Vinculado'
    )
    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=8,
        null=True,
        blank=True,
        verbose_name='Latitude'
    )
    longitude = models.DecimalField(
        max_digits=11,
        decimal_places=8,
        null=True,
        blank=True,
        verbose_name='Longitude'
    )
    is_anonymous = models.BooleanField(
        default=False,
        verbose_name='Anônimo'
    )
    category = models.ForeignKey(
        ManifestationCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='manifestations',
        verbose_name='Categoria'
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Data de Resolução'
    )
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='manifestations_resolved',
        verbose_name='Resolvido por'
    )
    # Agrupamento (funil de duplicidade): Pai/Filho
    related_group = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='related_manifestations',
        verbose_name='Grupo Relacionado (Pai)',
        help_text='Manifestação "pai" quando esta é agrupada a outra'
    )
    is_primary = models.BooleanField(
        default=False,
        verbose_name='É Primária',
        help_text='True se esta manifestação é a representante do grupo (pai)'
    )
    # Sugestão de duplicidade espacial (não agrupa automaticamente)
    potential_duplicate = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='potential_duplicates_of',
        verbose_name='Possível Duplicata De',
        help_text='ID da manifestação próxima sugerida pelo algoritmo de deduplicação'
    )
    # Ordem de Serviço (dossiê para a equipe de rua)
    work_order = models.ForeignKey(
        'WorkOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='manifestations',
        verbose_name='Ordem de Serviço',
        help_text='OS à qual esta manifestação foi agrupada para execução'
    )
    # Embedding vetorial para busca semântica (Gabinete AI Kernel: mxbai-embed-large, 1024 dimensões)
    embedding = VectorField(
        dimensions=1024,
        null=True,
        blank=True,
        verbose_name='Embedding Vetorial',
        help_text='Vetor de embedding gerado automaticamente via signal para busca semântica (1024 dimensões)'
    )

    class Meta:
        db_table = 'manifestations'
        verbose_name = 'Manifestação'
        verbose_name_plural = 'Manifestações'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['protocol']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['latitude', 'longitude']),
        ]
        # Índice HNSW para busca vetorial (opcional mas recomendado para performance)
        # Nota: Criado via migração SQL direta devido a limitações do Django ORM

    def __str__(self):
        return f"{self.protocol} - {self.description[:50]}..."

    def generate_protocol(self):
        """
        Gera um protocolo único no formato: OUV-YYYYMMDD-XXXXX
        """
        from datetime import datetime
        import random
        import string

        date_str = datetime.now().strftime('%Y%m%d')
        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        return f"OUV-{date_str}-{random_suffix}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        if not self.protocol:
            # Garantir unicidade do protocolo
            while True:
                protocol = self.generate_protocol()
                if not Manifestation.objects.filter(protocol=protocol).exists():
                    self.protocol = protocol
                    break
        super().save(*args, **kwargs)

        if is_new and self.service_schedule_id:
            ServiceSchedule.objects.filter(pk=self.service_schedule_id).update(
                booked_slots=F('booked_slots') + 1
            )


class ManifestationUpdate(TimeStampedModel):
    """
    Modelo para registrar andamentos/atualizações de uma manifestação
    """
    manifestation = models.ForeignKey(
        Manifestation,
        on_delete=models.CASCADE,
        related_name='updates',
        verbose_name='Manifestação'
    )
    internal_note = models.TextField(
        blank=True,
        null=True,
        verbose_name='Nota Interna',
        help_text='Nota visível apenas para a equipe interna'
    )
    public_note = models.TextField(
        blank=True,
        null=True,
        verbose_name='Nota Pública',
        help_text='Nota visível ao cidadão'
    )
    new_status = models.CharField(
        max_length=20,
        choices=Manifestation.STATUS_CHOICES,
        verbose_name='Novo Status'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='manifestation_updates',
        verbose_name='Atualizado por'
    )

    class Meta:
        db_table = 'manifestation_updates'
        verbose_name = 'Andamento'
        verbose_name_plural = 'Andamentos'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.manifestation.protocol} - {self.get_new_status_display()} - {self.created_at.strftime('%d/%m/%Y %H:%M')}"


class WorkOrder(TimeStampedModel):
    """
    Ordem de Serviço (dossiê) para execução pela secretaria.
    Pode agrupar várias manifestações (cluster) para uma mesma equipe de rua.
    """
    STATUS_SCHEDULED = 'scheduled'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_BLOCKED = 'blocked'
    STATUS_DONE = 'done'

    STATUS_CHOICES = [
        (STATUS_SCHEDULED, 'Cronograma'),
        (STATUS_IN_PROGRESS, 'Em Rua'),
        (STATUS_BLOCKED, 'Bloqueado'),
        (STATUS_DONE, 'Concluído'),
    ]

    sector = models.CharField(
        max_length=100,
        verbose_name='Setor',
        help_text='Ex: Obras, Iluminação, Saúde, Trânsito',
        db_index=True,
    )
    team_leader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='work_orders_led',
        verbose_name='Responsável / Líder de equipe',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_SCHEDULED,
        verbose_name='Status',
        db_index=True,
    )
    block_reason = models.TextField(
        blank=True,
        null=True,
        verbose_name='Motivo do bloqueio',
        help_text='Preenchido quando status = Bloqueado (ex: Setor incorreto, Falta orçamento)',
    )
    scheduled_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Data prevista',
    )

    class Meta:
        db_table = 'work_orders'
        verbose_name = 'Ordem de Serviço'
        verbose_name_plural = 'Ordens de Serviço'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sector']),
            models.Index(fields=['status']),
            models.Index(fields=['scheduled_date']),
        ]

    def __str__(self):
        count = self.manifestations.count()
        return f"OS {self.sector} — {count} manifestação(ões) — {self.get_status_display()}"


class SatisfactionSurvey(TimeStampedModel):
    """
    Avaliação de satisfação do cidadão (simples: nota 1-5 + comentário opcional).
    OneToOne com Manifestation; só pode avaliar quando status == RESOLVED.
    """
    manifestation = models.OneToOneField(
        Manifestation,
        on_delete=models.CASCADE,
        related_name='satisfaction_survey',
        verbose_name='Manifestação'
    )
    rating = models.PositiveSmallIntegerField(
        verbose_name='Nota',
        help_text='Nota de 1 a 5'
    )
    comment = models.TextField(
        blank=True,
        null=True,
        verbose_name='Comentário',
        help_text='Deseja adicionar algo? (opcional)'
    )

    class Meta:
        db_table = 'satisfaction_surveys'
        verbose_name = 'Avaliação de Satisfação'
        verbose_name_plural = 'Avaliações de Satisfação'
        constraints = [
            models.CheckConstraint(
                check=models.Q(rating__gte=1) & models.Q(rating__lte=5),
                name='satisfaction_rating_range'
            ),
        ]

    def __str__(self):
        return f"{self.manifestation.protocol} - {self.rating}/5"


def validate_file_upload(file):
    """
    Validador customizado para upload de arquivos.
    Aceita apenas imagens (jpg, jpeg, png, webp) e PDF.
    Rejeita executáveis e limita tamanho a 5MB.
    """
    import os
    from django.core.exceptions import ValidationError as DjangoValidationError
    
    # Tamanho máximo: 5MB
    max_size = 5 * 1024 * 1024  # 5MB em bytes
    
    # Extensões permitidas
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.pdf']
    allowed_mime_types = [
        'image/jpeg',
        'image/jpg',
        'image/png',
        'image/webp',
        'application/pdf'
    ]
    
    # Verificar tamanho
    if file.size > max_size:
        raise DjangoValidationError(f'O arquivo é muito grande. Tamanho máximo permitido: 5MB.')
    
    # Verificar extensão
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in allowed_extensions:
        raise DjangoValidationError(
            f'Formato de arquivo não permitido. '
            f'Formatos aceitos: {", ".join(allowed_extensions)}'
        )
    
    # Verificar MIME type (se disponível)
    if hasattr(file, 'content_type') and file.content_type:
        if file.content_type not in allowed_mime_types:
            raise DjangoValidationError(
                f'Tipo de arquivo não permitido. '
                f'Tipos aceitos: imagens (JPG, PNG, WEBP) e PDF.'
            )
    
    # Verificar se não é executável (por extensão)
    dangerous_extensions = ['.exe', '.bat', '.cmd', '.com', '.scr', '.vbs', '.js', '.jar', '.sh']
    if ext in dangerous_extensions:
        raise DjangoValidationError('Arquivos executáveis não são permitidos por segurança.')


class Attachment(TimeStampedModel):
    """
    Modelo para anexos das manifestações
    """
    FILE_TYPE_IMAGE = 'IMAGE'
    FILE_TYPE_DOCUMENT = 'DOCUMENT'
    FILE_TYPE_AUDIO = 'AUDIO'
    FILE_TYPE_VIDEO = 'VIDEO'
    FILE_TYPE_OTHER = 'OTHER'
    
    FILE_TYPE_CHOICES = [
        (FILE_TYPE_IMAGE, 'Imagem'),
        (FILE_TYPE_DOCUMENT, 'Documento'),
        (FILE_TYPE_AUDIO, 'Áudio'),
        (FILE_TYPE_VIDEO, 'Vídeo'),
        (FILE_TYPE_OTHER, 'Outro'),
    ]
    
    manifestation = models.ForeignKey(
        Manifestation,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name='Manifestação'
    )
    file = models.FileField(
        upload_to='manifestations/%Y/%m/%d/',
        verbose_name='Arquivo',
        validators=[validate_file_upload]
    )
    filename = models.CharField(
        max_length=255,
        verbose_name='Nome do Arquivo'
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Descrição',
        help_text='Descrição opcional do anexo (ex: "Foto do buraco")'
    )
    file_size = models.BigIntegerField(
        verbose_name='Tamanho (bytes)'
    )
    mime_type = models.CharField(
        max_length=100,
        verbose_name='Tipo MIME'
    )
    file_type = models.CharField(
        max_length=20,
        choices=FILE_TYPE_CHOICES,
        default=FILE_TYPE_OTHER,
        verbose_name='Tipo de Arquivo'
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='attachments_uploaded',
        verbose_name='Enviado por'
    )

    class Meta:
        db_table = 'attachments'
        verbose_name = 'Anexo'
        verbose_name_plural = 'Anexos'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.filename} - {self.manifestation.protocol}"
    
    def get_file_type_display(self):
        """Retorna o label do tipo de arquivo"""
        return dict(self.FILE_TYPE_CHOICES).get(self.file_type, 'Outro')
    
    def save(self, *args, **kwargs):
        """
        Detecta automaticamente o tipo de arquivo e preenche campos relacionados
        """
        import os
        import mimetypes
        
        # Se é um novo arquivo sendo salvo
        if self.file and not self.filename:
            self.filename = os.path.basename(self.file.name)
        
        if self.file:
            # Obter tamanho do arquivo
            if hasattr(self.file, 'size'):
                self.file_size = self.file.size
            elif self.file.file:
                self.file.file.seek(0, 2)  # Ir para o final
                self.file_size = self.file.file.tell()
                self.file.file.seek(0)  # Voltar ao início
            
            # Detectar MIME type
            if hasattr(self.file, 'content_type') and self.file.content_type:
                self.mime_type = self.file.content_type
            else:
                guessed_type, _ = mimetypes.guess_type(self.filename)
                self.mime_type = guessed_type or 'application/octet-stream'
            
            # Detectar tipo de arquivo baseado no MIME type
            if self.mime_type:
                if self.mime_type.startswith('image/'):
                    self.file_type = self.FILE_TYPE_IMAGE
                elif self.mime_type == 'application/pdf':
                    self.file_type = self.FILE_TYPE_DOCUMENT
                elif self.mime_type.startswith('audio/'):
                    self.file_type = self.FILE_TYPE_AUDIO
                elif self.mime_type.startswith('video/'):
                    self.file_type = self.FILE_TYPE_VIDEO
                else:
                    # Tentar detectar por extensão
                    ext = os.path.splitext(self.filename)[1].lower()
                    if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']:
                        self.file_type = self.FILE_TYPE_IMAGE
                    elif ext == '.pdf':
                        self.file_type = self.FILE_TYPE_DOCUMENT
                    else:
                        self.file_type = self.FILE_TYPE_OTHER
        
        super().save(*args, **kwargs)
