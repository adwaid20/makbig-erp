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
    """
    Returns attendance records for a given day from attendance_map
    """
    if attendance_map is None:
        return None
    return attendance_map.get(day)
