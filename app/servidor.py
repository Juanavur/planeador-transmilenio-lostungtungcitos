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
    return RED.rango("", "￿")


# ------------------------------------------------------------------ cada endpoint llama al motor
def api_info(q):
    return {"estaciones": RED.num_estaciones(), "rutas": RED.nombres_rutas(), "abiertas": todas()}


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
    pasajeros = int(q.get("pasajeros", 100000))
    ventana = float(q.get("ventana", 120))
    frecuencia = float(q.get("frecuencia", 0.25))
    capacidad = int(q.get("capacidad", 250))
    rnd = random.Random(0)
    # llegadas con un pico a la mitad de la ventana (más gente en la hora pico)
    llegadas = sorted(rnd.triangular(0, ventana, ventana / 2) for _ in range(pasajeros))
    esperas = simular_fila(llegadas, frecuencia, capacidad)                        # R10
    suma, cuenta = {}, {}
    for t, e in zip(llegadas, esperas):
        m = int(t)
        suma[m] = suma.get(m, 0) + e
        cuenta[m] = cuenta.get(m, 0) + 1
    minutos = sorted(suma)
    return {"promedio": sum(esperas) / len(esperas), "maxima": max(esperas),
            "buses": -(-pasajeros // capacidad),
            "curva": [[m, suma[m] / cuenta[m]] for m in minutos]}


def api_medir(q):
    tamanos = sorted(int(x) for x in q.get("tamanos", "1000,2000,4000,8000").split(",") if x.strip())
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
    puerto = 8501
    while True:
        try:
            servidor = ThreadingHTTPServer(("127.0.0.1", puerto), Manejador)
            break
        except OSError:
            puerto += 1
    url = "http://localhost:%d" % puerto
    print("Red cargada: %d estaciones, %d rutas" % (RED.num_estaciones(), len(RED.nombres_rutas())))
    print("App lista en", url, "  (Ctrl + C para cerrar)")
    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nApp cerrada.")


if __name__ == "__main__":
    main()
