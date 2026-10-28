"""
Conversión de horas. Internamente las horas son minutos desde medianoche (0..1439),
que se comparan y ordenan como números.

Decisión sobre horas >= 24 (el GTFS trae cosas como 25:10): se pasan a la hora real
del reloj con módulo 24 (25:10 -> 01:10). La conversión ya lo hace, pero el motor
también lo aplica por si la red del profesor trae horas así.
"""

MINUTOS_DIA = 1440


def a_minutos(hora):
    """'HH:MM' (o 'H:MM' o 'HH:MM:SS') -> minutos desde medianoche. None si no es válida."""
    if not isinstance(hora, str):
        return None
    partes = hora.strip().split(":")
    if len(partes) < 2 or not partes[0].isdigit() or not partes[1].isdigit():
        return None
    h = int(partes[0])
    m = int(partes[1])
    if m > 59:
        return None
    return (h * 60 + m) % MINUTOS_DIA


def a_texto(minutos):
    return "%02d:%02d" % (minutos // 60, minutos % 60)
