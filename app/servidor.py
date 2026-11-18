"""
App del planeador (front web). Solo usa la librería estándar de Python: no hay que instalar nada.

    python app/servidor.py

Abre el navegador en http://localhost:8501. Para cerrarla: Ctrl + C.

Este archivo solo traduce peticiones del navegador a llamadas del motor y devuelve JSON.
Ninguna regla del sistema vive aquí: todo lo decide motor/.
"""

import json
import os
import random
import sys
import threading
import unicodedata
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.join(AQUI, "..")
sys.path.insert(0, RAIZ)
sys.path.insert(0, AQUI)

from motor import Red, simular_fila          # noqa: E402
from herramientas.medir import medir          # noqa: E402

CARPETA_DATOS = sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, "datos")
CANDADO = threading.Lock()                    # una petición a la vez toca la red
RED = Red(CARPETA_DATOS)

EXPLICACION = {
    "carga Red(carpeta)": "Leer los CSV es lineal; insertar las n estaciones en el AVL cuesta log n cada una.",
    "R1 estado": "Tabla hash: no depende de n. Si sube un poco con redes grandes es por la memoria caché "
                 "del procesador (más datos, más fallos de caché), no por el algoritmo.",
    "R2 autocompletar (k=10)": "Bajar por el AVL (log n) y recorrer k nombres. Casi plano.",
    "R3 rango (~10 estaciones)": "Igual que R2 pero hasta un nombre final. Con ~10 resultados queda casi plano; "
                                 "si el rango fuera fijo en nombres, m crecería con n.",
    "R4 proximo_bus": "Búsqueda binaria sobre las horas de UNA ruta en UNA estación (h). h no crece al duplicar la red.",
    "R5 viaje (no se califica)": "Depende del largo de las rutas que tocan origen y destino, no de n.",
    "R6 ranking (k=10)": "El arreglo ordenado está guardado; se leen k resultados y se saltan las estaciones cerradas.",
    "R6 ranking (reconstruccion tras editar)": "La primera consulta tras editar una ruta reconstruye el ranking con merge sort: O(n log n).",
    "R7 agregar + quitar parada": "Lista doble + tabla de nodos: se cambian punteros, nada más.",
    "R8 cerrar + reabrir": "Cambiar una bandera después de una consulta a la tabla hash.",
    "R9 deshacer + rehacer": "Sacar y meter en una pila de nodos.",
    "R10 simular_fila (P=10n, salidas en segundos)": "Con llegadas ordenadas, cada pasajero entra y sale una vez; el resultado es el segundo de salida asignado.",
    "R10 simular_fila (P=10n, llegadas desordenadas)": "Incluye merge sort O(P log P); la asignación FIFO es O(P + B).",
}


def limpiar(texto):
    """Lo que escribe la persona -> formato de los datos (MAYÚSCULAS, sin tildes).
    Es comodidad de la interfaz, no una regla del sistema."""
    texto = unicodedata.normalize("NFD", texto or "")
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return " ".join(texto.upper().split())


def todas():
    return RED.rango("", "￿")


# ------------------------------------------------------------------ cada endpoint llama al motor
def api_info(q):
    return {"estaciones": RED.num_estaciones(), "rutas": RED.nombres_rutas(), "abiertas": todas()}


def api_estado(q):
    nombre = limpiar(q.get("nombre", ""))
    estado = RED.estado(nombre)                                                # R1
    if isinstance(estado, tuple):
        existe, abierta = estado
    else:
        existe = estado != "NO EXISTE"
        abierta = estado == "ABIERTA"
    return {"nombre": nombre, "existe": existe, "abierta": abierta,
            "rutas": RED.rutas_de(nombre) if existe else [],
            "buses": RED.buses_al_dia(nombre)}


def api_autocompletar(q):
    return RED.autocompletar(limpiar(q.get("prefijo", "")), int(q.get("k", 8)))  # R2


def api_rango(q):
    return RED.rango(limpiar(q.get("desde", "")), limpiar(q.get("hasta", "")))     # R3


def api_rutas_de(q):
    return RED.rutas_de(q.get("estacion", ""))


def api_proximo_bus(q):
    return RED.proximo_bus(q.get("estacion", ""), q.get("ruta", ""), q.get("hora", ""))  # R4


def api_viaje(q):
    plan = RED.viaje(q.get("origen", ""), q.get("destino", ""))                # R5
    if plan is None or len(plan) == 0:
        return plan
    vista = []
    for tramo in plan:
        if len(tramo) == 4:
            vista.append(tramo)
        else:
            ruta, sube, baja = tramo
            recorrido = RED.recorrido(ruta)
            vista.append((ruta, sube, baja, recorrido.index(baja) - recorrido.index(sube)))
    return vista


def api_ranking(q):
    top = RED.ranking(int(q.get("k", 10)))                                     # R6
    res = []
    for item in top:
        if isinstance(item, str):
            res.append({"nombre": item, "buses": RED.buses_al_dia(item)})
        else:
            nombre, buses = item
            res.append({"nombre": nombre, "buses": buses})
    return res


