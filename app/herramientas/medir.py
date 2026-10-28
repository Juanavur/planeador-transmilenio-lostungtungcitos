"""
Mide cuánto tarda cada operación del motor con redes de tamaño n, 2n, 4n, ...
Lo usa el panel de rendimiento (R11) y también se puede correr solo:

    python app/herramientas/medir.py 1000 2000 4000 8000

Para cada operación se hacen muchas llamadas con entradas al azar y se reporta el
promedio por llamada en microsegundos. (Una sola llamada O(1) dura menos de lo que
el reloj alcanza a medir bien, por eso se promedian cientos.)
"""

import os
import random
import sys
import tempfile
import time

_AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_AQUI, "..", ".."))     # raíz del repo (para importar motor)
sys.path.insert(0, os.path.join(_AQUI, ".."))           # app/ (para importar herramientas)

from motor import Red, simular_fila          # noqa: E402
from herramientas.generar_red import generar  # noqa: E402

# Complejidad esperada de cada operación, como función de n (estaciones).
# k = 10 fijo, h (pasadas por ruta y estación) y m (paradas por ruta) no crecen con n
# en las redes generadas, por eso varias quedan constantes.
ESPERADA = {
    "carga Red(carpeta)": ("O(n log n)", lambda n: n * _log2(n)),
    "R1 estado": ("O(1)", lambda n: 1),
    "R2 autocompletar (k=10)": ("O(log n + k)", lambda n: _log2(n) + 10),
    "R3 rango (~10 estaciones)": ("O(log n + m)", lambda n: _log2(n) + 10),
    "R4 proximo_bus": ("O(log h)", lambda n: 1),
    "R5 viaje (no se califica)": ("O(L)", lambda n: 1),
    "R6 ranking (k=10)": ("O(k)", lambda n: 1),
    "R7 agregar + quitar parada": ("O(1)", lambda n: 1),
    "R8 cerrar + reabrir": ("O(1)", lambda n: 1),
    "R9 deshacer + rehacer": ("O(1)", lambda n: 1),
    "R10 simular_fila (50n pasajeros)": ("O(P)", lambda n: n),
}


def _log2(n):
    c = 0
    while n > 1:
        n //= 2
        c += 1
    return max(c, 1)


def _cronometrar(funcion, veces, rondas=3):
    """Promedio por llamada en microsegundos; se toma la mejor de varias rondas
    (la menos afectada por otros programas del computador)."""
    mejor = None
    for _ in range(rondas):
        inicio = time.perf_counter()
        for i in range(veces):
            funcion(i)
        t = (time.perf_counter() - inicio) / veces * 1e6
        if mejor is None or t < mejor:
            mejor = t
    return mejor


def medir_tamano(n, veces=2000, semilla=0):
    rnd = random.Random(semilla)
    carpeta = tempfile.mkdtemp(prefix="red_%d_" % n)
    estaciones, rutas = generar(n, carpeta, semilla)
    ordenadas = sorted(estaciones)
    res = {}

    t0 = time.perf_counter()
    red = Red(carpeta)
    res["carga Red(carpeta)"] = (time.perf_counter() - t0) * 1e6

    nombres = [rnd.choice(estaciones) for _ in range(veces)]
    res["R1 estado"] = _cronometrar(lambda i: red.estado(nombres[i]), veces)

    # prefijo de 1 letra: siempre hay más de k coincidencias, así se mide justo O(log n + k)
    prefijos = [nombres[i][:1] for i in range(veces)]
    res["R2 autocompletar (k=10)"] = _cronometrar(lambda i: red.autocompletar(prefijos[i], 10), veces)

    pares = []
    for _ in range(veces):
        j = rnd.randrange(len(ordenadas) - 11)
        pares.append((ordenadas[j], ordenadas[j + 10]))
    res["R3 rango (~10 estaciones)"] = _cronometrar(lambda i: red.rango(pares[i][0], pares[i][1]), veces)

    consultas = []
    for _ in range(veces):
        ruta, paradas = rnd.choice(rutas)
        consultas.append((rnd.choice(paradas), ruta, "%02d:%02d" % (rnd.randint(4, 22), rnd.randint(0, 59))))
    res["R4 proximo_bus"] = _cronometrar(lambda i: red.proximo_bus(*consultas[i]), veces)

    viajes = [(rnd.choice(estaciones), rnd.choice(estaciones)) for _ in range(veces // 4)]
    res["R5 viaje (no se califica)"] = _cronometrar(lambda i: red.viaje(*viajes[i]), veces // 4)

    red.ranking(10)                                  # construye el cache una vez
    res["R6 ranking (k=10)"] = _cronometrar(lambda i: red.ranking(10), veces)

    ediciones = []
    for i in range(veces):
        ruta, paradas = rnd.choice(rutas)
        ediciones.append((ruta, "NUEVA%d" % i, rnd.choice(paradas)))

    def editar(i):
        ruta, nueva, despues = ediciones[i]
        red.agregar_parada(ruta, nueva, despues)
        red.quitar_parada(ruta, nueva)
    res["R7 agregar + quitar parada"] = _cronometrar(editar, veces)

    def cerrar_reabrir(i):
        red.cerrar(nombres[i])
        red.reabrir(nombres[i])
    res["R8 cerrar + reabrir"] = _cronometrar(cerrar_reabrir, veces)

    def deshacer_rehacer(i):
        red.deshacer()
        red.rehacer()
    res["R9 deshacer + rehacer"] = _cronometrar(deshacer_rehacer, veces)

    llegadas = sorted(rnd.randint(0, 7200) for _ in range(50 * n))
    res["R10 simular_fila (50n pasajeros)"] = _cronometrar(lambda i: simular_fila(llegadas, 120, 160), 1)
    return res


def medir(tamanos, veces=2000, avisar=None):
    """Devuelve filas (operacion, n, microsegundos, esperado_escalado, complejidad)."""
    crudo = []
    for n in tamanos:
        if avisar:
            avisar(n)
        crudo.append((n, medir_tamano(n, veces)))
    filas = []
    # la curva teórica se ancla en el punto más grande (ahí el tiempo ya es estable:
    # en los tamaños pequeños influyen el calentamiento y la caché)
    n0, base = crudo[len(crudo) - 1]
    for op, (texto, f) in ESPERADA.items():
        for n, res in crudo:
            esperado = base[op] * f(n) / f(n0)
            filas.append((op, n, res[op], esperado, texto))
    return filas


if __name__ == "__main__":
    tamanos = [int(x) for x in sys.argv[1:]] or [1000, 2000, 4000, 8000]
    filas = medir(tamanos, avisar=lambda n: print("midiendo n =", n, "...", flush=True))
    actual = None
    for op, n, us, esp, texto in filas:
        if op != actual:
            print("\n%s   esperado %s" % (op, texto))
            actual = op
        print("   n=%7d   %12.2f us   (esperado ~%.2f)" % (n, us, esp))
