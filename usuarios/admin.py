from django.contrib import admin
from django.utils.html import format_html
from .models import Usuario, Rol, ContenidoIndex, BarberoDestacado  # Sololos modelos de usuarios

admin.site.register(Usuario)
admin.site.register(Rol)

@admin.register(ContenidoIndex)
class ContenidoIndexAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Hero (portada principal)", {
            'fields': (
                'hero_etiqueta', 'hero_titulo', 'hero_descripcion',
                'hero_tarjeta_titulo', 'hero_tarjeta_texto',
                'hero_imagen_1', 'hero_imagen_2', 'hero_imagen_3',
            )
        }),
        ("Sección Marca / Sobre nosotros", {
            'fields': ('marca_titulo', 'marca_descripcion', 'marca_imagen')
        }),
        ("Contacto", {
            'fields': (
                'horario_semana', 'horario_sabado',
                'telefono_fijo', 'whatsapp', 'direccion', 'mapa_embed_url',
            )
        }),
        ("Banner CTA final", {
            'fields': ('cta_titulo', 'cta_texto')
        }),
    )

    def has_add_permission(self, request):
        # Bloquea "Agregar" si ya existe la fila única (patrón singleton)
        return not ContenidoIndex.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        # Redirige directo a la única fila para editar, en vez de mostrar una lista
        obj = ContenidoIndex.cargar()
        from django.shortcuts import redirect
        return redirect(f'/admin/usuarios/contenidoindex/{obj.pk}/change/')


@admin.register(BarberoDestacado)
class BarberoDestacadoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'especialidad', 'orden', 'activo', 'miniatura')
    list_editable = ('orden', 'activo')
    ordering = ('orden',)

    def miniatura(self, obj):
        if obj.foto:
            return format_html('<img src="{}" style="height:40px;border-radius:6px;" />', obj.foto.url)
        return "—"
    miniatura.short_description = "Foto"