"""
Clase Red: el contrato que prueba el script del profesor (R1 a R9).

Estructuras que guarda la red
-----------------------------
  _estaciones : TablaHash   nombre -> Estacion                         (R1, R8)
  _indice     : AVL         nombre -> Estacion, en orden alfabético     (R2, R3)
  _rutas      : TablaHash   nombre -> Ruta (lista doble + tabla nodos)  (R5, R7)
  _horarios   : TablaHash   "RUTA|ESTACION" -> arreglo ordenado de minutos (R4, R6)
  _ranking    : arreglo de estaciones ordenado por buses al día (cache) (R6)
  _deshacer, _rehacer : Pila de cambios                                 (R9)

Notación de complejidades en este archivo:
  n = estaciones de la red, h = pasadas de una ruta por una estación,
  m = paradas de una ruta, k = cuántos resultados se piden.
"""

import csv

from .tabla_hash import TablaHash
from .avl import AVL
from .lista_doble import ListaDoble
from .pila_cola import Pila
from .ordenar import ordenar_si_hace_falta, merge_sort, primer_mayor_igual
from .horas import a_minutos, a_texto

_SEP = "|"   # separador de la clave compuesta ruta|estacion


# =============================================================================== modelos
class Estacion:
    __slots__ = ("nombre", "abierta", "existe", "buses", "rutas")

    def __init__(self, nombre):
        self.nombre = nombre
        self.abierta = True
        self.existe = True          # False solo si se deshizo la creación (ver R9)
        self.buses = 0              # buses que pasan al día (para R6)
        self.rutas = TablaHash(5)   # nombre de ruta -> Ruta, rutas que paran aquí

    def visible(self):
        """R8: una estación cerrada (o deshecha) no aparece ni se usa."""
        return self.existe and self.abierta


class Ruta:
    __slots__ = ("nombre", "paradas", "nodos")

    def __init__(self, nombre):
        self.nombre = nombre
        self.paradas = ListaDoble()   # recorrido en su único sentido
        self.nodos = TablaHash(7)     # estación -> nodo de la lista, para editar en O(1)


def _archivo(carpeta, nombre):
    """Une carpeta y archivo sin usar os (no está en los módulos permitidos).
    La barra / funciona también en Windows."""
    while len(carpeta) > 1 and (carpeta.endswith("/") or carpeta.endswith("\\")):
        carpeta = carpeta[:-1]
    return carpeta + "/" + nombre


def _leer_csv(ruta_archivo, columnas):
    """Lee un CSV y devuelve filas con las columnas pedidas, en ese orden.
    (No se usa csv.DictReader porque devuelve dict, que está prohibido en motor/.)"""
    with open(ruta_archivo, newline="", encoding="utf-8-sig") as f:
        lector = csv.reader(f)
        encabezado = next(lector, None)
        if encabezado is None:
            return
        posiciones = []
        for col in columnas:
            pos = -1
            for i in range(len(encabezado)):
                if encabezado[i].strip().lower() == col:
                    pos = i
            if pos < 0:
                raise ValueError("Falta la columna '%s' en %s" % (col, ruta_archivo))
            posiciones.append(pos)
        for fila in lector:
            if len(fila) == 0:
                continue
            yield [fila[p].strip() for p in posiciones]


