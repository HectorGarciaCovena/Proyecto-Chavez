from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('crear-pedido/', views.crear_pedido, name='crear_pedido'),
    path('detalle-pedido/<int:pedido_id>/', views.detalle_pedido, name='detalle_pedido'),
    path('simular-pago/<int:orden_id>/', views.simular_pago, name='simular_pago'),
    path('boleta/<int:orden_id>/', views.generar_boleta, name='generar_boleta'),
]





