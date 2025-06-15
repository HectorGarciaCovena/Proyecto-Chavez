from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css_class):
    attrs = field.field.widget.attrs
    attrs['class'] = css_class
    attrs['required'] = True  # ← esta línea es clave
    return field.as_widget(attrs=attrs)



