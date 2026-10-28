"""
Lista doblemente enlazada: el recorrido de cada ruta (R7).

Cada nodo conoce al anterior y al siguiente. Si además se tiene una tabla hash
estación -> nodo (eso lo hace la clase Ruta), agregar una parada después de otra o
quitar una parada es O(1): solo se cambian punteros, no se corre nada.

Complejidad (m = paradas de la ruta)
-----------
- insertar_despues / eliminar: O(1)
- recorrer hacia adelante o hacia atrás: O(m)
"""


class NodoParada:
    __slots__ = ("estacion", "ant", "sig")

    def __init__(self, estacion):
        self.estacion = estacion      # nombre de la estación (texto)
        self.ant = None
        self.sig = None


class ListaDoble:
    def __init__(self):
        self.cabeza = None
        self.cola = None
        self.tam = 0

    def __len__(self):
        return self.tam

    def insertar_despues(self, ref, estacion):
        """Inserta después del nodo ref. Si ref es None, inserta al inicio."""
        nuevo = NodoParada(estacion)
        if ref is None:
            nuevo.sig = self.cabeza
            if self.cabeza is not None:
                self.cabeza.ant = nuevo
            self.cabeza = nuevo
            if self.cola is None:
                self.cola = nuevo
        else:
            nuevo.ant = ref
            nuevo.sig = ref.sig
            if ref.sig is not None:
                ref.sig.ant = nuevo
            else:
                self.cola = nuevo
            ref.sig = nuevo
        self.tam += 1
        return nuevo

    def agregar_al_final(self, estacion):
        return self.insertar_despues(self.cola, estacion)

    def eliminar(self, nodo):
        if nodo.ant is not None:
            nodo.ant.sig = nodo.sig
        else:
            self.cabeza = nodo.sig
        if nodo.sig is not None:
            nodo.sig.ant = nodo.ant
        else:
            self.cola = nodo.ant
        nodo.ant = nodo.sig = None
        self.tam -= 1

    def a_lista(self, al_reves=False):
        res = []
        n = self.cola if al_reves else self.cabeza
        while n is not None:
            res.append(n.estacion)
            n = n.ant if al_reves else n.sig
        return res
