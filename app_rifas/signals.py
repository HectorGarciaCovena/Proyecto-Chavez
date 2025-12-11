from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import NumeroSeleccionado, Numero, Orden

@receiver(post_delete, sender=NumeroSeleccionado)
def liberar_numero_y_orden(sender, instance, **kwargs):
    # -----------------------------------------
    # 1. LIBERAR EL NÚMERO EN TABLA Numero
    # -----------------------------------------
    if instance.rifa_id:
        try:
            numero_int = int(instance.numero)
            Numero.objects.filter(
                numero=numero_int,
                rifa_id=instance.rifa_id
            ).update(
                comprado=False,
                participante=None,
                orden=None,
                fecha_compra=None
            )
        except ValueError:
            pass  # Si no se puede convertir el número, lo ignoramos

    # ---------------------------------------------------------
    # 2. ELIMINAR LA ORDEN SI NO TIENE MÁS NÚMEROS RELACIONADOS
    # ---------------------------------------------------------
    orden_id = instance.orden_id
    if not orden_id:
        return

    # Ver si quedan números ligados a esa orden
    aun_tiene_numeros = NumeroSeleccionado.objects.filter(orden_id=orden_id).exists()

    if not aun_tiene_numeros:
        # Eliminar sin error, incluso si ya no existe
        Orden.objects.filter(id=orden_id).delete()
