"""
Ordenamiento y búsqueda propios (sorted, .sort, bisect, min y max están prohibidos).

- merge_sort: O(n log n) siempre, y es ESTABLE (si dos elementos empatan, conservan
  el orden en que venían). Se escogió sobre quicksort porque su peor caso también es
  O(n log n) y porque la estabilidad sirve para desempatar por nombre.
- primer_mayor_igual: búsqueda binaria, O(log n).
"""


def esta_ordenado(arr, menor):
    """O(n). Sirve para no ordenar lo que ya viene ordenado del CSV."""
    for i in range(1, len(arr)):
        if menor(arr[i], arr[i - 1]):
            return False
    return True


def merge_sort(arr, menor=None):
    """Devuelve una lista NUEVA ordenada. `menor(a, b)` dice si a va antes que b.
    Versión de abajo hacia arriba (sin recursión): mezcla bloques de 1, 2, 4, 8..."""
    if menor is None:
        def menor(a, b):
            return a < b
    n = len(arr)
    origen = list(arr)
    if n < 2:
        return origen
    destino = [None] * n
    ancho = 1
    while ancho < n:
        izq = 0
        while izq < n:
            mitad = izq + ancho
            if mitad > n:
                mitad = n
            der = izq + 2 * ancho
            if der > n:
                der = n
            i, j, k = izq, mitad, izq
            while i < mitad and j < der:
                if menor(origen[j], origen[i]):      # solo si j es estrictamente menor: estable
                    destino[k] = origen[j]
                    j += 1
                else:
                    destino[k] = origen[i]
                    i += 1
                k += 1
            while i < mitad:
                destino[k] = origen[i]
                i += 1
                k += 1
            while j < der:
                destino[k] = origen[j]
                j += 1
                k += 1
            izq = der
        origen, destino = destino, origen
        ancho *= 2
    return origen


def ordenar_si_hace_falta(arr, menor=None):
    if menor is None:
        def menor(a, b):
            return a < b
    if esta_ordenado(arr, menor):
        return arr
    return merge_sort(arr, menor)


def primer_mayor_igual(arr, x):
    """Índice del primer elemento >= x en un arreglo ordenado (len(arr) si no hay). O(log n)."""
    lo, hi = 0, len(arr)
    while lo < hi:
        mid = (lo + hi) // 2
        if arr[mid] < x:
            lo = mid + 1
        else:
            hi = mid
    return lo
