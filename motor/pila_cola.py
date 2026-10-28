"""
Pila (R9: deshacer / rehacer) y Cola (R10: fila de abordaje), con nodos enlazados.

Pila: el último en entrar es el primero en salir (LIFO). Push y pop en la cima: O(1).
Cola: el primero en llegar es el primero en salir (FIFO). Encolar al final y
      desencolar al frente: O(1). (list.pop(0) sería O(n) porque corre todo el arreglo.)
La pila usa nodos enlazados; la cola, un arreglo circular (ver por qué abajo).
"""


class _Nodo:
    __slots__ = ("valor", "sig")

    def __init__(self, valor, sig=None):
        self.valor = valor
        self.sig = sig


class Pila:
    def __init__(self):
        self._cima = None
        self._n = 0

    def __len__(self):
        return self._n

    def vacia(self):
        return self._cima is None

    def apilar(self, valor):
        self._cima = _Nodo(valor, self._cima)
        self._n += 1

    def desapilar(self):
        if self._cima is None:
            return None
        v = self._cima.valor
        self._cima = self._cima.sig
        self._n -= 1
        return v

    def vaciar(self):
        """O(1): se suelta la cima y el recolector de basura se encarga del resto."""
        self._cima = None
        self._n = 0


class Cola:
    """Cola con ARREGLO CIRCULAR: `frente` apunta al primero y el final se calcula con
    módulo, así que el arreglo se reutiliza dando la vuelta. Si se llena, se duplica
    (O(n) cada vez que se duplica -> O(1) amortizado).

    Por qué arreglo circular y no nodos enlazados: con cientos de miles de pasajeros,
    crear un objeto nodo por pasajero hace trabajar de más al recolector de basura de
    Python y en la práctica la simulación crecía más rápido que lineal. El arreglo solo
    guarda números, no crea objetos."""

    def __init__(self, capacidad=16):
        self._datos = [None] * capacidad
        self._frente = 0
        self._n = 0

    def __len__(self):
        return self._n

    def vacia(self):
        return self._n == 0

    def encolar(self, valor):
        cap = len(self._datos)
        if self._n == cap:
            nuevo = [None] * (cap * 2)
            for i in range(self._n):
                nuevo[i] = self._datos[(self._frente + i) % cap]
            self._datos = nuevo
            self._frente = 0
            cap *= 2
        self._datos[(self._frente + self._n) % cap] = valor
        self._n += 1

    def desencolar(self):
        if self._n == 0:
            return None
        v = self._datos[self._frente]
        self._datos[self._frente] = None
        self._frente = (self._frente + 1) % len(self._datos)
        self._n -= 1
        return v