def api_recorrido(q):
    ruta = q.get("ruta", "")
    return {"ida": RED.recorrido(ruta), "al_reves": RED.recorrido(ruta, al_reves=True)}  # R7


def api_agregar_parada(q):
    despues = q.get("despues_de", "")
    return RED.agregar_parada(q.get("ruta", ""), limpiar(q.get("nueva", "")), despues or None)  # R7


def api_quitar_parada(q):
    return RED.quitar_parada(q.get("ruta", ""), q.get("estacion", ""))            # R7


def api_cerrar(q):
    return RED.cerrar(limpiar(q.get("nombre", "")))                                # R8


def api_reabrir(q):
    return RED.reabrir(limpiar(q.get("nombre", "")))                               # R8


def api_deshacer(q):
    return RED.deshacer()                                                          # R9


def api_rehacer(q):
    return RED.rehacer()                                                           # R9


# Límites de R10: el motor simula persona por persona, así que sin tope un valor enorme
# (por ejemplo 100 billones) llena la memoria y, como la petición tiene el CANDADO, congela toda la app.
MAX_PASAJEROS = 300_000
MAX_VENTANA_MIN = 1440
MIN_FRECUENCIA_MIN, MAX_FRECUENCIA_MIN = 0.05, 60
MAX_CAPACIDAD = 2000


def _numero(q, nombre, defecto, minimo, maximo, etiqueta):
    try:
        v = float(q.get(nombre, defecto))
    except (TypeError, ValueError):
        raise ValueError("%s debe ser un número" % etiqueta)
    if v != v or v < minimo or v > maximo:        # v != v detecta NaN
        raise ValueError("%s debe estar entre %s y %s" % (etiqueta, f"{minimo:,}".replace(",", " "), f"{maximo:,}".replace(",", " ")))
    return v


def api_fila(q):
    # Se valida ANTES de generar nada. La página manda minutos; el motor trabaja en segundos.
    pasajeros = int(_numero(q, "pasajeros", 100000, 1, MAX_PASAJEROS, "Personas que llegan"))
    ventana = int(_numero(q, "ventana", 120, 1, MAX_VENTANA_MIN, "Llegan durante (min)") * 60)
    frecuencia = _numero(q, "frecuencia", 0.25, MIN_FRECUENCIA_MIN, MAX_FRECUENCIA_MIN, "Un bus cada (min)") * 60
    capacidad = int(_numero(q, "capacidad", 250, 1, MAX_CAPACIDAD, "Cupo por bus"))
    rnd = random.Random(0)
    # Llegadas enteras en segundos, con un pico a la mitad de la ventana.
    llegadas = sorted(int(rnd.triangular(0, ventana, ventana / 2)) for _ in range(pasajeros))
    salidas = simular_fila(llegadas, frecuencia, capacidad)                        # R10
    # Una sola pasada, con listas por minuto (más rápido que diccionarios).
    n_min = ventana // 60 + 1
    suma, cuenta = [0] * n_min, [0] * n_min
    espera_total, espera_max = 0, 0
    for llegada, salida in zip(llegadas, salidas):
        espera = salida - llegada                      # segundos que esperó esta persona
        espera_total += espera
        if espera > espera_max:
            espera_max = espera
        m = llegada // 60
        suma[m] += espera
        cuenta[m] += 1
    return {"promedio": espera_total / len(salidas) / 60, "maxima": espera_max / 60,   # minutos
            "buses": len(set(salidas)),
            "curva": [[m, suma[m] / cuenta[m] / 60] for m in range(n_min) if cuenta[m]]}


def api_medir(q):
    tamanos = sorted(int(x) for x in q.get("tamanos", "10000,20000,40000,80000").split(",") if x.strip())
    filas = medir(tamanos, veces=250)                                              # R11
    res = {}
    for op, n, us, esp, texto in filas:
        res.setdefault(op, {"complejidad": texto, "explicacion": EXPLICACION.get(op, ""), "puntos": []})
        res[op]["puntos"].append([n, us, esp])
    return [{"operacion": op, **v} for op, v in res.items()]


# ------------------------------------------------------------------ tabla de datos
def api_tabla_estaciones(q):
    filas = []
    for nombre, abierta, n_rutas, buses in RED.todas_las_estaciones():
        filas.append({"estacion": nombre, "estado": "Abierta" if abierta else "Cerrada",
                      "rutas": n_rutas, "buses_al_dia": buses})
    return filas


def api_tabla_rutas(q):
    filas = []
    for ruta in RED.nombres_rutas():
        paradas = RED.recorrido(ruta)
        pasadas = sum(len(RED.horarios(ruta, e)) for e in paradas)
        filas.append({"ruta": ruta, "paradas": len(paradas),
                      "desde": paradas[0] if paradas else "", "hasta": paradas[-1] if paradas else "",
                      "pasadas_al_dia": pasadas, "recorrido": " → ".join(paradas)})
    return filas


def _minutos(h):
    a, b = h.split(":")
    return int(a) * 60 + int(b)


