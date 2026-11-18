"""
Mide el motor en redes de varios tamaños y calcula la pendiente log-log de cada
operación (0 = constante, 1 = lineal), como describe la rúbrica del proyecto.

Pensado para guardarse en app/herramientas/ y correrse desde la raíz del repo:

    python app/herramientas/pendientes.py 10000 20000 40000 80000

Diferencias con medir.py: usa la MEDIANA de llamadas individuales (no el promedio),
cronometra cada operación por separado y calcula la pendiente al final.
Con los cuatro tamaños completos tarda varios minutos y puede usar alrededor de 1 GB.
"""

import gc
import math
import os
import random
import shutil
import statistics
import sys
import tempfile
import time

_AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_AQUI, "..", ".."))   # raíz del repo (motor)
sys.path.insert(0, os.path.join(_AQUI, ".."))         # app/ (herramientas)

from motor import Red, simular_fila          # noqa: E402
from herramientas.generar_red import generar  # noqa: E402

pc = time.perf_counter_ns

# Qué pendiente se espera de cada fila (según el README).
DEBE_SER = {
    "carga (s)": "~1 (n log n)",
    "R1 estado": "~0 (O(1))",
    "R2 autocompletar k=10, prefijo 1 letra": "~0 (O(log n + k))",
    "R2 autocompletar k=10, prefijo 3 letras": "~0 (O(log n + k))",
    "R3 rango (~11 estaciones)": "~0 (O(log n + m))",
    "R4 proximo_bus": "~0 (O(log h))",
    "R5 viaje (no se mide en el bono)": "no aplica",
    "R6 ranking k=10 (sin cambios)": "~0 (O(k))",
    "R6 ranking k=10 con 200 cerradas en la cima": "~0 (O(k + c))",
    "R6 ranking k=10 justo despues de editar una ruta": "~1 (O(n log n), reconstruye)",
    "R7 agregar_parada": "~0 (O(1))",
    "R7 quitar_parada": "~0 (O(1))",
    "R7 recorrido": "~0 (O(m))",
    "R8 cerrar": "~0 (O(1))",
    "R8 reabrir": "~0 (O(1))",
    "R9 deshacer (historial largo)": "~0 (O(1))",
    "R9 rehacer (historial largo)": "~0 (O(1))",
    "R10 simular_fila P=10n, llegadas ordenadas (us)": "~1 (O(P))",
    "R10 simular_fila P=10n, llegadas desordenadas (us)": "~1 (O(P log P))",
}


def mediana_us(f, reps):
    out = []
    for i in range(reps):
        t0 = pc()
        f(i)
        out.append(pc() - t0)
    return statistics.median(out) / 1000.0


