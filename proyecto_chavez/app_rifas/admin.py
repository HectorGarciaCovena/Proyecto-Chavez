from django.contrib import admin
from django.core.exceptions import ValidationError
from .models import Participante, Orden, Numero, NumeroSeleccionado, NumeroBendecido, Rifa, MensajeSorteo, SliderImagen

class NumeroSeleccionadoInline(admin.TabularInline):
    model = NumeroSeleccionado
    extra = 0

class NumeroBendecidoAdmin(admin.ModelAdmin):
    list_display = ['numero']
    search_fields = ['numero']

class OrdenAdmin(admin.ModelAdmin):
    list_display = ('id', 'participante', 'estado', 'metodo_pago', 'total', 'pagado', 'fecha')
    list_filter = ('estado', 'metodo_pago')
    inlines = [NumeroSeleccionadoInline]

class NumeroAdmin(admin.ModelAdmin):
    list_display = ('numero', 'rifa', 'comprado')
    list_filter = ('rifa', 'comprado')
    search_fields = ('numero',)
    list_per_page = 50

admin.site.register(Participante)
admin.site.register(Orden, OrdenAdmin)
admin.site.register(Numero, NumeroAdmin)
admin.site.register(NumeroSeleccionado)
admin.site.register(Rifa)
admin.site.register(MensajeSorteo)
admin.site.register(SliderImagen)
admin.site.register(NumeroBendecido)

