"""
Genera redes sintéticas con el mismo formato de los 3 CSV, del tamaño que se quiera.
Sirve para el panel de rendimiento (R11) y para probar con redes más grandes que la
real, como hará el profesor.

    python app/herramientas/generar_red.py 8000 red_8000

Con n estaciones se crean n/10 rutas de 8 a 16 paradas, y cada ruta pasa entre
40 y 120 veces al día. Así, al duplicar n se duplica toda la red (estaciones, rutas
y horarios), pero cada ruta sigue teniendo un tamaño parecido, como en la vida real.
"""

import csv
import os
import random
import sys

LETRAS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def nombres_unicos(n, rnd):
    vistos = set()
    res = []
    while len(res) < n:
        largo = rnd.randint(5, 10)
        nombre = "".join(rnd.choice(LETRAS) for _ in range(largo))
        if rnd.random() < 0.3:
            nombre = "CALLE " + str(rnd.randint(1, 250)) + " " + nombre[:3]
        if nombre not in vistos:
            vistos.add(nombre)
            res.append(nombre)
    return res


def generar(n, carpeta, semilla=0):
    rnd = random.Random(semilla)
    os.makedirs(carpeta, exist_ok=True)
    estaciones = nombres_unicos(n, rnd)
    n_rutas = max(2, n // 10)

    with open(os.path.join(carpeta, "estaciones.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["nombre"])
        for e in estaciones:
            w.writerow([e])

    rutas = []
    with open(os.path.join(carpeta, "rutas.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ruta", "orden", "estacion"])
        for i in range(n_rutas):
            nombre = "R%d" % i
            paradas = rnd.sample(estaciones, rnd.randint(8, 16))
            rutas.append((nombre, paradas))
            for orden, e in enumerate(paradas, start=1):
                w.writerow([nombre, orden, e])

    with open(os.path.join(carpeta, "horarios.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ruta", "estacion", "hora"])
        for nombre, paradas in rutas:
            salidas = rnd.randint(40, 120)
            inicio = 4 * 60 + rnd.randint(0, 60)
            paso = max(1, (23 * 60 - inicio) // salidas)
            for pos, e in enumerate(paradas):
                for s in range(salidas):
                    m = (inicio + s * paso + pos * 3) % 1440
                    w.writerow([nombre, e, "%02d:%02d" % (m // 60, m % 60)])
    return estaciones, rutas


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("uso: python app/herramientas/generar_red.py N CARPETA")
    generar(int(sys.argv[1]), sys.argv[2])
    print("Red de", sys.argv[1], "estaciones en", sys.argv[2])
