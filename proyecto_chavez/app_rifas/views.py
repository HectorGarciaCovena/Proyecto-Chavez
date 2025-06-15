# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from .forms import ParticipanteForm, OrdenForm
from .models import Orden, MensajeSorteo, NumeroSeleccionado, Numero, SliderImagen, Rifa, Participante
from django.http import JsonResponse
import io
import qrcode
from django.http import FileResponse, HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa

def home(request):
    mensaje = MensajeSorteo.objects.first()
    slider_imagenes = SliderImagen.objects.filter(activo=True)
    return render(request, 'app_rifas/home.html', {
        'mensaje': mensaje,
        'slider_imagenes': slider_imagenes
    })

def crear_pedido(request):
    cantidad = int(request.GET.get("cantidad") or request.POST.get("cantidad") or 1)

    if request.method == 'POST':
        participante_form = ParticipanteForm(request.POST)
        orden_form = OrdenForm(request.POST)

        numeros_str = request.POST.get('numeros_favoritos', '')
        numeros = [n.strip() for n in numeros_str.split(',') if n.strip()]

        if participante_form.is_valid() and orden_form.is_valid():
            vendidos = Numero.objects.filter(numero__in=numeros, comprado=True).values_list('numero', flat=True)
            duplicados = set(numeros) & set(str(n) for n in vendidos)
            if duplicados:
                orden_form.add_error(None, f"Los siguientes números ya están vendidos: {', '.join(duplicados)}")
            elif len(numeros) != cantidad:
                orden_form.add_error(None, f"Debe ingresar exactamente {cantidad} números.")
            elif any(len(n) != 6 or not n.isdigit() for n in numeros):
                orden_form.add_error(None, "Todos los números deben tener exactamente 6 dígitos.")
            elif len(set(numeros)) != len(numeros):
                orden_form.add_error(None, "Los números no deben repetirse.")
            else:
                cedula = participante_form.cleaned_data['cedula']
                participante, creado = Participante.objects.get_or_create(
                    cedula=cedula,
                    defaults=participante_form.cleaned_data
                )
                orden = orden_form.save(commit=False)
                orden.participante = participante
                orden.fecha = timezone.now()
                orden.estado = 'pendiente'
                orden.pagado = False
                orden.total = 0
                orden.save()

                for numero in numeros:
                    NumeroSeleccionado.objects.create(orden=orden, numero=numero)

                return redirect('detalle_pedido', orden.id)
    else:
        participante_form = ParticipanteForm()
        orden_form = OrdenForm()

    return render(request, 'app_rifas/crear_pedido.html', {
        'participante_form': participante_form,
        'orden_form': orden_form,
        'cantidad_maxima': cantidad
    })

def detalle_pedido(request, pedido_id):
    pedido = get_object_or_404(Orden, pk=pedido_id)
    numeros = NumeroSeleccionado.objects.filter(orden=pedido)
    return render(request, 'app_rifas/detalle_pedido.html', {
        'pedido': pedido,
        'numeros': numeros,
    })
    

def simular_pago(request, orden_id):
    orden = get_object_or_404(Orden, id=orden_id, estado='pendiente')

    if request.method in ['POST', 'GET']:
        rifa = Rifa.objects.first()
        if not rifa:
            messages.error(request, "⚠️ No hay ninguna rifa creada. Por favor, crea una antes de simular el pago.")
            return redirect('detalle_pedido', orden.id)

        numeros_seleccionados = NumeroSeleccionado.objects.filter(orden=orden)
        cantidad_numeros = numeros_seleccionados.count()
        orden.total = rifa.precio_numero * cantidad_numeros
        orden.estado = 'pagado'
        orden.pagado = True
        orden.save()

        for seleccionado in numeros_seleccionados:
            numero = int(seleccionado.numero)
            numero_obj, creado = Numero.objects.get_or_create(
                numero=numero,
                rifa=rifa,
                defaults={
                    'comprado': True,
                    'participante': orden.participante,
                    'orden': orden,
                    'fecha_compra': timezone.now()
                }
            )
            if not creado:
                numero_obj.comprado = True
                numero_obj.participante = orden.participante
                numero_obj.orden = orden
                numero_obj.fecha_compra = timezone.now()
                numero_obj.save()

        numeros_seleccionados.delete()
        messages.success(request, f"✅ El pago de la orden #{orden.id} fue simulado exitosamente.")
        return redirect('detalle_pedido', orden.id)

    return redirect('home')

def verificar_numero(request, numero):
    vendido = Numero.objects.filter(numero=numero, comprado=True).exists()
    return JsonResponse({'vendido': vendido})

def generar_boleta(request, orden_id):
    orden = Orden.objects.get(pk=orden_id)

    if orden.estado != "pagado":
        return redirect("detalle_pedido", pedido_id=orden_id)

    numeros = NumeroSeleccionado.objects.filter(orden=orden)
    rifa = Rifa.objects.first()  # Ajusta si manejas varias rifas

    # Generar QR
    qr_url = f"http://tusitio.com/verificar-boleta/{orden.id}"
    qr_img = qrcode.make(qr_url)
    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format="PNG")
    qr_base64 = qr_buffer.getvalue().hex()

    # Preparar contexto
    context = {
        "orden": orden,
        "participante": orden.participante,
        "numeros": numeros,
        "rifa": rifa,
        "qr_base64": qr_base64,
    }

    # Generar PDF desde HTML
    template = get_template("app_rifas/boleto.html")
    html = template.render(context)
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html.encode("utf-8")), result)

    if not pdf.err:
        return FileResponse(result, as_attachment=True, filename=f"boleto_orden_{orden.id}.pdf")
    return HttpResponse("Error al generar PDF", status=500)