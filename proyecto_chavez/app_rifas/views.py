# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from .forms import ParticipanteForm, OrdenForm
from .models import Orden, MensajeSorteo, NumeroSeleccionado, Numero, SliderImagen, Rifa, NumeroBendecido, Participante
from django.http import JsonResponse, HttpResponse
import io, base64
import qrcode
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.conf import settings
from django.templatetags.static import static
from django.views.decorators.cache import never_cache

from .models import Rifa, Numero

def home(request):
    mensaje = MensajeSorteo.objects.first()
    slider_imagenes = SliderImagen.objects.filter(activo=True)
    
    rifa = Rifa.objects.first()
    total_numeros = rifa.total_numeros() if rifa else 1
    numeros_vendidos = Numero.objects.filter(comprado=True).count()
    porcentaje_vendidos = round((numeros_vendidos / total_numeros) * 100) if total_numeros else 0

    return render(request, 'app_rifas/home.html', {
        'mensaje': mensaje,
        'slider_imagenes': slider_imagenes,
        'rifa': rifa,
        'total_numeros': total_numeros,
        'numeros_vendidos': numeros_vendidos,
        'porcentaje_vendidos': porcentaje_vendidos,
    })

def crear_pedido(request):
    rifa = Rifa.objects.first()
    cantidad = int(request.GET.get("cantidad") or request.POST.get("cantidad") or 1)

    if not rifa:
        messages.error(request, "No hay una rifa activa.")
        return redirect("home")

    numero_min = rifa.numero_inicial
    numero_max = rifa.numero_final

    if request.method == 'POST':
        participante_form = ParticipanteForm(request.POST)
        orden_form = OrdenForm(request.POST)

        numeros_str = request.POST.get('numeros_favoritos', '')
        numeros = [n.strip() for n in numeros_str.split(',') if n.strip()]

        if participante_form.is_valid() and orden_form.is_valid():
            if len(numeros) != cantidad:
                orden_form.add_error(None, f"Debe ingresar exactamente {cantidad} números.")
            elif any(not n.isdigit() or not (numero_min <= int(n) <= numero_max) for n in numeros):
                orden_form.add_error(None, f"Todos los números deben tener entre {numero_min} y {numero_max}.")
            elif len(set(numeros)) != len(numeros):
                orden_form.add_error(None, "Los números no deben repetirse.")
            else:
                cedula = participante_form.cleaned_data['cedula']
                participante, creado = Participante.objects.get_or_create(
                    cedula=cedula,
                    defaults={
                        'nombre': participante_form.cleaned_data['nombre'],
                        'apellido': participante_form.cleaned_data['apellido'],
                        'email': participante_form.cleaned_data['email'],
                        'telefono': participante_form.cleaned_data['telefono'],
                        'pais': participante_form.cleaned_data['pais'],
                        'provincia': participante_form.cleaned_data['provincia'],
                        'ciudad': participante_form.cleaned_data['ciudad'],
                        'direccion': participante_form.cleaned_data['direccion'],
                    }
                )

                orden = orden_form.save(commit=False)
                orden.participante = participante
                orden.fecha = timezone.now()
                orden.total = rifa.precio_numero * cantidad
                orden.save()

                for numero in numeros:
                    NumeroSeleccionado.objects.create(orden=orden, numero=numero)

                return redirect('detalle_pedido', orden.id)
    else:
        participante_form = ParticipanteForm()
        orden_form = OrdenForm()

    total_numeros = rifa.total_numeros()
    numeros_vendidos = Numero.objects.filter(rifa=rifa, comprado=True).count()
    porcentaje = int((numeros_vendidos / total_numeros) * 100) if total_numeros else 0

    return render(request, 'app_rifas/crear_pedido.html', {
        'participante_form': participante_form,
        'orden_form': orden_form,
        'cantidad_maxima': cantidad,
        'rifa': rifa,
        'numeros_vendidos': numeros_vendidos,
        'total_numeros': total_numeros,
        'porcentaje': porcentaje,
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
    orden = get_object_or_404(Orden, pk=orden_id)

    if orden.estado != "pagado":
        return redirect("detalle_pedido", pedido_id=orden_id)

    numeros = Numero.objects.filter(orden=orden)
    rifa = Rifa.objects.first()

    # QR
    qr_url = f"{settings.SITE_URL}/verificar-boleta/{orden.id}"
    qr_img = qrcode.make(qr_url)
    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format="PNG")
    qr_base64 = base64.b64encode(qr_buffer.getvalue()).decode('utf-8')

    context = {
        "orden": orden,
        "participante": orden.participante,
        "numeros": numeros,
        "rifa": rifa,
        "qr_base64": qr_base64,
        "logo_url": request.build_absolute_uri(static('app_rifas/img/logo.png')),
    }

    template = get_template("app_rifas/boleto.html")
    html = template.render(context)
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html.encode("utf-8")), dest=result)

    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="boleto_orden_{orden.id}.pdf"'
        return response

    return HttpResponse("Error al generar PDF", status=500)

def verificar_participante(request, cedula):
    try:
        participante = Participante.objects.get(cedula=cedula)
        return JsonResponse({
            "existe": True,
            "nombre": participante.nombre,
            "apellido": participante.apellido,
            "email": participante.email,
            "telefono": participante.telefono,
            "direccion": participante.direccion,
            "ciudad": participante.ciudad,
            "provincia": participante.provincia,
            "pais": participante.pais,
        })
    except Participante.DoesNotExist:
        return JsonResponse({"existe": False})

@never_cache
def selector_numeros(request, cantidad):
    rifa = Rifa.objects.first()
    if not rifa:
        return HttpResponse("No hay rifa activa.", status=404)

    vendidos = Numero.objects.filter(rifa=rifa, comprado=True).values_list('numero', flat=True)

    # ✅ Generar el rango en Python
    rango_numeros = range(rifa.numero_inicial, rifa.numero_final + 1)

    return render(request, 'app_rifas/selector_numeros.html', {
        'cantidad': int(cantidad),
        'numero_min': rifa.numero_inicial,
        'numero_max': rifa.numero_final,
        'vendidos': list(vendidos),
        'rango_numeros': rango_numeros,  # ← esto es clave
    })