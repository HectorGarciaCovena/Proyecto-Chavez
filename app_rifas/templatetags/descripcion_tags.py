from django import template
import re

register = template.Library()

@register.filter(name='format_descripcion')
def format_descripcion(value):
    if not value:
        return ""

    icon_map = {
        r'\b(carro|auto|camioneta|vehículo)\b': '🚙',
        r'\b(modelo|marca)\b': '🏷️',
        r'\bcolor\b': '🎨',
        r'\bkilometraje\b': '🔧',
        r'\b0 ?km\b': '✨ 0km',
        r'\bestado\b': '✅',
        r'\b4x4\b': '🎯 4x4',
        r'\b4x2\b': '🎯 4x2',
        r'\b202[0-9]\b': '📅 \\g<0>',
    }

    for pattern, icon in icon_map.items():
        value = re.sub(pattern, icon, value, flags=re.IGNORECASE)

    value = re.sub(r',\s*', '<br>', value)
    return value
