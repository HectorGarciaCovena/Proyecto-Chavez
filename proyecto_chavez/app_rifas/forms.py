from django import forms
from .models import Participante, Orden

class ParticipanteForm(forms.ModelForm):
    class Meta:
        model = Participante
        fields = '__all__'

    def clean_cedula(self):
        cedula = self.cleaned_data.get('cedula')
        if not cedula or not cedula.isdigit() or len(cedula) != 10:
            raise forms.ValidationError("La cédula debe tener 10 dígitos numéricos.")

        provincia = int(cedula[:2])
        if provincia < 1 or provincia > 24:
            raise forms.ValidationError("Código de provincia inválido.")

        coef = [2, 1, 2, 1, 2, 1, 2, 1, 2]
        suma = sum((a if a < 10 else a - 9) for a in [int(x) * y for x, y in zip(cedula[:9], coef)])
        verificador = int(cedula[9])
        if (10 - suma % 10) % 10 != verificador:
            raise forms.ValidationError("La cédula no es válida.")

        return cedula

class OrdenForm(forms.ModelForm):
    metodo_pago = forms.CharField(widget=forms.HiddenInput(), required=True)

    class Meta:
        model = Orden
        fields = ['metodo_pago']
 
