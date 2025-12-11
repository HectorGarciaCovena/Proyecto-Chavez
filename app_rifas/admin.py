from django.contrib import admin, messages
from django.db.models import Sum
from django.urls import path, reverse
from django.shortcuts import redirect, render
from django.utils.html import format_html
from django.contrib.auth import authenticate
from django.utils import timezone

from .models import (
    Rifa, Numero, Participante, Orden,
    NumeroSeleccionado, MensajeSorteo,
    SliderImagen, NumeroBendecido
)

import random


# =====================================================================
# 🔐 SECURITY LAYER – PASSWORD-PROTECTED DELETE
# =====================================================================

def secure_delete_view(self, request, object_id, extra_context=None):
    """Protege la eliminación individual pidiendo contraseña."""

    obj = self.get_object(request, object_id)

    # Si ya se envió el formulario con contraseña
    if request.method == "POST" and "password" in request.POST:

        user = authenticate(
            username=request.user.username,
            password=request.POST.get("password")
        )

        if not user:
            messages.error(request, "❌ Contraseña incorrecta.")
            return redirect(request.path)

        # ✔ Ejecutar eliminación REAL
        self.delete_model(request, obj)

        messages.success(request, "🗑 Eliminado correctamente.")

        # Redirigir al listado del modelo
        return redirect(
            reverse(f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_changelist")
        )

    # Primera vez: mostrar pantalla de confirmación
    return render(request, "admin/security_confirm_delete.html", {
        "object": obj,
        "cancel_url": reverse(
            f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_change",
            args=[object_id]
        )
    })


def secure_bulk_delete(self, request, queryset):
    """Protege la eliminación múltiple (delete_selected)."""

    if request.POST.get("action") == "delete_selected":

        # Si ya enviaron contraseña
        if request.method == "POST" and "password" in request.POST:

            user = authenticate(
                username=request.user.username,
                password=request.POST.get("password")
            )

            if not user:
                messages.error(request, "❌ Contraseña incorrecta.")
                return redirect(request.get_full_path())

            # ✔ Ejecutar eliminación una por una
            for obj in queryset:
                self.delete_model(request, obj)

            messages.success(request, "🗑 Eliminación múltiple completada.")
            return redirect(request.get_full_path())

        # Primera vez: mostrar pantalla de confirmación
        return render(request, "admin/security_confirm_delete.html", {
            "object": f"{queryset.count()} objetos seleccionados",
            "cancel_url": request.get_full_path()
        })

    return super(self.__class__, self).response_action(request, queryset)


# =====================================================================
#   ADMIN — ÓRDENES
# =====================================================================
@admin.register(Orden)
class OrdenAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'participante', 'metodo_pago', 'total',
        'estado', 'pagado_icono', 'fecha', 'descargar_boleto'
    )
    list_filter = ('metodo_pago', 'estado', 'fecha')
    search_fields = (
        'participante__nombre',
        'participante__apellido',
        'participante__cedula'
    )
    readonly_fields = ('fecha', 'total')

    # Seguridad también para órdenes (si no quieres contraseña aquí,
    # comenta las dos líneas siguientes)
    delete_view = secure_delete_view
    response_action = secure_bulk_delete

    # ---------- ICONO DE ESTADO ----------
    def pagado_icono(self, obj):
        return "✔️" if obj.estado == "pagado" else "⏳"
    pagado_icono.short_description = "Pagado"

    # ---------- ENLACE PARA DESCARGAR BOLETO ----------
    def descargar_boleto(self, obj):
        if obj.estado != "pagado":
            return "—"
        url = reverse("generar_boleta", args=[obj.id])
        return format_html(
            '<a class="button" href="{}" target="_blank">📄 Descargar</a>',
            url
        )
    descargar_boleto.short_description = "Boleto"

    # ---------- GUARDAR ORDEN ----------
    def save_model(self, request, obj, form, change):
        """
        Si la orden pasa de PENDIENTE a PAGADO:
        - Marca los números seleccionados como comprados.
        - Asigna participante, orden y fecha_compra en Numero.
        """

        was_pending_to_paid = False

        if change:
            previous = Orden.objects.get(id=obj.id)
            if previous.estado == "pendiente" and obj.estado == "pagado":
                was_pending_to_paid = True

        super().save_model(request, obj, form, change)

        # Solo procesar números cuando realmente cambió a pagado
        if was_pending_to_paid:
            seleccionados = NumeroSeleccionado.objects.filter(orden=obj)

            for seleccionado in seleccionados:
                try:
                    # NumeroSeleccionado.numero ya guarda el mismo string que Numero.numero
                    numero_obj = Numero.objects.get(
                        numero=seleccionado.numero,
                        rifa=obj.rifa
                    )
                except Numero.DoesNotExist:
                    continue

                numero_obj.comprado = True
                numero_obj.participante = obj.participante
                numero_obj.orden = obj
                numero_obj.fecha_compra = timezone.now()
                numero_obj.save()

            # NO borramos NumeroSeleccionado: sirve como historial.
            # Si quisieras borrarlos, lo harías aquí explícitamente.

    # ---------- TOTAL RECAUDADO EN LISTADO ----------
    def changelist_view(self, request, extra_context=None):
        total_pagado = Orden.objects.filter(
            estado="pagado"
        ).aggregate(total=Sum("total"))["total"] or 0

        extra_context = extra_context or {}
        # Para que funcione con cualquier template que uses:
        extra_context["total_pagado"] = total_pagado
        extra_context["total_recaudado"] = total_pagado

        return super().changelist_view(request, extra_context)


