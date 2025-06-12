from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('participar/', views.crear_pedido, name='crear_pedido'),
]

