# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from .forms import ParticipanteForm, OrdenForm
from .models import Orden, MensajeSorteo, NumeroSeleccionado, Numero, SliderImagen, Rifa, NumeroBendecido, Participante
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
import io, base64,json, requests, qrcode
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.conf import settings
from django.templatetags.static import static
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.urls import reverse
from .utils import get_paypal_access_token
from django.contrib.staticfiles import finders
from django.shortcuts import render
from app_rifas.models import Rifa, Numero, SliderImagen

def home(request):
    rifa = Rifa.objects.first()

    numeros_total = Numero.objects.filter(rifa=rifa).count()
    numeros_vendidos = Numero.objects.filter(rifa=rifa, comprado=True).count()

    porcentaje = 0
    if numeros_total > 0:
        porcentaje = round((numeros_vendidos / numeros_total) * 100, 2)

    # Cargar imágenes ACTIVAS del slider
    slider_imagenes = SliderImagen.objects.filter(activo=True)

    return render(request, "app_rifas/home.html", {
        "rifa": rifa,
        "numeros_vendidos": numeros_vendidos,
        "total_numeros": numeros_total,
        "porcentaje_vendidos": porcentaje,
        "slider_imagenes": slider_imagenes,
    })

def crear_pedido(request):

    # Obtener rifa activa
    rifa = Rifa.objects.first()

    if not rifa:
        messages.error(request, "⚠️ No hay rifas activas en este momento.")
        return redirect("home")

    # Cantidad solicitada
    cantidad = request.GET.get("cantidad") or request.POST.get("cantidad") or 1
    try:
        cantidad = int(cantidad)
        if cantidad < 1:
            cantidad = 1
    except:
        cantidad = 1

    # =========================================
    # POST — Procesamiento del pedido
    # =========================================
    if request.method == "POST":

        participante_form = ParticipanteForm(request.POST)
        orden_form = OrdenForm(request.POST)

        numeros_str_list = request.POST.get("numeros_favoritos", "").split(",")
        numeros_str_list = [n.strip() for n in numeros_str_list if n.strip()]

        metodo_pago = request.POST.get("metodo_pago")

        # ==========================
        # VALIDACIONES
        # ==========================

        if metodo_pago != "transferencia":
            messages.error(request, "Método de pago inválido.")
            return redirect("crear_pedido")

        if len(numeros_str_list) != cantidad:
            messages.error(request, f"Debe seleccionar exactamente {cantidad} números.")
            return redirect("crear_pedido")

        if not participante_form.is_valid():
            messages.error(request, "Complete correctamente todos los campos del formulario.")
            return redirect("crear_pedido")

        # ==========================
        # CREAR O RECUPERAR PARTICIPANTE
        # ==========================

        cedula = participante_form.cleaned_data["cedula"]
        participante, _ = Participante.objects.get_or_create(
            cedula=cedula,
            defaults=participante_form.cleaned_data
        )

        # ==========================
        # CREAR ORDEN (siempre PENDIENTE)
        # ==========================

        total = rifa.precio_numero * cantidad

        orden = Orden.objects.create(
            participante=participante,
            rifa=rifa,
            metodo_pago="transferencia",
            total=total,
            estado="pendiente",
            pagado=False,
        )

        # ==========================
        # PROCESAR NÚMEROS
        # ==========================

        for numero_str in numeros_str_list:
            try:
                # Validar existencia del número
                if not Numero.objects.filter(numero=numero_str, rifa=rifa).exists():
                    messages.error(request, f"El número {numero_str} no existe en esta rifa.")
                    orden.delete()
                    return redirect("crear_pedido")

                numero_obj = Numero.objects.get(numero=numero_str, rifa=rifa)

                if numero_obj.comprado:
                    messages.error(request, f"El número {numero_str} ya fue vendido.")
                    orden.delete()
                    return redirect("crear_pedido")

                # Crear número seleccionado temporal
                NumeroSeleccionado.objects.create(
                    orden=orden,
                    numero=numero_str,
                    rifa=rifa,
                    participante=participante
                )

            except Exception:
                messages.error(request, f"Número inválido: {numero_str}")
                orden.delete()
                return redirect("crear_pedido")

        # ==========================
        # FIN — Siempre pendiente
        # ==========================
        return redirect("detalle_pedido", pedido_id=orden.id)

    # =========================================
    # GET — Formulario vacío
    # =========================================

    participante_form = ParticipanteForm()
    orden_form = OrdenForm()

    return render(request, "app_rifas/crear_pedido.html", {
        "rifa": rifa,
        "cantidad_maxima": cantidad,
        "participante_form": participante_form,
        "orden_form": orden_form,
    })

