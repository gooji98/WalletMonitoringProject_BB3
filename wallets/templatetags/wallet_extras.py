from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter
def format_crypto(value, decimals=4):
    if value is None:
        return "-"

    try:
        number = Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        return value

    if number == 0:
        return "0"

    decimals = int(decimals)
    formatted = f"{number:.{decimals}f}"

    if "." in formatted:
        formatted = formatted.rstrip("0").rstrip(".")

    return formatted