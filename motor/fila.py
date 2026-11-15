"""
R10. Fila de abordaje en hora pico.

simular_fila(llegadas, frecuencia, capacidad)
    llegadas   : lista con el minuto (o segundo, la unidad da igual) en que llega cada pasajero
    frecuencia : cada cuánto sale un bus (los buses salen en 0, f, 2f, 3f, ...)
    capacidad  : cuántos pasajeros caben en cada bus
Devuelve una lista `esperas` del mismo tamaño que `llegadas`:
    esperas[i] = cuánto esperó el pasajero i desde que llegó hasta que subió.

Reglas:
  - Suben en orden de llegada (FIFO). Si dos llegan al mismo tiempo, primero el que
    aparece antes en la lista.
  - Quien llega justo cuando sale un bus alcanza a subir a ese bus.

Estructura: Cola con arreglo circular (encolar/desencolar O(1), ver motor/pila_cola.py).
Se descartó usar una lista con pop(0): cada pop(0) es O(P) y con cientos de miles de
pasajeros la simulación sería O(P^2).

Complejidad: O(P + B), P = pasajeros, B = buses que salen con alguien esperando
(cuando la fila está vacía se salta directo al bus de la siguiente llegada).
Si `llegadas` no viene ordenada, se ordena primero con merge sort: O(P log P).
"""

from .pila_cola import Cola
from .ordenar import esta_ordenado, merge_sort


def simular_fila(llegadas, frecuencia, capacidad):
    if frecuencia <= 0 or capacidad <= 0:
        raise ValueError("frecuencia y capacidad deben ser positivas")
    p = len(llegadas)
    esperas = [0] * p
    if p == 0:
        return esperas

    # orden de llegada (índices); casi siempre ya viene ordenada y no cuesta nada
    if esta_ordenado(llegadas, lambda a, b: a < b):
        orden = None
    else:
        orden = merge_sort(list(range(p)), lambda i, j: llegadas[i] < llegadas[j])

    cola = Cola()
    siguiente = 0          # próximo pasajero (en orden de llegada) que aún no está en la fila
    abordados = 0
    t = 0                  # hora de salida del bus actual
    while abordados < p:
        if cola.vacia():
            # nadie esperando: saltar al primer bus en o después de la próxima llegada
            a = llegadas[siguiente if orden is None else orden[siguiente]]
            q = a // frecuencia
            if q * frecuencia < a:
                q += 1
            if q * frecuencia > t:
                t = q * frecuencia
        while siguiente < p:
            idx = siguiente if orden is None else orden[siguiente]
            if llegadas[idx] > t:
                break
            cola.encolar(idx)
            siguiente += 1
        suben = 0
        while suben < capacidad and not cola.vacia():
            idx = cola.desencolar()
            esperas[idx] = t - llegadas[idx]
            suben += 1
        abordados += suben
        t += frecuencia
    return esperas
