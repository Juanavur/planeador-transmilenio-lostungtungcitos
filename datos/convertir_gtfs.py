"""
Conversión del GTFS de TransMilenio (julio 2021) a los tres CSV que lee el motor.

    python datos/convertir_gtfs.py RUTA_AL_ZIP_O_CARPETA  [--salida datos] [--todo] [--dia lunes]

Este script NO es parte del motor: aquí se puede usar cualquier librería (pandas).

Salida (por defecto, esta misma carpeta datos/):
    estaciones.csv  -> nombre
    rutas.csv       -> ruta, orden, estacion
    horarios.csv    -> ruta, estacion, hora

Decisiones (explicadas también en el README):
  1. Por defecto solo se toma el sistema TRONCAL (las estaciones de TransMilenio).
     Con --todo se agregan alimentadores, zonales (SITP), etc.
  2. Una estación troncal tiene varios "stops" en el GTFS (vagones / plataformas:
     "Calle 85 B - 4 ó 6", "Portal 80 T-1A"). Se agrupan en una sola estación
     quitando el sufijo de vagón. Así un transbordo dentro de la misma estación funciona.
  3. Nombres en MAYÚSCULAS, sin tildes, sin espacios dobles y sin repetidos.
  4. Solo se usan los viajes del día elegido (por defecto un día hábil, lunes),
     para que "buses al día" sea de verdad un día y no la suma de lunes+sábado+domingo.
  5. Cada route_id del GTFS ya va en un solo sentido (B74 va al norte, J74 al sur).
     El orden de paradas de la ruta sale del patrón de paradas más frecuente entre
     sus viajes (si empatan, el más largo). Si una estación se repite dentro del
     patrón, se deja solo la primera aparición.
  6. Horas: el GTFS usa horas como 25:10 para viajes que pasan de medianoche.
     Se convierten a la hora real del reloj (25:10 -> 01:10) y se trunca a minutos.
"""

import argparse
import os
import re
import sys
import tempfile
import unicodedata
import zipfile

import pandas as pd

DIAS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
DIAS_ES = {"lunes": "monday", "martes": "tuesday", "miercoles": "wednesday",
           "jueves": "thursday", "viernes": "friday", "sabado": "saturday", "domingo": "sunday"}


# ----------------------------------------------------------------------------- nombres
def normalizar(texto):
    """Mayúsculas, sin tildes (Ñ -> N), sin símbolos raros, espacios simples."""
    texto = str(texto).replace("º", "").replace("°", "")
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = texto.upper().replace(",", " ")
    return re.sub(r"\s+", " ", texto).strip()


def nombre_estacion_troncal(stop_name):
    """'Calle 85 B - 4 ó 6' -> 'CALLE 85';  'Portal 80 T-1A' -> 'PORTAL 80'."""
    n = normalizar(stop_name)
    n = re.sub(r"\s+[A-F]\s*-\s*[\d O]+$", "", n)        # vagón: " B - 4 O 6"
    n = re.sub(r"\s+T-?\d+\s*[A-Z]?$", "", n)            # plataforma de portal: " T-1A", " T2 A"
    return n.strip()


def nombre_parada_otra(stop_name, stop_code):
    """Paradas no troncales: '659A03_Costa Rica' -> 'COSTA RICA 659A03'.
    Se conserva el código para no fusionar paradas lejanas que se llaman igual."""
    base = str(stop_name)
    if "_" in base:
        base = base.split("_", 1)[1]
    return normalizar(base + " " + str(stop_code))


def hora_reloj(hhmmss):
    """'25:10:30' -> '01:10'."""
    partes = str(hhmmss).strip().split(":")
    h = int(partes[0]) % 24
    m = int(partes[1])
    return "%02d:%02d" % (h, m)


# ----------------------------------------------------------------------------- lectura
def abrir_gtfs(ruta):
    if os.path.isdir(ruta):
        return ruta, None
    tmp = tempfile.TemporaryDirectory()
    with zipfile.ZipFile(ruta) as z:
        z.extractall(tmp.name)
    # algunos zips traen una subcarpeta
    for raiz, _, archivos in os.walk(tmp.name):
        if "stop_times.txt" in archivos:
            return raiz, tmp
    sys.exit("No encontré stop_times.txt dentro de " + ruta)


def leer(carpeta, nombre, **kw):
    return pd.read_csv(os.path.join(carpeta, nombre), dtype=str, **kw)


def servicios_del_dia(carpeta, dia):
    cal = leer(carpeta, "calendar.txt")
    return set(cal.loc[cal[dia] == "1", "service_id"])