# =============================================================================== Red
class Red:
    def __init__(self, carpeta):
        self._estaciones = TablaHash()
        self._indice = AVL()
        self._rutas = TablaHash()
        self._horarios = TablaHash()
        self._deshacer = Pila()
        self._rehacer = Pila()
        self._ranking = []
        self._ranking_sucio = True
        self._cargar(carpeta)

    # --------------------------------------------------------------------- carga
    def _cargar(self, carpeta):
        # 1) estaciones
        for (nombre,) in _leer_csv(_archivo(carpeta, "estaciones.csv"), ["nombre"]):
            if nombre != "" and self._estaciones.obtener(nombre) is None:
                self._crear_estacion(nombre)

        # 2) rutas: se agrupan las filas por ruta y se ordenan por la columna "orden"
        filas_por_ruta = TablaHash()
        nombres_rutas = []
        for ruta, orden, est in _leer_csv(_archivo(carpeta, "rutas.csv"),
                                          ["ruta", "orden", "estacion"]):
            lista = filas_por_ruta.obtener(ruta)
            if lista is None:
                lista = []
                filas_por_ruta.poner(ruta, lista)
                nombres_rutas.append(ruta)
            lista.append((int(orden), est))

        def por_orden(a, b):
            return a[0] < b[0]

        for nombre_ruta in nombres_rutas:
            filas = ordenar_si_hace_falta(filas_por_ruta.obtener(nombre_ruta), por_orden)
            r = Ruta(nombre_ruta)
            self._rutas.poner(nombre_ruta, r)
            for _, est in filas:
                if r.nodos.contiene(est):          # una estación una sola vez por ruta
                    continue
                e = self._estaciones.obtener(est)
                if e is None:
                    e = self._crear_estacion(est)
                r.nodos.poner(est, r.paradas.agregar_al_final(est))
                e.rutas.poner(nombre_ruta, r)

        # 3) horarios: "RUTA|ESTACION" -> arreglo de minutos.
        #    Truco: si filas seguidas tienen la misma clave (el CSV suele venir agrupado),
        #    se reutiliza el arreglo sin volver a calcular el hash.
        clave_anterior = None
        arreglo = None
        claves = []
        for ruta, est, hora in _leer_csv(_archivo(carpeta, "horarios.csv"),
                                         ["ruta", "estacion", "hora"]):
            minutos = a_minutos(hora)
            if minutos is None:
                continue
            clave = ruta + _SEP + est
            if clave != clave_anterior:
                arreglo = self._horarios.obtener(clave)
                if arreglo is None:
                    arreglo = []
                    self._horarios.poner(clave, arreglo)
                    claves.append((clave, ruta, est))
                clave_anterior = clave
            arreglo.append(minutos)

        for clave, ruta, est in claves:
            arr = ordenar_si_hace_falta(self._horarios.obtener(clave))
            self._horarios.poner(clave, arr)
            r = self._rutas.obtener(ruta)
            if r is not None and r.nodos.contiene(est):
                self._estaciones.obtener(est).buses += len(arr)

    def _crear_estacion(self, nombre):
        e = Estacion(nombre)
        self._estaciones.poner(nombre, e)
        self._indice.insertar(nombre, e)
        self._ranking_sucio = True
        return e

    def _pasadas(self, ruta, estacion):
        arr = self._horarios.obtener(ruta + _SEP + estacion)
        return 0 if arr is None else len(arr)

    def _visible(self, nombre):
        e = self._estaciones.obtener(nombre)
        if e is None or not e.visible():
            return None
        return e

    # ===================================================================== R1
    def estado(self, nombre):
        """R1. Devuelve (existe, abierta).  O(1) promedio: una consulta a la tabla hash.
        Se escogió tabla hash y no búsqueda binaria/AVL (O(log n)) porque es la
        consulta más frecuente de la app."""
        e = self._estaciones.obtener(nombre)
        if e is None or not e.existe:
            return (False, False)
        return (True, e.abierta)

    # ===================================================================== R2
    def autocompletar(self, prefijo, k):
        """R2. Hasta k estaciones abiertas que empiezan por `prefijo`, en orden alfabético.
        O(log n + k + c), c = cerradas que se saltan dentro del prefijo.
        Todo lo que empieza por P es >= P en orden alfabético y está seguido en el
        recorrido inorden, así que basta arrancar en P y parar al salir del prefijo."""
        res = []
        if k <= 0:
            return res
        for nombre, e in self._indice.desde(prefijo):
            if not nombre.startswith(prefijo):
                break
            if e.visible():
                res.append(nombre)
                if len(res) == k:
                    break
        return res

    # ===================================================================== R3
    def rango(self, desde, hasta):
        """R3. Estaciones abiertas con desde <= nombre <= hasta, en orden alfabético.
        O(log n + m), m = estaciones dentro del rango."""
        res = []
        if desde > hasta:
            return res
        for nombre, e in self._indice.desde(desde):
            if nombre > hasta:
                break
            if e.visible():
                res.append(nombre)
        return res

    # ===================================================================== R4
    def proximo_bus(self, estacion, ruta, hora):
        """R4. Hora ('HH:MM') del siguiente bus de `ruta` en `estacion` a partir de `hora`
        (si pasa justo a esa hora, cuenta). Si ya no hay más ese día, devuelve el primero
        del día siguiente. None si la estación está cerrada, la ruta no para ahí o no
        tiene horarios.
        O(log h): búsqueda binaria en el arreglo ordenado de horas de esa ruta y estación.
        Se descartó recorrer el arreglo (O(h)) porque las troncales pasan cientos de veces."""
        if self._visible(estacion) is None:
            return None
        r = self._rutas.obtener(ruta)
        if r is None or not r.nodos.contiene(estacion):
            return None
        arr = self._horarios.obtener(ruta + _SEP + estacion)
        minutos = a_minutos(hora)
        if arr is None or len(arr) == 0 or minutos is None:
            return None
        i = primer_mayor_igual(arr, minutos)
        if i == len(arr):
            i = 0                                   # se pasa al día siguiente
        return a_texto(arr[i])

    # ===================================================================== R5
    def viaje(self, origen, destino):
        """R5. Viaje directo o con UN transbordo que pase por menos paradas.

        Devuelve una lista de tramos (ruta, sube_en, baja_en, paradas):
          - directo:     [(ruta, origen, destino, p)]
          - transbordo:  [(ruta1, origen, T, p1), (ruta2, T, destino, p2)]
        [] si origen == destino.  None si no hay viaje (o alguna está cerrada).

        Idea (no hay un algoritmo del curso que lo haga tal cual; se combinan dos):
          1. Desde el DESTINO, por cada ruta que para ahí, se camina hacia ATRÁS por la
             lista doble y se anota en una tabla hash cada estación T con cuántas paradas
             le faltan para llegar al destino (y en qué ruta). Es "BFS de un nivel" hacia atrás.
          2. Desde el ORIGEN, por cada ruta que para ahí, se camina hacia ADELANTE
             contando paradas. Si se llega al destino es un directo; si se pasa por una T
             de la tabla, hay un transbordo con total = paradas hasta T + las anotadas.
          3. Gana el de menos paradas; si empatan, el directo; luego por nombre de ruta.
        Las paradas cuentan todas las estaciones por las que pasa el bus (también las
        cerradas, porque el bus pasa por ahí aunque no pare); el transbordo solo en abiertas.
        O(L), L = suma de las longitudes de las rutas que pasan por origen y destino."""
        eo = self._visible(origen)
        ed = self._visible(destino)
        if eo is None or ed is None:
            return None
        if origen == destino:
            return []

        # 1) hacia atrás desde el destino: estación T -> [paradas hasta destino, ruta]
        hacia_destino = TablaHash()
        for rb in ed.rutas.valores():
            nodo = rb.nodos.obtener(destino).ant
            d = 1
            while nodo is not None:
                t = nodo.estacion
                et = self._estaciones.obtener(t)
                if et.visible():
                    actual = hacia_destino.obtener(t)
                    if actual is None:
                        hacia_destino.poner(t, [d, rb.nombre])
                    elif d < actual[0] or (d == actual[0] and rb.nombre < actual[1]):
                        actual[0] = d
                        actual[1] = rb.nombre
                nodo = nodo.ant
                d += 1

        # 2) hacia adelante desde el origen
        mejor = None          # (total, n_tramos, ruta1, ruta2, transbordo, p1, p2)
        for ra in eo.rutas.valores():
            nodo = ra.nodos.obtener(origen).sig
            j = 1
            while nodo is not None:
                x = nodo.estacion
                if x == destino:
                    cand = (j, 1, ra.nombre, "", "", j, 0)
                    if mejor is None or self._mejor_que(cand, mejor):
                        mejor = cand
                    break                       # más allá del destino solo hay viajes más largos
                info = hacia_destino.obtener(x)
                if info is not None and info[1] != ra.nombre:
                    cand = (j + info[0], 2, ra.nombre, info[1], x, j, info[0])
                    if mejor is None or self._mejor_que(cand, mejor):
                        mejor = cand
                nodo = nodo.sig
                j += 1

        if mejor is None:
            return None
        if mejor[1] == 1:
            return [(mejor[2], origen, destino, mejor[5])]
        return [(mejor[2], origen, mejor[4], mejor[5]), (mejor[3], mejor[4], destino, mejor[6])]

    @staticmethod
    def _mejor_que(a, b):
        """Compara candidatos: menos paradas, luego menos tramos, luego nombres de ruta."""
        for i in range(5):
            if a[i] != b[i]:
                return a[i] < b[i]
        return False

    # ===================================================================== R6
    def ranking(self, k):
        """R6. Las k estaciones abiertas por donde pasan más buses al día
        (empates: orden alfabético).
        El arreglo ordenado se guarda (cache). Consultar es O(k + c), c = cerradas que se
        saltan. Cerrar/reabrir NO lo desordena (solo se saltan las cerradas); solo una
        edición de ruta cambia los conteos y marca el cache como sucio: la siguiente
        consulta lo reconstruye con merge sort en O(n log n).
        Se descartó un heap en cada consulta (O(n + k log n)) porque se consulta mucho
        y cambia poco."""
        res = []
        if k <= 0:
            return res
        if self._ranking_sucio:
            self._reconstruir_ranking()
        for e in self._ranking:
            if e.visible():
                res.append(e.nombre)
                if len(res) == k:
                    break
        return res

    def _reconstruir_ranking(self):
        todas = []
        for e in self._estaciones.valores():
            if e.existe:
                todas.append(e)

        def va_antes(a, b):
            if a.buses != b.buses:
                return a.buses > b.buses
            return a.nombre < b.nombre

        self._ranking = merge_sort(todas, va_antes)
        self._ranking_sucio = False

    def buses_al_dia(self, nombre):
        """Extra para la app: cuántos buses pasan al día por la estación."""
        e = self._estaciones.obtener(nombre)
        return 0 if e is None or not e.existe else e.buses

    # ===================================================================== R7
    def agregar_parada(self, ruta, nueva, despues_de):
        """R7. Mete `nueva` justo después de `despues_de` en la ruta
        (despues_de=None la pone al inicio). Si `nueva` no existía como estación, se crea.
        Devuelve True si se hizo.  O(1) con la lista doble + tabla de nodos
        (más O(log n) si hay que crear la estación en el AVL)."""
        r = self._rutas.obtener(ruta)
        if r is None or nueva == "" or nueva == despues_de or r.nodos.contiene(nueva):
            return False
        if despues_de is not None and not r.nodos.contiene(despues_de):
            return False
        e = self._estaciones.obtener(nueva)
        creo = e is None or not e.existe
        self._hacer_agregar(r, nueva, despues_de, creo)
        self._registrar(("agregar", ruta, nueva, despues_de, creo))
        return True

    def quitar_parada(self, ruta, estacion):
        """R7. Quita la estación del recorrido de la ruta. True si se hizo. O(1)."""
        r = self._rutas.obtener(ruta)
        if r is None or not r.nodos.contiene(estacion):
            return False
        anterior = self._hacer_quitar(r, estacion)
        self._registrar(("quitar", ruta, estacion, anterior))
        return True

    def recorrido(self, ruta, al_reves=False):
        """R7. Lista de estaciones de la ruta, en su sentido o al revés.
        O(m): se recorre la lista doble por `sig` o por `ant`. None si no existe."""
        r = self._rutas.obtener(ruta)
        if r is None:
            return None
        return r.paradas.a_lista(al_reves)

    def _hacer_agregar(self, r, nueva, despues_de, creo):
        e = self._estaciones.obtener(nueva)
        if e is None:
            e = self._crear_estacion(nueva)
        elif creo:
            e.existe = True
        ref = None if despues_de is None else r.nodos.obtener(despues_de)
        r.nodos.poner(nueva, r.paradas.insertar_despues(ref, nueva))
        e.rutas.poner(r.nombre, r)
        e.buses += self._pasadas(r.nombre, nueva)
        self._ranking_sucio = True

    def _hacer_quitar(self, r, estacion):
        """Quita y devuelve el nombre de la parada anterior (o None) para poder deshacer."""
        nodo = r.nodos.obtener(estacion)
        anterior = None if nodo.ant is None else nodo.ant.estacion
        r.paradas.eliminar(nodo)
        r.nodos.eliminar(estacion)
        e = self._estaciones.obtener(estacion)
        e.rutas.eliminar(r.nombre)
        e.buses -= self._pasadas(r.nombre, estacion)
        self._ranking_sucio = True
        return anterior

    # ===================================================================== R8
    def cerrar(self, nombre):
        """R8. Cierra la estación. True si estaba abierta. O(1).
        Cerrar es solo cambiar una bandera; cada consulta revisa `visible()`."""
        e = self._estaciones.obtener(nombre)
        if e is None or not e.existe or not e.abierta:
            return False
        e.abierta = False
        self._registrar(("cerrar", nombre))
        return True

    def reabrir(self, nombre):
        """R8. Reabre la estación. True si estaba cerrada. O(1)."""
        e = self._estaciones.obtener(nombre)
        if e is None or not e.existe or e.abierta:
            return False
        e.abierta = True
        self._registrar(("reabrir", nombre))
        return True

    # ===================================================================== R9
    def _registrar(self, cambio):
        """Todo cambio nuevo va a la pila de deshacer y borra lo que había para rehacer."""
        self._deshacer.apilar(cambio)
        self._rehacer.vaciar()

    def deshacer(self):
        """R9. Deshace el último cambio (cierre, reapertura o edición). O(1).
        True si había algo que deshacer."""
        cambio = self._deshacer.desapilar()
        if cambio is None:
            return False
        self._aplicar(cambio, al_reves=True)
        self._rehacer.apilar(cambio)
        return True

    def rehacer(self):
        """R9. Rehace el último cambio deshecho. O(1). True si había algo."""
        cambio = self._rehacer.desapilar()
        if cambio is None:
            return False
        self._aplicar(cambio, al_reves=False)
        self._deshacer.apilar(cambio)
        return True

    def _aplicar(self, cambio, al_reves):
        tipo = cambio[0]
        if tipo == "cerrar" or tipo == "reabrir":
            e = self._estaciones.obtener(cambio[1])
            cerrar = (tipo == "cerrar") != al_reves      # deshacer un cierre = reabrir
            e.abierta = not cerrar
        elif tipo == "agregar":
            _, ruta, nueva, despues_de, creo = cambio
            r = self._rutas.obtener(ruta)
            if al_reves:
                self._hacer_quitar(r, nueva)
                if creo:
                    self._estaciones.obtener(nueva).existe = False
            else:
                self._hacer_agregar(r, nueva, despues_de, creo)
        elif tipo == "quitar":
            _, ruta, estacion, anterior = cambio
            r = self._rutas.obtener(ruta)
            if al_reves:
                self._hacer_agregar(r, estacion, anterior, False)
            else:
                self._hacer_quitar(r, estacion)

    # ===================================================================== extras para la app
    def rutas_de(self, estacion):
        """Nombres de las rutas que paran en la estación (en orden alfabético)."""
        e = self._estaciones.obtener(estacion)
        if e is None:
            return []
        nombres = []
        for r in e.rutas.valores():
            nombres.append(r.nombre)
        return merge_sort(nombres)

    def todas_las_estaciones(self):
        """Extra para la tabla de datos: todas las estaciones que existen (abiertas y
        cerradas) en orden alfabético, como (nombre, abierta, rutas que paran, buses al día).
        Recorrido inorden completo del AVL: O(n)."""
        filas = []
        for nombre, e in self._indice.desde(""):
            if e.existe:
                filas.append((nombre, e.abierta, len(e.rutas), e.buses))
        return filas

    def horarios(self, ruta, estacion):
        """Extra para la tabla de datos: las horas ('HH:MM') en que la ruta pasa por la
        estación, en orden. [] si la ruta no para ahí. O(h)."""
        r = self._rutas.obtener(ruta)
        if r is None or not r.nodos.contiene(estacion):
            return []
        arr = self._horarios.obtener(ruta + _SEP + estacion)
        res = []
        if arr is not None:
            for m in arr:
                res.append(a_texto(m))
        return res

    def nombres_rutas(self):
        nombres = []
        for r in self._rutas.valores():
            nombres.append(r.nombre)
        return merge_sort(nombres)

    def num_estaciones(self):
        """Estaciones que existen (abiertas o cerradas). O(n), solo lo usa la app."""
        total = 0
        for e in self._estaciones.valores():
            if e.existe:
                total += 1
        return total
