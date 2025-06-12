from django.contrib import admin
from .models import Participante, Orden, Rifa, Numero, MensajeSorteo

admin.site.register(Participante)
admin.site.register(Orden)
admin.site.register(Rifa)
admin.site.register(Numero)
admin.site.register(MensajeSorteo)