# ----------------------------------------------------------------------------- conversión
def convertir(origen, salida, todo=False, dia="monday"):
    carpeta, tmp = abrir_gtfs(origen)
    print("Leyendo GTFS de", carpeta)

    routes = leer(carpeta, "routes.txt")
    trips = leer(carpeta, "trips.txt")
    stops = leer(carpeta, "stops.txt")

    if not todo:
        routes = routes[routes["route_desc"].str.upper() == "TRONCAL"]
    servicios = servicios_del_dia(carpeta, dia)
    trips = trips[trips["route_id"].isin(routes["route_id"]) & trips["service_id"].isin(servicios)]
    print("Rutas:", len(routes), " viajes del día:", len(trips))

    # nombre de estación para cada stop_id
    # algunos vagones troncales vienen marcados con otro stop_desc: se reconocen por el nombre
    patron_vagon = r"\s[A-Fa-f]\s*-\s*[\d ÓOóo]+$"
    patron_portal = r"(?i)^portal .*\sT-?\d+\s*[A-Z]?$"
    es_troncal = (stops["stop_desc"].str.upper() == "TRONCAL") | \
        stops["stop_name"].str.contains(patron_vagon, regex=True, na=False) | \
        stops["stop_name"].str.contains(patron_portal, regex=True, na=False)
    stops["estacion"] = [
        nombre_estacion_troncal(n) if t else nombre_parada_otra(n, c)
        for n, c, t in zip(stops["stop_name"], stops["stop_code"], es_troncal)
    ]
    estacion_de = dict(zip(stops["stop_id"], stops["estacion"]))

    # nombre único y normalizado para cada ruta
    nombre_ruta = {}
    usados = set()
    for rid, corto, largo in zip(routes["route_id"], routes["route_short_name"], routes["route_long_name"]):
        base = normalizar(corto if isinstance(corto, str) and corto.strip() else largo)
        nombre = base if base not in usados else base + " " + normalizar(rid)
        usados.add(nombre)
        nombre_ruta[rid] = nombre
    ruta_de_viaje = dict(zip(trips["trip_id"], trips["route_id"].map(nombre_ruta)))

    # stop_times es grande (~300 MB): se lee por pedazos y solo con los viajes que sirven
    print("Leyendo stop_times.txt por pedazos...")
    pedazos = []
    for ch in pd.read_csv(os.path.join(carpeta, "stop_times.txt"), dtype=str,
                          usecols=["trip_id", "departure_time", "stop_id", "stop_sequence"],
                          chunksize=1_000_000):
        ch = ch[ch["trip_id"].isin(ruta_de_viaje.keys())]
        if len(ch):
            pedazos.append(ch)
    st = pd.concat(pedazos, ignore_index=True)
    st["stop_sequence"] = st["stop_sequence"].astype(int)
    st["estacion"] = st["stop_id"].map(estacion_de)
    st["ruta"] = st["trip_id"].map(ruta_de_viaje)
    st = st.dropna(subset=["estacion", "ruta"])
    st = st.sort_values(["trip_id", "stop_sequence"])
    # una estación cuenta una sola vez por viaje (dos vagones seguidos = misma estación)
    st = st.drop_duplicates(subset=["trip_id", "estacion"], keep="first")
    print("Pasadas útiles:", len(st))

    # patrón de paradas de cada viaje -> patrón representativo de cada ruta
    patrones = st.groupby("trip_id", sort=False)["estacion"].apply(tuple)
    por_ruta = {}
    for trip_id, patron in patrones.items():
        conteo = por_ruta.setdefault(ruta_de_viaje[trip_id], {})
        conteo[patron] = conteo.get(patron, 0) + 1

    filas_rutas = []
    estaciones_de_ruta = {}
    for ruta in sorted(por_ruta):
        conteo = por_ruta[ruta]
        patron = max(conteo, key=lambda p: (conteo[p], len(p)))
        if len(patron) < 2:
            continue
        estaciones_de_ruta[ruta] = set(patron)
        for i, est in enumerate(patron, start=1):
            filas_rutas.append((ruta, i, est))

    # horarios: solo de estaciones que están en el recorrido oficial de la ruta
    mascara = [e in estaciones_de_ruta.get(r, ()) for r, e in zip(st["ruta"], st["estacion"])]
    hor = st.loc[mascara, ["ruta", "estacion", "departure_time"]].copy()
    hor["hora"] = hor["departure_time"].map(hora_reloj)
    hor = hor.drop(columns="departure_time").sort_values(["ruta", "estacion", "hora"])

    estaciones = sorted({e for _, _, e in filas_rutas})

    os.makedirs(salida, exist_ok=True)
    pd.DataFrame({"nombre": estaciones}).to_csv(os.path.join(salida, "estaciones.csv"), index=False)
    pd.DataFrame(filas_rutas, columns=["ruta", "orden", "estacion"]).to_csv(
        os.path.join(salida, "rutas.csv"), index=False)
    hor.to_csv(os.path.join(salida, "horarios.csv"), index=False)

    print("Listo ->", salida)
    print("  estaciones:", len(estaciones))
    print("  rutas:", len(estaciones_de_ruta), " filas rutas.csv:", len(filas_rutas))
    print("  filas horarios.csv:", len(hor))
    if tmp is not None:
        tmp.cleanup()


def main():
    p = argparse.ArgumentParser(description="GTFS de TransMilenio -> 3 CSV del motor")
    p.add_argument("gtfs", help="zip del GTFS o carpeta descomprimida")
    p.add_argument("--salida", default=os.path.dirname(os.path.abspath(__file__)))
    p.add_argument("--todo", action="store_true", help="incluir alimentadores, zonales, etc.")
    p.add_argument("--dia", default="lunes", help="día de servicio: lunes ... domingo")
    a = p.parse_args()
    dia = DIAS_ES.get(normalizar(a.dia).lower(), a.dia.lower())
    if dia not in DIAS:
        sys.exit("Día no válido: " + a.dia)
    convertir(a.gtfs, a.salida, todo=a.todo, dia=dia)


if __name__ == "__main__":
    main()
