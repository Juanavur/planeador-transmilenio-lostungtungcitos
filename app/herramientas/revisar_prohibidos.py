"""
Revisa que dentro de motor/ no se use nada prohibido por el enunciado:
dict, set, sorted, .sort(), min, max, `x in lista`, .index(), .count(),
bisect, heapq, collections, functools ni librerías externas.

    python app/herramientas/revisar_prohibidos.py

Es conservador: marca TODO `in`/`not in` que no sea un `for ... in`, aunque sea sobre un
texto, para que no haya discusión. Córranlo antes de cada commit.
"""

import ast
import os
import sys

PERMITIDOS = {"csv", "time", "random"}
FUNCIONES_PROHIBIDAS = {"dict", "set", "frozenset", "sorted", "min", "max"}
METODOS_PROHIBIDOS = {"sort", "index", "count"}


def revisar_archivo(ruta):
    problemas = []
    arbol = ast.parse(open(ruta, encoding="utf-8").read(), ruta)
    for nodo in ast.walk(arbol):
        linea = getattr(nodo, "lineno", 0)
        if isinstance(nodo, (ast.Dict, ast.DictComp)):
            problemas.append((linea, "dict literal / comprensión de dict"))
        elif isinstance(nodo, (ast.Set, ast.SetComp)):
            problemas.append((linea, "set literal / comprensión de set"))
        elif isinstance(nodo, ast.Call):
            f = nodo.func
            if isinstance(f, ast.Name) and f.id in FUNCIONES_PROHIBIDAS:
                problemas.append((linea, f.id + "()"))
            if isinstance(f, ast.Attribute) and f.attr in METODOS_PROHIBIDOS:
                problemas.append((linea, "." + f.attr + "()"))
            if any(isinstance(k, ast.keyword) and k.arg is None for k in nodo.keywords):
                problemas.append((linea, "**kwargs (crea un dict)"))
        elif isinstance(nodo, ast.Compare):
            for op in nodo.ops:
                if isinstance(op, (ast.In, ast.NotIn)):
                    problemas.append((linea, "operador in / not in"))
        elif isinstance(nodo, ast.Import):
            for a in nodo.names:
                if a.name.split(".")[0] not in PERMITIDOS:
                    problemas.append((linea, "import " + a.name))
        elif isinstance(nodo, ast.ImportFrom):
            if nodo.level == 0 and (nodo.module or "").split(".")[0] not in PERMITIDOS:
                problemas.append((linea, "from " + str(nodo.module) + " import ..."))
        elif isinstance(nodo, ast.FunctionDef) and nodo.args.kwarg is not None:
            problemas.append((linea, "**kwargs en la firma (crea un dict)"))
    return problemas


def main():
    raiz = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "motor")
    total = 0
    for carpeta, _, archivos in os.walk(raiz):
        for nombre in sorted(archivos):
            if nombre.endswith(".py"):
                ruta = os.path.join(carpeta, nombre)
                for linea, que in revisar_archivo(ruta):
                    print("%s:%d  %s" % (os.path.relpath(ruta), linea, que))
                    total += 1
    if total:
        print("\n%d problema(s). Un requisito con algo prohibido pierde resultados y rendimiento." % total)
        sys.exit(1)
    print("motor/ limpio: no usa nada prohibido.")


if __name__ == "__main__":
    main()
