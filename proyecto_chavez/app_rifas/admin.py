from django.contrib import admin
from django.core.exceptions import ValidationError
from .models import Participante, Orden, Numero, NumeroSeleccionado, NumeroBendecido, Rifa, MensajeSorteo, SliderImagen
from django.db.models import Sum

class NumeroSeleccionadoInline(admin.TabularInline):
    model = NumeroSeleccionado
    extra = 0

class NumeroBendecidoAdmin(admin.ModelAdmin):
    list_display = ['numero']
    search_fields = ['numero']

# Tu admin personalizado para mostrar total recaudado
@admin.register(Orden)
class OrdenAdmin(admin.ModelAdmin):
    list_display = ('id', 'participante', 'metodo_pago', 'total', 'estado', 'pagado', 'fecha')
    list_filter = ('estado', 'metodo_pago', 'pagado')
    search_fields = ('participante__cedula', 'participante__nombre', 'participante__apellido')
    date_hierarchy = 'fecha'

    change_list_template = "admin/recaudacion_total.html"

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        try:
            queryset = response.context_data['cl'].queryset
            total_pagado = queryset.filter(estado='pagado').aggregate(Sum('total'))['total__sum'] or 0
            response.context_data['total_pagado'] = total_pagado
        except (AttributeError, KeyError):
            pass
        return response

class NumeroAdmin(admin.ModelAdmin):
    list_display = ('numero', 'rifa', 'comprado')
    list_filter = ('rifa', 'comprado')
    search_fields = ('numero',)
    list_per_page = 50

admin.site.register(Participante)
admin.site.register(Numero, NumeroAdmin)
admin.site.register(NumeroSeleccionado)
admin.site.register(Rifa)
admin.site.register(MensajeSorteo)
admin.site.register(SliderImagen)
admin.site.register(NumeroBendecido)