def api_tabla_horarios(q):
    """Para una ruta: cada parada con su primer bus, último bus, cuántos pasan y cada cuánto."""
    ruta = q.get("ruta", "")
    filas = []
    for orden, est in enumerate(RED.recorrido(ruta) or [], start=1):
        horas = RED.horarios(ruta, est)
        if len(horas) > 1:
            m = [_minutos(h) for h in horas]
            cada = (m[-1] - m[0]) / (len(m) - 1)
        else:
            cada = None
        filas.append({"orden": orden, "estacion": est, "primer_bus": horas[0] if horas else "",
                      "ultimo_bus": horas[-1] if horas else "", "pasadas": len(horas),
                      "cada_min": round(cada, 1) if cada is not None else "", "horas": horas})
    return filas


# ------------------------------------------------------------------ mapa
def _coordenadas():
    import csv
    ruta = os.path.join(CARPETA_DATOS, "coordenadas.csv")
    res = {}
    if os.path.exists(ruta):
        with open(ruta, encoding="utf-8") as f:
            for fila in csv.DictReader(f):
                res[fila["estacion"]] = (float(fila["lat"]), float(fila["lon"]))
    return res


COORDENADAS = _coordenadas()


def api_mapa(q):
    """Estaciones con su posición real y el recorrido de cada ruta, para dibujar el mapa."""
    estaciones = []
    for nombre, abierta, n_rutas, buses in RED.todas_las_estaciones():
        if nombre in COORDENADAS:
            lat, lon = COORDENADAS[nombre]
            estaciones.append({"nombre": nombre, "lat": lat, "lon": lon, "abierta": abierta,
                               "buses": buses, "rutas": RED.rutas_de(nombre)})
    rutas = [{"ruta": r, "paradas": RED.recorrido(r)} for r in RED.nombres_rutas()]
    return {"estaciones": estaciones, "rutas": rutas}


RUTAS = {name[4:]: f for name, f in list(globals().items()) if name.startswith("api_")}


class Manejador(BaseHTTPRequestHandler):
    def _enviar(self, codigo, cuerpo, tipo):
        datos = cuerpo.encode("utf-8") if isinstance(cuerpo, str) else cuerpo
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(datos)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(datos)

    def do_GET(self):
        url = urlparse(self.path)
        if url.path in ("/", "/index.html"):
            with open(os.path.join(AQUI, "index.html"), encoding="utf-8") as f:
                return self._enviar(200, f.read(), "text/html; charset=utf-8")
        if url.path == "/fondo_mapa.jpg":                 # fondo del mapa (© colaboradores de OpenStreetMap)
            with open(os.path.join(AQUI, "fondo_mapa.jpg"), "rb") as f:
                return self._enviar(200, f.read(), "image/jpeg")
        activos = {
            "/assets/logo-transmitracker.png": ("logo-transmitracker.png", "image/png"),
            "/assets/concrete-reference.png": ("concrete-reference.png", "image/png"),
            "/assets/bogota-colpatria.jpg": ("bogota-colpatria.jpg", "image/jpeg"),
            "/assets/bogota-plaza-bolivar.jpg": ("bogota-plaza-bolivar.jpg", "image/jpeg"),
            "/assets/bogota-transmilenio.jpg": ("bogota-transmilenio.jpg", "image/jpeg"),
        }
        if url.path in activos:
            nombre_archivo, tipo = activos[url.path]
            with open(os.path.join(AQUI, "assets", nombre_archivo), "rb") as f:
                return self._enviar(200, f.read(), tipo)
        if url.path.startswith("/api/"):
            nombre = url.path[5:]
            funcion = RUTAS.get(nombre)
            if funcion is None:
                return self._enviar(404, json.dumps({"error": "no existe"}), "application/json")
            q = {k: v[0] for k, v in parse_qs(url.query, keep_blank_values=True).items()}
            try:
                if nombre == "medir":                      # tarda: no bloquea a los demás
                    resultado = funcion(q)
                else:
                    with CANDADO:
                        resultado = funcion(q)
                return self._enviar(200, json.dumps(resultado, ensure_ascii=False),
                                    "application/json; charset=utf-8")
            except Exception as e:                         # el error se muestra en la página
                return self._enviar(500, json.dumps({"error": str(e)}, ensure_ascii=False),
                                    "application/json; charset=utf-8")
        self._enviar(404, "No encontrado", "text/plain; charset=utf-8")

    def log_message(self, *args):                          # sin ruido en la terminal
        pass


def main():
    en_render = "PORT" in os.environ          # Render define PORT; en tu PC no existe
    puerto = int(os.environ.get("PORT", 8501))
    host = "0.0.0.0" if en_render else "127.0.0.1"
    while True:
        try:
            servidor = ThreadingHTTPServer((host, puerto), Manejador)
            break
        except OSError:
            if en_render:
                raise                         # en Render no cambiamos de puerto
            puerto += 1
    url = "http://localhost:%d" % puerto
    print("Red cargada: %d estaciones, %d rutas" % (RED.num_estaciones(), len(RED.nombres_rutas())), flush=True)
    print("App lista en", url, "  (Ctrl + C para cerrar)", flush=True)
    if not en_render:                         # abrir el navegador solo tiene sentido en tu PC
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nApp cerrada.")


if __name__ == "__main__":
    main()
