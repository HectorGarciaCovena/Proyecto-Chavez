from django import forms
from .models import Participante, Orden
import re

class ParticipanteForm(forms.ModelForm):
    class Meta:
        model = Participante
        fields = '__all__'

class OrdenForm(forms.ModelForm):
    numeros_favoritos = forms.CharField(
        label="Números Favoritos",
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Ej: 123456,234567,345678'})
    )

    class Meta:
        model = Orden
        fields = ['estado', 'metodo_pago', 'numeros_favoritos']

    def __init__(self, *args, **kwargs):
        # Capturar la cantidad desde la vista
        self.cantidad = kwargs.pop('cantidad', None)
        super().__init__(*args, **kwargs)

    def clean_numeros_favoritos(self):
        data = self.cleaned_data['numeros_favoritos']
        cantidad = self.cantidad

        if not data:
            raise forms.ValidationError("Debe ingresar los números favoritos separados por comas.")

        numeros = [n.strip() for n in data.split(',') if n.strip()]
        
        # Validación: cantidad exacta
        if cantidad and len(numeros) != cantidad:
            raise forms.ValidationError(f"Debe ingresar exactamente {cantidad} números.")

        # Validación: formato de cada número
        for n in numeros:
            if not re.fullmatch(r'\d{6}', n):
                raise forms.ValidationError(f"El número '{n}' no tiene exactamente 6 dígitos.")

        # Validación: que no estén repetidos
        if len(set(numeros)) != len(numeros):
            raise forms.ValidationError("Los números no deben repetirse.")

        return data

