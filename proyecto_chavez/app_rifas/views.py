from django.shortcuts import render, redirect
from django.utils import timezone
from .forms import ParticipanteForm, OrdenForm
from .models import Orden, MensajeSorteo

def home(request):
    mensaje = MensajeSorteo.objects.first()
    return render(request, 'app_rifas/home.html', {'mensaje': mensaje})

def crear_pedido(request):
    cantidad = int(request.GET.get('cantidad', 1))  # Valor por defecto si no viene en la URL

    if request.method == 'POST':
        participante_form = ParticipanteForm(request.POST)
        orden_form = OrdenForm(request.POST, cantidad=cantidad)

        if participante_form.is_valid() and orden_form.is_valid():
            participante = participante_form.save()

            orden = orden_form.save(commit=False)
            orden.participante = participante
            orden.fecha = timezone.now()
            orden.total = 0
            orden.save()

            return redirect('pedido_exitoso')
    else:
        participante_form = ParticipanteForm()
        orden_form = OrdenForm(cantidad=cantidad)

    return render(request, 'app_rifas/crear_pedido.html', {
        'participante_form': participante_form,
        'orden_form': orden_form,
    })