def medir_tamano(n, semilla=1):
    rnd = random.Random(semilla)
    carpeta = tempfile.mkdtemp(prefix="pend_%d_" % n)
    estaciones, rutas = generar(n, carpeta, 0)
    res = {}
    cargas = []
    for intento in range(3):
        gc.collect()
        t0 = time.perf_counter()
        red = Red(carpeta)
        cargas.append(time.perf_counter() - t0)
        if intento < 2:
            del red
    res["carga (s)"] = statistics.median(cargas)
    shutil.rmtree(carpeta)

    V = 2000
    nombres = [rnd.choice(estaciones) for _ in range(V)]
    ordenadas = sorted(estaciones)
    gc.collect()

    res["R1 estado"] = mediana_us(lambda i: red.estado(nombres[i]), V)
    p1 = [nombres[i][:1] for i in range(V)]
    res["R2 autocompletar k=10, prefijo 1 letra"] = mediana_us(lambda i: red.autocompletar(p1[i], 10), V)
    p3 = [nombres[i][:3] for i in range(V)]
    res["R2 autocompletar k=10, prefijo 3 letras"] = mediana_us(lambda i: red.autocompletar(p3[i], 10), V)
    pares = []
    for _ in range(V):
        j = rnd.randrange(len(ordenadas) - 11)
        pares.append((ordenadas[j], ordenadas[j + 10]))
    res["R3 rango (~11 estaciones)"] = mediana_us(lambda i: red.rango(*pares[i]), V)

    cons = []
    for _ in range(V):
        ruta, paradas = rnd.choice(rutas)
        cons.append((rnd.choice(paradas), ruta, "%02d:%02d" % (rnd.randint(4, 22), rnd.randint(0, 59))))
    res["R4 proximo_bus"] = mediana_us(lambda i: red.proximo_bus(*cons[i]), V)

    viajes = [(rnd.choice(estaciones), rnd.choice(estaciones)) for _ in range(150)]
    res["R5 viaje (no se mide en el bono)"] = mediana_us(lambda i: red.viaje(*viajes[i]), 150)

    red.ranking(10)
    res["R6 ranking k=10 (sin cambios)"] = mediana_us(lambda i: red.ranking(10), V)
    top = [t[0] for t in red.ranking(200)]
    for nom in top:
        red.cerrar(nom)
    res["R6 ranking k=10 con 200 cerradas en la cima"] = mediana_us(lambda i: red.ranking(10), 300)
    for nom in top:
        red.reabrir(nom)

    pool = list(estaciones)
    rnd.shuffle(pool)
    distintas = pool[:1000]
    res["R8 cerrar"] = mediana_us(lambda i: red.cerrar(distintas[i]), 1000)
    res["R8 reabrir"] = mediana_us(lambda i: red.reabrir(distintas[i]), 1000)
    res["R9 deshacer (historial largo)"] = mediana_us(lambda i: red.deshacer(), 1000)
    res["R9 rehacer (historial largo)"] = mediana_us(lambda i: red.rehacer(), 1000)

    ed = []
    for i in range(500):
        ruta, paradas = rnd.choice(rutas)
        ed.append((ruta, "NUEVA%d" % i, rnd.choice(paradas)))
    res["R7 agregar_parada"] = mediana_us(lambda i: red.agregar_parada(*ed[i]), 500)
    res["R7 recorrido"] = mediana_us(lambda i: red.recorrido(ed[i][0]), 500)
    res["R7 quitar_parada"] = mediana_us(lambda i: red.quitar_parada(ed[i][0], ed[i][1]), 500)

    tiempos = []
    for i in range(5):
        ruta, paradas = rnd.choice(rutas)
        red.agregar_parada(ruta, "X%d" % i, paradas[0])     # deja el ranking "sucio"
        t0 = pc()
        red.ranking(10)
        tiempos.append(pc() - t0)
    res["R6 ranking k=10 justo despues de editar una ruta"] = statistics.median(tiempos) / 1000.0

    P = 10 * n
    ordenadas_ll = sorted(rnd.randint(0, 7200) for _ in range(P))
    desordenadas = list(ordenadas_ll)
    rnd.shuffle(desordenadas)
    res["R10 simular_fila P=10n, llegadas ordenadas (us)"] = mediana_us(lambda i: simular_fila(ordenadas_ll, 120, 160), 3)
    res["R10 simular_fila P=10n, llegadas desordenadas (us)"] = mediana_us(lambda i: simular_fila(desordenadas, 120, 160), 3)
    return res


def pendiente(xs, ys):
    lx = [math.log(x) for x in xs]
    ly = [math.log(y) for y in ys]
    mx, my = sum(lx) / len(lx), sum(ly) / len(ly)
    return sum((a - mx) * (b - my) for a, b in zip(lx, ly)) / sum((a - mx) ** 2 for a in lx)


def main(tamanos):
    datos = []
    for n in tamanos:
        print("midiendo n =", n, "...", flush=True)
        datos.append(medir_tamano(n))
        gc.collect()
    cab = "%-52s" % "operacion (us, salvo carga en s)" + "".join("%11d" % n for n in tamanos)
    print("\n" + cab + "   pendiente   debe ser")
    for op in datos[0]:
        ys = [d[op] for d in datos]
        print("%-52s" % op + "".join("%11.2f" % y for y in ys) +
              "     %+.2f     %s" % (pendiente(tamanos, ys), DEBE_SER.get(op, "")))


if __name__ == "__main__":
    main([int(x) for x in sys.argv[1:]] or [10000, 20000, 40000, 80000])
