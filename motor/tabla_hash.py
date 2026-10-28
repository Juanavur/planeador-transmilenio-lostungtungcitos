"""
Tabla hash propia (reemplaza a dict, que está prohibido en motor/).

Cómo funciona
-------------
- Un arreglo de "cubetas". Cada cubeta es None o una lista de pares [clave, valor]
  (encadenamiento separado: si dos claves caen en la misma cubeta, van en la misma lista).
- La cubeta de una clave sale de una función hash propia sobre los caracteres del texto.
- Cuando el factor de carga (elementos / cubetas) pasa de 0.75, se duplica el arreglo
  y se reubican todos los elementos (rehash). Eso mantiene las cubetas cortas.

Complejidad (n = número de elementos, L = largo de la clave)
-----------
- obtener / poner / eliminar / contiene: O(L) promedio, que para nombres de estación
  es O(1) respecto a n. Peor caso O(n) si todo colisiona (muy improbable).
- El rehash cuesta O(n), pero pasa cada vez que n se duplica, así que el costo
  amortizado por inserción sigue siendo O(1).
"""

_CARGA_MAXIMA = 0.75


def hash_texto(texto):
    """Hash polinomial (estilo FNV-1a) sobre los códigos de los caracteres."""
    h = 2166136261
    for c in texto:
        h = ((h ^ ord(c)) * 16777619) & 0xFFFFFFFF
    return h


class TablaHash:
    def __init__(self, capacidad=17):
        self._capacidad = capacidad
        self._cubetas = [None] * capacidad
        self._n = 0

    def __len__(self):
        return self._n

    # ------------------------------------------------------------------ internos
    def _indice(self, clave):
        return hash_texto(clave) % self._capacidad

    def _redimensionar(self):
        viejas = self._cubetas
        self._capacidad = self._capacidad * 2 + 1          # tamaño impar: reparte mejor
        self._cubetas = [None] * self._capacidad
        for cubeta in viejas:
            if cubeta is not None:
                for par in cubeta:
                    i = self._indice(par[0])
                    if self._cubetas[i] is None:
                        self._cubetas[i] = [par]
                    else:
                        self._cubetas[i].append(par)

    # ------------------------------------------------------------------ públicos
    def obtener(self, clave, defecto=None):
        cubeta = self._cubetas[self._indice(clave)]
        if cubeta is not None:
            for par in cubeta:
                if par[0] == clave:
                    return par[1]
        return defecto

    def contiene(self, clave):
        cubeta = self._cubetas[self._indice(clave)]
        if cubeta is not None:
            for par in cubeta:
                if par[0] == clave:
                    return True
        return False

    def poner(self, clave, valor):
        i = self._indice(clave)
        cubeta = self._cubetas[i]
        if cubeta is None:
            self._cubetas[i] = [[clave, valor]]
        else:
            for par in cubeta:
                if par[0] == clave:
                    par[1] = valor
                    return
            cubeta.append([clave, valor])
        self._n += 1
        if self._n > self._capacidad * _CARGA_MAXIMA:
            self._redimensionar()

    def eliminar(self, clave):
        """Quita la clave. Devuelve True si estaba."""
        i = self._indice(clave)
        cubeta = self._cubetas[i]
        if cubeta is None:
            return False
        for pos in range(len(cubeta)):
            if cubeta[pos][0] == clave:
                # se cambia por el último y se saca el último: O(1) dentro de la cubeta
                cubeta[pos] = cubeta[len(cubeta) - 1]
                cubeta.pop()
                if len(cubeta) == 0:
                    self._cubetas[i] = None
                self._n -= 1
                return True
        return False

    def pares(self):
        """Recorre todos los (clave, valor). O(n + capacidad) = O(n)."""
        for cubeta in self._cubetas:
            if cubeta is not None:
                for par in cubeta:
                    yield par[0], par[1]

    def valores(self):
        for cubeta in self._cubetas:
            if cubeta is not None:
                for par in cubeta:
                    yield par[1]
