from django.db import models

# Modelo de Participante (cliente)
class Participante(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    email = models.EmailField()
    telefono = models.CharField(max_length=20, blank=True)
    pais = models.CharField(max_length=50, default="Ecuador")
    provincia = models.CharField(max_length=50)
    ciudad = models.CharField(max_length=50)
    direccion = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"


# Modelo de Orden o Compra
class Orden(models.Model):
    participante = models.ForeignKey(Participante, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    metodo_pago = models.CharField(max_length=50, choices=[
        ("transferencia", "Transferencia bancaria"),
        ("tarjeta", "Tarjeta de crédito/débito"),
        ("paypal", "PayPal"),
    ])
    total = models.DecimalField(max_digits=8, decimal_places=2)
    estado = models.CharField(max_length=20, choices=[
        ("pendiente", "Pendiente"),
        ("pagado", "Pagado"),
        ("cancelado", "Cancelado"),
    ], default="pendiente")

    def __str__(self):
        return f"Orden #{self.id} - {self.participante}"


# Modelo de Rifa (asumo que ya existe, pero incluyo aquí por claridad)
class Rifa(models.Model):
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    fecha_sorteo = models.DateField()
    precio_numero = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return self.titulo


# Modelo de Número (boleto de rifa)
class Numero(models.Model):
    numero = models.PositiveIntegerField()
    rifa = models.ForeignKey(Rifa, on_delete=models.CASCADE, related_name='numeros')
    participante = models.ForeignKey(Participante, on_delete=models.SET_NULL, null=True, blank=True)
    orden = models.ForeignKey(Orden, on_delete=models.SET_NULL, null=True, blank=True)
    comprado = models.BooleanField(default=False)
    fecha_compra = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.numero:05d} - {self.rifa.titulo}"

# Mensaje que aparece en la pantalla principal (editable desde el admin)
class MensajeSorteo(models.Model):
    mensaje = models.TextField("Mensaje principal")
    actualizado = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Mensaje Principal del Sorteo"

    class Meta:
        verbose_name = "Mensaje del Sorteo"
        verbose_name_plural = "Mensaje del Sorteo"

class NumeroSeleccionado(models.Model):
    orden = models.ForeignKey('Orden', on_delete=models.CASCADE, related_name='numeros')
    numero = models.CharField(max_length=6)

    def __str__(self):
        return self.numero
