"""
App del planeador (front web). Solo usa la librería estándar de Python: no hay que instalar nada.

    python app/servidor.py

Abre el navegador en http://localhost:8501. Para cerrarla: Ctrl + C.

Este archivo solo traduce peticiones del navegador a llamadas del motor y devuelve JSON.
Ninguna regla del sistema vive aquí: todo lo decide motor/.
"""


import json
import math
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
    "R6 ranking (k=10)": "El arreglo ordenado está guardado; solo se leen k elementos.",
    "R7 agregar + quitar parada": "Lista doble + tabla de nodos: se cambian punteros, nada más.",
    "R8 cerrar + reabrir": "Cambiar una bandera después de una consulta a la tabla hash.",
    "R9 deshacer + rehacer": "Sacar y meter en una pila de nodos.",
    "R10 simular_fila (50n pasajeros)": "Cada pasajero entra y sale de la cola una vez: lineal en P.",
}


def limpiar(texto):
    """Lo que escribe la persona -> formato de los datos (MAYÚSCULAS, sin tildes).
    Es comodidad de la interfaz, no una regla del sistema."""
    texto = unicodedata.normalize("NFD", texto or "")
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return " ".join(texto.upper().split())


def todas():
    return RED.rango("", "\uffff")


# ------------------------------------------------------------------ cada endpoint llama al motor
def api_info(q):
    return {"estaciones": RED.num_estaciones(), "rutas": RED.nombres_rutas(), "abiertas": todas()}

def api_ping(q):
    return {"ok": True}

def api_estado(q):
    nombre = limpiar(q.get("nombre", ""))
    existe, abierta = RED.estado(nombre)                                       # R1
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
    return RED.viaje(q.get("origen", ""), q.get("destino", ""))                    # R5


def api_ranking(q):
    top = RED.ranking(int(q.get("k", 10)))                                         # R6
    return [{"nombre": e, "buses": RED.buses_al_dia(e)} for e in top]


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


def api_fila(q):
    pasajeros = max(1, int(float(q.get("pasajeros", 100000))))
    ventana = max(0.01, float(q.get("ventana", 120)))
    frecuencia = max(0.0001, float(q.get("frecuencia", 0.25)))
    capacidad = max(1, int(float(q.get("capacidad", 250))))
    buses_totales = -(-pasajeros // capacidad)

    # Tope seguro de memoria y CPU para Render Free (máx 200,000 nodos en la Cola)
    TOPE_P = 200_000
    TOPE_PUNTOS_CURVA = 240

    # Si los números son manejables en RAM y no requerirán millones de buses vacíos,
    # usamos simular_fila() directamente o reescalando P y capacidad por el mismo factor:
    escala = max(1.0, pasajeros / TOPE_P)
    p_sim = int(round(pasajeros / escala))
    cap_sim = int(round(capacidad / escala))
    buses_estimados = pasajeros / capacidad

    if cap_sim >= 1 and buses_estimados <= 500_000:
        rnd = random.Random(0)
        # Cuantiles exactos o muestra aleatoria ordenada de la distribución triangular
        llegadas = sorted(rnd.triangular(0, ventana, ventana / 2) for _ in range(p_sim))
        esperas = simular_fila(llegadas, frecuencia, cap_sim)                      # R10
        paso_min = max(1.0, ventana / TOPE_PUNTOS_CURVA)
        suma, cuenta = {}, {}
        for t, e in zip(llegadas, esperas):
            m = int(t // paso_min) * paso_min
            suma[m] = suma.get(m, 0.0) + e
            cuenta[m] = cuenta.get(m, 0) + 1
        minutos = sorted(suma)
        return {
            "promedio": sum(esperas) / len(esperas),
            "maxima": max(esperas),
            "buses": buses_totales,
            "curva": [[round(m, 2), suma[m] / cuenta[m]] for m in minutos],
        }

    # Si el profesor ingresa un número astronómico (ej. 10^12 pasajeros o 10^9 buses),
    # generamos N cuantiles exactos de la distribución triangular (inversa de la CDF)
    # y los pasamos por simular_fila() escalando el tiempo para que tarde < 5 ms:
    n_muestra = 5000
    # Inversa exacta de la distribución triangular simétrica en [0, ventana] con pico en ventana/2
    llegadas_norm = []
    for i in range(n_muestra):
        u = (i + 0.5) / n_muestra
        if u < 0.5:
            t_val = ventana * math.sqrt(u / 2.0)
        else:
            t_val = ventana * (1.0 - math.sqrt((1.0 - u) / 2.0))
        llegadas_norm.append(t_val)

    # Cada uno de los n_muestra representa (pasajeros / n_muestra) personas.
    # Equivale a que 1 unidad de capacidad en la muestra = (capacidad * n_muestra / pasajeros)
    # Para usar simular_fila() con capacidad entera = 1, escalamos la frecuencia efectiva:
    frec_efectiva = frecuencia * (pasajeros / (n_muestra * capacidad))
    esperas = simular_fila(llegadas_norm, frec_efectiva, 1)                        # R10

    paso_min = max(1.0, ventana / min(TOPE_PUNTOS_CURVA, int(ventana) or 1))
    suma, cuenta = {}, {}
    for t, e in zip(llegadas_norm, esperas):
        m = int(t // paso_min) * paso_min
        suma[m] = suma.get(m, 0.0) + e
        cuenta[m] = cuenta.get(m, 0) + 1
    minutos = sorted(suma)
    return {
        "promedio": sum(esperas) / len(esperas),
        "maxima": max(esperas),
        "buses": buses_totales,
        "curva": [[round(m, 2), suma[m] / cuenta[m]] for m in minutos],
    }


def api_medir(q):
    # Limitar tamaños máximos para evitar que un tamaño absurdo en R11 agote los 512MB de Render
    tamanos_raw = [int(x) for x in q.get("tamanos", "1000,2000,4000,8000").split(",") if x.strip()]
    tamanos = sorted(min(max(10, x), 32000) for x in tamanos_raw[:6])
    filas = medir(tamanos, veces=1500)                                             # R11
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
    def _enviar(self, codigo, cuerpo, tipo, cache="no-store"):
        datos = cuerpo.encode("utf-8") if isinstance(cuerpo, str) else cuerpo
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(datos)))
        self.send_header("Cache-Control", cache)
        self.end_headers()
        self.wfile.write(datos)

    def do_GET(self):
        url = urlparse(self.path)
        if url.path in ("/", "/index.html"):
            with open(os.path.join(AQUI, "index.html"), encoding="utf-8") as f:
                return self._enviar(200, f.read(), "text/html; charset=utf-8")
        if url.path == "/fondo_mapa.jpg":
            with open(os.path.join(AQUI, "fondo_mapa.jpg"), "rb") as f:
                return self._enviar(200, f.read(), "image/jpeg", "public, max-age=86400")
        if url.path == "/icono.png":
            with open(os.path.join(AQUI, "icono.png"), "rb") as f:
                return self._enviar(200, f.read(), "image/png", "public, max-age=86400")
        if url.path.startswith("/api/"):
            nombre = url.path[5:]
            funcion = RUTAS.get(nombre)
            if funcion is None:
                return self._enviar(404, json.dumps({"error": "no existe"}), "application/json")
            q = {k: v[0] for k, v in parse_qs(url.query, keep_blank_values=True).items()}
            try:
                if nombre in ("medir", "fila"):            # no tocan RED: no bloquean a los demás
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
