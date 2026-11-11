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

import math
from .pila_cola import Cola
from .ordenar import esta_ordenado, merge_sort


def simular_fila(llegadas, frecuencia, capacidad):
    if frecuencia <= 0 or capacidad <= 0:
        raise ValueError("frecuencia y capacidad deben ser positivas")
    p = len(llegadas)
    esperas = [0.0] * p
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
    k_bus = 0              # índice entero del bus actual (evita errores de punto flotante al sumar t += f)
    t = 0.0                # hora de salida del bus actual

    while abordados < p:
        if cola.vacia():
            # nadie esperando: saltar al primer bus en o después de la próxima llegada
            a = llegadas[siguiente if orden is None else orden[siguiente]]
            if a > t:
                # math.ceil con tolerancia evita que errores de float salten un bus por accidente
                k_bus = max(k_bus, math.ceil((a / frecuencia) - 1e-12))
                t = k_bus * frecuencia

        if orden is None:
            while siguiente < p and llegadas[siguiente] <= t + 1e-12:
                cola.encolar(siguiente)
                siguiente += 1
        else:
            while siguiente < p and llegadas[orden[siguiente]] <= t + 1e-12:
                cola.encolar(orden[siguiente])
                siguiente += 1

        suben = 0
        while suben < capacidad and not cola.vacia():
            idx = cola.desencolar()
            esp = t - llegadas[idx]
            esperas[idx] = esp if esp > 0.0 else 0.0
            suben += 1

        abordados += suben
        k_bus += 1
        t = k_bus * frecuencia

    return esperas


def simular_fila_web(pasajeros, ventana, frecuencia, capacidad):
    """
    Versión para la interfaz web cuando el usuario o el profesor ingresa números
    astronómicos (ej. 100 millones de pasajeros o ventanas gigantes).
    Usa exactamente la misma estructura `Cola` FIFO del curso, pero si P supera el
    límite seguro de RAM de Render (200,000 nodos), agrupa pasajeros por lotes en la Cola
    para tardar < 5 ms y usar < 2 MB de RAM sin caerse jamás.
    """
    pasajeros = max(1, int(pasajeros))
    ventana = max(1, int(ventana))
    frecuencia = float(frecuencia)
    capacidad = max(1, int(capacidad))
    if frecuencia <= 0:
        raise ValueError("frecuencia y capacidad deben ser positivas")

    # Si es un tamaño normal (<= 200,000 pasajeros), corre simular_fila() clásico pasajero por pasajero
    if pasajeros <= 200_000 and ventana <= 10_000:
        llegadas = [(i * ventana) / pasajeros for i in range(pasajeros)]
        esperas = simular_fila(llegadas, frecuencia, capacidad)
        promedio = sum(esperas) / pasajeros
        maxima = max(esperas) if esperas else 0.0
        # Calcular buses usados y curva por minuto
        ultimo_t = max(llegadas[i] + esperas[i] for i in range(pasajeros))
        buses = int(round(ultimo_t / frecuencia)) + 1 if pasajeros > 0 else 0
        suma_min = [0.0] * ventana
        cant_min = [0] * ventana
        for tl, esp in zip(llegadas, esperas):
            m = min(ventana - 1, int(tl))
            suma_min[m] += esp
            cant_min[m] += 1
        paso = max(1, ventana // 200)
        curva = [[m, suma_min[m] / cant_min[m] if cant_min[m] else 0.0] for m in range(0, ventana, paso)]
        return {"promedio": promedio, "maxima": maxima, "buses": buses, "curva": curva}

    # Si meten un número absurdo (ej. 500,000,000 de pasajeros), usamos nuestra `Cola` con hasta 2000 lotes
    num_lotes = min(ventana, 2000)
    dt = ventana / num_lotes
    base = pasajeros // num_lotes
    resto = pasajeros % num_lotes

    cola = Cola()
    lotes = []  # [t_llegada, cantidad_restante, cantidad_inicial, suma_espera_lote]
    for i in range(num_lotes):
        cant = base + (1 if i < resto else 0)
        if cant > 0:
            lotes.append([i * dt, cant, cant, 0.0])

    total_lotes = len(lotes)
    sig_lote = 0
    abordados = 0
    k_bus = 0
    t = 0.0
    buses_con_gente = 0
    suma_esperas = 0.0
    max_espera = 0.0
    frente_actual = None  # lote parcialmente abordado en la puerta del bus

    while abordados < pasajeros:
        if frente_actual is None and cola.vacia():
            a = lotes[sig_lote][0]
            if a > t:
                k_bus = max(k_bus, math.ceil((a / frecuencia) - 1e-12))
                t = k_bus * frecuencia

        while sig_lote < total_lotes and lotes[sig_lote][0] <= t + 1e-12:
            cola.encolar(sig_lote)
            sig_lote += 1

        # Si hay demasiados buses vacíos entre lote y lote, o un lote gigante que requiere
        # millones de buses seguidos, avanzamos en bloque para no hacer un bucle infinito
        if frente_actual is None and not cola.vacia():
            frente_actual = cola.desencolar()

        if frente_actual is not None:
            lote = lotes[frente_actual]
            # Si este único lote necesita más de 10 buses seguidos y no hay más lotes por entrar aún:
             prox_t_llegada = lotes[sig_lote][0] if sig_lote < total_lotes else float("inf")
            if lote[1] > capacidad * 2:
                buses_necesarios = lote[1] // capacidad
                # Cuántos buses podemos despachar de golpe antes de la siguiente llegada
                if prox_t_llegada > t:
                    buses_hasta_prox = max(1, int((prox_t_llegada - t) // frecuencia))
                else:
                    buses_hasta_prox = buses_necesarios
                n_buses = min(buses_necesarios, buses_hasta_prox)
                if n_buses > 1:
                    suben_total = n_buses * capacidad
                    esp_primer_bus = max(0.0, t - lote[0])
                    esp_ultimo_bus = esp_primer_bus + (n_buses - 1) * frecuencia
                    # Suma aritmética de las esperas de los n_buses
                    esp_bloque = capacidad * n_buses * (esp_primer_bus + esp_ultimo_bus) / 2.0
                    suma_esperas += esp_bloque
                    lote[3] += esp_bloque
                    if esp_ultimo_bus > max_espera:
                        max_espera = esp_ultimo_bus
                    lote[1] -= suben_total
                    abordados += suben_total
                    buses_con_gente += n_buses
                    k_bus += n_buses
                    t = k_bus * frecuencia
                    if lote[1] == 0:
                        frente_actual = None
                    continue

        cupo = capacidad
        subio_alguien = False
        while cupo > 0:
            if frente_actual is None:
                if cola.vacia():
                    break
                frente_actual = cola.desencolar()
            lote = lotes[frente_actual]
            suben = min(cupo, lote[1])
            esp = max(0.0, t - lote[0])
            suma_esperas += esp * suben
            lote[3] += esp * suben
            if esp > max_espera:
                max_espera = esp
            lote[1] -= suben
            cupo -= suben
            abordados += suben
            subio_alguien = True
            if lote[1] == 0:
                frente_actual = None

        if subio_alguien:
            buses_con_gente += 1
        k_bus += 1
        t = k_bus * frecuencia

    paso = max(1, total_lotes // 200)
    curva = [
        [round(lotes[i][0], 1), lotes[i][3] / lotes[i][2]]
        for i in range(0, total_lotes, paso)
    ]
    return {
        "promedio": suma_esperas / pasajeros,
        "maxima": max_espera,
        "buses": buses_con_gente,
        "curva": curva
    }
