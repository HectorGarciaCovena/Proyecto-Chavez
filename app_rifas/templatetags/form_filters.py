from django import template
from django.forms.boundfield import BoundField

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css_class):
    # Si NO es un campo de formulario, devuélvelo sin modificar
    if not isinstance(field, BoundField):
        return field  

    # Si ES un BoundField, añade la clase y el required
    widget = field.field.widget
    attrs = widget.attrs.copy()  # ← evita editar attrs globales del widget
    attrs['class'] = css_class
    attrs['required'] = True

    return field.as_widget(attrs=attrs)