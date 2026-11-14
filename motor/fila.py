"""
R10. Fila de abordaje en hora pico.

simular_fila(llegadas, frecuencia, capacidad)
    llegadas   : lista con el segundo en que llega cada pasajero
    frecuencia : cada cuánto sale un bus (los buses salen en f, 2f, 3f, ...)
    capacidad  : cuántos pasajeros caben en cada bus
Devuelve una lista `salidas` del mismo tamaño que `llegadas`:
    salidas[i] = segundo en que salió el bus al que subió el pasajero i.

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
    salidas = [0] * p
    if p == 0:
        return salidas

    # orden de llegada (índices); si ya viene ordenada no cuesta O(P log P)
    if esta_ordenado(llegadas, lambda a, b: a < b):
        orden = None
    else:
        orden = merge_sort(list(range(p)), lambda i, j: llegadas[i] < llegadas[j])

    cola = Cola()
    siguiente = 0          # próximo pasajero (en orden de llegada) que aún no está en la fila
    abordados = 0
    t = frecuencia         # los buses salen en frecuencia, 2*frecuencia, ...
    while abordados < p:
        if cola.vacia():
            # nadie esperando: saltar al primer bus (>= frecuencia) en o después de la próxima llegada
            a = llegadas[siguiente if orden is None else orden[siguiente]]
            q = int(a // frecuencia)
            if q * frecuencia < a - 1e-12:
                q += 1
            if q < 1:
                q = 1
            if q * frecuencia > t:
                t = q * frecuencia
        while siguiente < p:
            idx = siguiente if orden is None else orden[siguiente]
            if llegadas[idx] > t + 1e-12:
                break
            cola.encolar(idx)
            siguiente += 1
        suben = 0
        while suben < capacidad and not cola.vacia():
            idx = cola.desencolar()
            salidas[idx] = t
            suben += 1
        abordados += suben
        t += frecuencia
    return salidas
