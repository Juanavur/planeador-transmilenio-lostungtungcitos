"""
Árbol AVL ordenado por nombre (texto). Se usa para R2 (autocompletar) y R3 (rango).

Por qué un AVL y no un arreglo ordenado
---------------------------------------
Con agregar_parada (R7) puede aparecer una estación nueva. En un arreglo ordenado
meterla cuesta O(n) (correr todo a la derecha). En el AVL cuesta O(log n) y el árbol
se mantiene balanceado con rotaciones, así que nunca se degenera en una lista.

Complejidad (n = número de estaciones)
-----------
- insertar / buscar: O(log n)
- desde(texto): llegar al primer nombre >= texto cuesta O(log n); cada siguiente
  nombre en orden alfabético cuesta O(1) amortizado. Pedir m nombres: O(log n + m).
"""


class _Nodo:
    __slots__ = ("clave", "valor", "izq", "der", "altura")

    def __init__(self, clave, valor):
        self.clave = clave
        self.valor = valor
        self.izq = None
        self.der = None
        self.altura = 1


def _altura(n):
    return n.altura if n is not None else 0


def _actualizar(n):
    a, b = _altura(n.izq), _altura(n.der)
    n.altura = (a if a > b else b) + 1


def _rotar_derecha(y):
    x = y.izq
    y.izq = x.der
    x.der = y
    _actualizar(y)
    _actualizar(x)
    return x


def _rotar_izquierda(x):
    y = x.der
    x.der = y.izq
    y.izq = x
    _actualizar(x)
    _actualizar(y)
    return y


def _balancear(n):
    _actualizar(n)
    fb = _altura(n.izq) - _altura(n.der)
    if fb > 1:                                   # cargado a la izquierda
        if _altura(n.izq.izq) < _altura(n.izq.der):
            n.izq = _rotar_izquierda(n.izq)      # caso izquierda-derecha
        return _rotar_derecha(n)
    if fb < -1:                                  # cargado a la derecha
        if _altura(n.der.der) < _altura(n.der.izq):
            n.der = _rotar_derecha(n.der)        # caso derecha-izquierda
        return _rotar_izquierda(n)
    return n


class AVL:
    def __init__(self):
        self._raiz = None
        self._n = 0

    def __len__(self):
        return self._n

    def insertar(self, clave, valor):
        self._raiz = self._insertar(self._raiz, clave, valor)

    def _insertar(self, n, clave, valor):
        if n is None:
            self._n += 1
            return _Nodo(clave, valor)
        if clave < n.clave:
            n.izq = self._insertar(n.izq, clave, valor)
        elif clave > n.clave:
            n.der = self._insertar(n.der, clave, valor)
        else:
            n.valor = valor
            return n
        return _balancear(n)

    def buscar(self, clave):
        n = self._raiz
        while n is not None:
            if clave < n.clave:
                n = n.izq
            elif clave > n.clave:
                n = n.der
            else:
                return n.valor
        return None

    def desde(self, inicio):
        """Recorre en orden alfabético los (clave, valor) con clave >= inicio.
        Es un recorrido inorden con pila explícita que arranca en el primer nodo >= inicio.
        Como es un generador, quien lo usa puede parar cuando quiera (por eso sale
        O(log n + m) y no O(n))."""
        pila = []
        n = self._raiz
        while n is not None:                      # baja guardando los candidatos >= inicio
            if n.clave >= inicio:
                pila.append(n)
                n = n.izq
            else:
                n = n.der
        while len(pila) > 0:
            n = pila.pop()
            yield n.clave, n.valor
            m = n.der                             # sucesor: lo más a la izquierda del subárbol derecho
            while m is not None:
                pila.append(m)
                m = m.izq

    def altura(self):
        return _altura(self._raiz)
