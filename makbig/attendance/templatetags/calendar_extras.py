from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    Generic dictionary getter:
    {{ my_dict|get_item:key }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)


@register.filter
def get_day_attendance(attendance_map, day):
    if isinstance(attendance_map, (set, frozenset)):
        return day in attendance_map
    if hasattr(attendance_map, 'get'):
        return bool(attendance_map.get(day))
    return False
