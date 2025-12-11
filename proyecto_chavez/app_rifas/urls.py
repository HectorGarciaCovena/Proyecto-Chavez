from django.urls import path
from . import views
from django.conf import settings

urlpatterns = [
    path('', views.home, name='home'),
    path('crear-pedido/', views.crear_pedido, name='crear_pedido'),
    path('detalle-pedido/<int:pedido_id>/', views.detalle_pedido, name='detalle_pedido'),
    path('simular-pago/<int:orden_id>/', views.simular_pago, name='simular_pago'),
    path('boleta/<int:orden_id>/', views.generar_boleta, name='generar_boleta'),
    path('verificar-numero/<str:numero>/', views.verificar_numero, name='verificar_numero'),
    path('generar-boleta/<int:orden_id>/', views.generar_boleta, name='generar_boleta'),
    path('verificar-participante/<str:cedula>/', views.verificar_participante, name='verificar_participante'),
    path("selector-numeros/<int:rifa_id>/", views.selector_numeros, name="selector_numeros"),
    path('paypal/create/<int:orden_id>/', views.paypal_create_order, name='paypal_create'),
    path('paypal/success/', views.paypal_success_view, name='paypal_success'),
    path('paypal/cancel/', views.paypal_cancel_view, name='paypal_cancel'),
    path('cancelar-pedido/<int:pedido_id>/', views.cancelar_pedido, name='cancelar_pedido'),
]