# =====================================================================
#   ADMIN — NÚMEROS
# =====================================================================
@admin.register(Numero)
class NumeroAdmin(admin.ModelAdmin):

    list_display = ('numero_formateado', 'rifa', 'comprado',
                    'participante_nombre', 'ver_orden')
    list_filter = ('rifa', 'comprado')
    search_fields = ('numero', 'participante__nombre', 'orden__id')
    list_per_page = 50

    # Seguridad
    delete_view = secure_delete_view
    response_action = secure_bulk_delete

    def delete_model(self, request, obj):
        return super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        return super().delete_queryset(request, queryset)

    def numero_formateado(self, obj):
        # Si luego cambias a más dígitos, aquí puedes adaptar.
        return obj.numero.zfill(4)

    def participante_nombre(self, obj):
        return obj.participante.nombre if obj.participante else "—"

    def ver_orden(self, obj):
        if obj.orden:
            return format_html(
                '<a href="/admin/app_rifas/orden/{}/change/">#{} ↗️</a>',
                obj.orden.id, obj.orden.id
            )
        return "—"


# =====================================================================
#   ADMIN — RIFAS
# =====================================================================
@admin.register(Rifa)
class RifaAdmin(admin.ModelAdmin):

    list_display = ['titulo', 'fecha_sorteo', 'precio_numero']
    change_form_template = "admin/app_rifas/rifa/change_form.html"

    # Seguridad
    delete_view = secure_delete_view
    response_action = secure_bulk_delete

    def delete_model(self, request, obj):
        return super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        return super().delete_queryset(request, queryset)

    # URLs personalizadas
    def get_urls(self):
        urls = super().get_urls()

        custom_urls = [
            path(
                "<int:rifa_id>/generar-numeros/",
                self.admin_site.admin_view(self.generar_numeros),
                name="app_rifas_rifa_generar_numeros"
            ),
            path(
                "<int:rifa_id>/regenerar-numeros/",
                self.admin_site.admin_view(self.regenerar_numeros),
                name="app_rifas_rifa_regenerar_numeros"
            ),
        ]
        return custom_urls + urls

    # Generar números
    def generar_numeros(self, request, rifa_id):
        rifa = Rifa.objects.get(id=rifa_id)

        if Numero.objects.filter(rifa=rifa).exists():
            messages.warning(request, "⚠️ Ya existen números. Use 'Re-generar números'.")
            return redirect(f"/admin/app_rifas/rifa/{rifa_id}/change/")

        if request.method == "GET":
            return render(request, "admin/app_rifas/rifa/generar_numeros.html", {"rifa": rifa})

        cantidad = int(request.POST.get("cantidad"))
        digitos = int(request.POST.get("digitos"))
        total_posibles = 10 ** digitos

        if cantidad > total_posibles:
            messages.error(request, "❌ No se pueden generar tantos números únicos.")
            return redirect(f"/admin/app_rifas/rifa/{rifa_id}/change/")

        nuevos = [str(n).zfill(digitos) for n in random.sample(range(total_posibles), cantidad)]

        Numero.objects.bulk_create([Numero(rifa=rifa, numero=n) for n in nuevos])

        messages.success(request, f"🎉 Generados {cantidad} números.")
        return redirect(f"/admin/app_rifas/rifa/{rifa_id}/change/")

    # Regenerar números
    def regenerar_numeros(self, request, rifa_id):
        rifa = Rifa.objects.get(id=rifa_id)

        if request.method == "GET":
            return render(request, "admin/app_rifas/rifa/regenerar_numeros.html", {"rifa": rifa})

        cantidad = int(request.POST.get("cantidad"))
        digitos = int(request.POST.get("digitos"))
        total_posibles = 10 ** digitos

        Numero.objects.filter(rifa=rifa).delete()

        if cantidad > total_posibles:
            messages.error(request, "❌ No se pueden generar tantos números únicos.")
            return redirect(f"/admin/app_rifas/rifa/{rifa_id}/change/")

        nuevos = [str(n).zfill(digitos) for n in random.sample(range(total_posibles), cantidad)]

        Numero.objects.bulk_create([Numero(rifa=rifa, numero=n) for n in nuevos])

        messages.success(request, "🔁 ¡Números regenerados correctamente!")
        return redirect(f"/admin/app_rifas/rifa/{rifa_id}/change/")

    # Estadísticas del panel
    def change_view(self, request, object_id, form_url='', extra_context=None):
        rifa = Rifa.objects.get(pk=object_id)
        numeros = Numero.objects.filter(rifa=rifa)

        total = numeros.count()
        vendidos = numeros.filter(comprado=True).count()
        disponibles = total - vendidos
        porcentaje = round((vendidos / total * 100), 2) if total else 0

        ctx = {
            "hay_numeros": total > 0,
            "total_numeros": total,
            "vendidos": vendidos,
            "disponibles": disponibles,
            "porcentaje": porcentaje,
            "rifa": rifa,
        }

        return super().change_view(request, object_id, form_url, extra_context=ctx)


# =====================================================================
#   ADMIN — PARTICIPANTES
# =====================================================================
@admin.register(Participante)
class ParticipanteAdmin(admin.ModelAdmin):

    list_display = ["nombre", "apellido", "cedula", "telefono"]

    # Seguridad
    delete_view = secure_delete_view
    response_action = secure_bulk_delete

    def delete_model(self, request, obj):
        return super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        return super().delete_queryset(request, queryset)


# =====================================================================
#   MODELOS RESTANTES
# =====================================================================
@admin.register(NumeroSeleccionado)
class NumeroSeleccionadoAdmin(admin.ModelAdmin):
    list_display = ['numero', 'rifa', 'participante', 'orden', 'fecha_seleccion']

admin.site.register(MensajeSorteo)
admin.site.register(SliderImagen)
admin.site.register(NumeroBendecido)

