from django.db import models
from django.core.exceptions import ValidationError

# Validador de cédula ecuatoriana
def validar_cedula_ecuador(value):
    if not value.isdigit() or len(value) != 10:
        raise ValidationError("La cédula debe tener exactamente 10 dígitos.")

    provincia = int(value[:2])
    if provincia < 1 or provincia > 24:
        raise ValidationError("La cédula ingresada no pertenece a una provincia válida.")

    coeficientes = [2, 1, 2, 1, 2, 1, 2, 1, 2]
    suma = sum((x if x < 10 else x - 9) for x in [int(a)*b for a, b in zip(value[:9], coeficientes)])
    verificador = int(value[9])
    if (10 - suma % 10) % 10 != verificador:
        raise ValidationError("La cédula ingresada no es válida.")

class Participante(models.Model):
    cedula = models.CharField(max_length=10, blank=True, validators=[validar_cedula_ecuador])
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
    pagado = models.BooleanField(default=False)

    def __str__(self):
        return f"Orden #{self.id} - {self.participante}"

class Rifa(models.Model):
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    fecha_sorteo = models.DateField()
    precio_numero = models.DecimalField(max_digits=6, decimal_places=2)
    numero_inicial = models.PositiveIntegerField(default=10000)
    numero_final = models.PositiveIntegerField(default=19999)

    def total_numeros(self):
        return self.numero_final - self.numero_inicial + 1

    def __str__(self):
        return self.titulo

class Numero(models.Model):
    numero = models.PositiveIntegerField()
    rifa = models.ForeignKey(Rifa, on_delete=models.CASCADE, related_name='numeros')
    participante = models.ForeignKey(Participante, on_delete=models.SET_NULL, null=True, blank=True)
    orden = models.ForeignKey(Orden, on_delete=models.SET_NULL, null=True, blank=True)
    comprado = models.BooleanField(default=False)
    fecha_compra = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.numero:05d} - {self.rifa.titulo}"

class NumeroSeleccionado(models.Model):
    orden = models.ForeignKey('Orden', on_delete=models.CASCADE, related_name='numeros')
    numero = models.CharField(max_length=5)

    def __str__(self):
        return self.numero

class MensajeSorteo(models.Model):
    mensaje = models.TextField("Mensaje principal")
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Mensaje del Sorteo"
        verbose_name_plural = "Mensaje del Sorteo"

    def __str__(self):
        return "Mensaje Principal del Sorteo"

class SliderImagen(models.Model):
    titulo = models.CharField(max_length=100)
    imagen = models.ImageField(upload_to='slider/')
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.titulo

class NumeroBendecido(models.Model):
    numero = models.CharField(max_length=5, unique=True)
    rifa = models.ForeignKey(Rifa, on_delete=models.CASCADE, related_name='bendecidos')

    def clean(self):
        if not self.numero.isdigit():
            raise ValidationError("El número debe contener solo dígitos.")
        if len(self.numero) != 5:
            raise ValidationError("El número debe tener exactamente 5 dígitos.")

    def save(self, *args, **kwargs):
        self.full_clean()  # Llama a clean() antes de guardar
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.numero} (Rifa: {self.rifa.titulo})"