def detalle_pedido(request, pedido_id):
    pedido = get_object_or_404(Orden, pk=pedido_id)

    # Si el cliente decide cancelar desde esta vista
    if request.method == 'POST' and 'cancelar' in request.POST and pedido.estado == 'pendiente':
        # Liberar números seleccionados
        NumeroSeleccionado.objects.filter(orden=pedido).delete()
        pedido.delete()
        return render(request, 'app_rifas/cancel.html')

    # Obtener números según estado de la orden
    if pedido.estado == 'pagado':
        numeros = Numero.objects.filter(orden=pedido).order_by('numero')
    else:
        numeros = NumeroSeleccionado.objects.filter(orden=pedido).order_by('numero')

    # Generar URL para continuar el pago (respetando método original)
    metodo_param = "?metodo=tarjeta" if pedido.metodo_pago == "tarjeta" else ""
    metodo_pago_url = reverse("paypal_create", args=[pedido.id]) + metodo_param

    return render(request, 'app_rifas/detalle_pedido.html', {
        'pedido': pedido,
        'numeros': numeros,
        'metodo_pago_url': metodo_pago_url,
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

    # --- Generar QR ---
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

    # --- Renderizar HTML ---
    template = get_template("app_rifas/boleto.html")
    html = template.render(context)

    # --- Cargar CSS externo ---
    css_path = finders.find('app_rifas/css/boleto_pdf.css')
    if css_path:
        with open(css_path, "r", encoding="utf-8") as f:
            css_content = f.read()
        html = f"<style>{css_content}</style>" + html

    # --- Convertir a PDF ---
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html.encode("utf-8")), dest=result)

    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename=\"boleto_orden_{orden.id}.pdf\"'
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
def selector_numeros(request, rifa_id):
    rifa = Rifa.objects.get(id=rifa_id)

    # Obtener todos los números creados para esa rifa
    numeros = list(rifa.numeros.values_list("numero", flat=True))

    cantidad = int(request.GET.get("cantidad", 1))

    return render(request, "app_rifas/selector_numeros.html", {
        "rifa": rifa,
        "cantidad_maxima": cantidad,
        "numeros": numeros,
        "vendidos": list(rifa.numeros.filter(comprado=True).values_list("numero", flat=True)),
    })


@csrf_exempt
def paypal_create_order(request, orden_id):
    orden = get_object_or_404(Orden, id=orden_id, estado="pendiente")

    # Leer el método desde la URL (?metodo=tarjeta o ?metodo=paypal)
    metodo = request.GET.get("metodo", "paypal")
    landing_page = "BILLING" if metodo == "tarjeta" else "LOGIN"
    access_token = get_paypal_access_token()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }

    order_data = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "amount": {
                    "currency_code": "USD",
                    "value": str(orden.total),
                },
                "description": f"Orden #{orden.id} - Participación en rifa",
            }
        ],
        "application_context": {
            "brand_name": "DYL Sorteos",
            "landing_page": landing_page,  # ← aquí se usa correctamente
            "user_action": "PAY_NOW",
            "return_url": request.build_absolute_uri(
                reverse("paypal_success") + f"?orden_id={orden.id}"
            ),
            "cancel_url": request.build_absolute_uri(
                reverse("paypal_cancel") + f"?orden_id={orden.id}"
            ),
        },
    }

    response = requests.post(
        f"{settings.PAYPAL_API_BASE}/v2/checkout/orders",
        headers=headers,
        json=order_data,
    )

    if response.status_code in [200, 201]:
        data = response.json()
        for link in data.get("links", []):
            if link["rel"] == "approve":
                return redirect(link["href"])
        return JsonResponse({"error": "No se encontró el enlace de aprobación."}, status=400)
    else:
        return JsonResponse({"error": "Error al crear la orden en PayPal."}, status=400)

@csrf_exempt
def paypal_success_view(request):
    orden_id = request.GET.get('orden_id')
    orden = get_object_or_404(Orden, id=orden_id, estado='pendiente')

    rifa = orden.rifa
    participante = orden.participante
    numeros_temp = NumeroSeleccionado.objects.filter(orden=orden)
    cantidad_numeros = numeros_temp.count()

    # Actualizar orden como pagada
    orden.total = rifa.precio_numero * cantidad_numeros
    orden.estado = 'pagado'
    orden.pagado = True
    orden.save()

    # Convertir números reservados en números vendidos reales
    for seleccionado in numeros_temp:
        numero_str = seleccionado.numero
        numero_int = int(numero_str)

        numero_obj, creado = Numero.objects.get_or_create(
            numero=numero_int,
            rifa=rifa,
            defaults={
                'comprado': True,
                'participante': participante,
                'orden': orden,
                'fecha_compra': timezone.now()
            }
        )

        if not creado:
            numero_obj.comprado = True
            numero_obj.participante = participante
            numero_obj.orden = orden
            numero_obj.fecha_compra = timezone.now()
            numero_obj.save()

    # Eliminar solo los temporales (no pierde historial)
    numeros_temp.delete()

    messages.success(request, f"✅ El pago de la orden #{orden.id} fue exitoso mediante PayPal.")
    return redirect('detalle_pedido', pedido_id=orden.id)

@csrf_protect
def cancelar_pedido(request, pedido_id):
    if request.method == 'POST':
        orden = get_object_or_404(Orden, id=pedido_id, estado='pendiente')

        # Liberar los números asignados a esta orden
        numeros = Numero.objects.filter(orden=orden)
        for numero in numeros:
            numero.comprado = False
            numero.participante = None
            numero.orden = None
            numero.fecha_compra = None
            numero.save()

        # Eliminar registros de NumeroSeleccionado
        NumeroSeleccionado.objects.filter(orden=orden).delete()

        # Eliminar la orden
        orden.delete()

        # Mostrar cancel.html en lugar de redirigir al home
        return render(request, 'app_rifas/cancel.html')

    messages.error(request, "❌ Acción no permitida.")
    return redirect('home')

def paypal_cancel_view(request):
    pedido_id = request.GET.get("orden_id")
    if pedido_id:
        return redirect('detalle_pedido', pedido_id=pedido_id)
    return redirect('home')  # fallback


