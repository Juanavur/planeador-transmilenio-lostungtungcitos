"""
Pruebas del motor con una red pequeña hecha a mano (app/pruebas/red_mini).

    python -m unittest discover -s app/pruebas -v

Red de prueba:
    R1: A -> B -> C -> D
    R2: C -> E -> F
    R3: A -> E
    R4: CALLE 26 -> CALLE 45 -> CALLE 80
"""

import os
import random
import sys
import unittest

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", ".."))

from motor import Red, simular_fila                         # noqa: E402
from motor.tabla_hash import TablaHash                      # noqa: E402
from motor.avl import AVL                                   # noqa: E402
from motor.ordenar import merge_sort, primer_mayor_igual    # noqa: E402

MINI = os.path.join(AQUI, "red_mini")


class TestEstructuras(unittest.TestCase):
    def test_tabla_hash_contra_dict(self):
        rnd = random.Random(1)
        t, d = TablaHash(), {}
        for _ in range(5000):
            k = "K%d" % rnd.randint(0, 800)
            if rnd.random() < 0.3:
                self.assertEqual(t.eliminar(k), k in d)
                d.pop(k, None)
            else:
                t.poner(k, k + "v")
                d[k] = k + "v"
        self.assertEqual(len(t), len(d))
        for k in d:
            self.assertEqual(t.obtener(k), d[k])
        self.assertEqual(sorted(t.pares()), sorted(d.items()))

    def test_avl_balanceado_y_ordenado(self):
        a = AVL()
        nombres = ["N%05d" % i for i in range(3000)]       # en orden: el peor caso de un BST normal
        for n in nombres:
            a.insertar(n, n)
        self.assertLessEqual(a.altura(), 18)                # 1.44 log2(3000) ~ 16.6
        self.assertEqual([c for c, _ in a.desde("N01000")][:3], ["N01000", "N01001", "N01002"])
        self.assertEqual([c for c, _ in a.desde("")], nombres)

    def test_merge_sort_estable(self):
        rnd = random.Random(2)
        datos = [(rnd.randint(0, 20), i) for i in range(500)]
        self.assertEqual(merge_sort(datos, lambda a, b: a[0] < b[0]),
                         sorted(datos, key=lambda x: x[0]))
        self.assertEqual(primer_mayor_igual([1, 3, 3, 5], 3), 1)
        self.assertEqual(primer_mayor_igual([1, 3, 3, 5], 6), 4)


class TestRed(unittest.TestCase):
    def setUp(self):
        self.red = Red(MINI)

    # R1
    def test_estado(self):
        self.assertEqual(self.red.estado("A"), (True, True))
        self.assertEqual(self.red.estado("Z"), (False, False))
        self.red.cerrar("A")
        self.assertEqual(self.red.estado("A"), (True, False))

    # R2
    def test_autocompletar(self):
        self.assertEqual(self.red.autocompletar("CALLE", 10),
                         ["CALLE 100", "CALLE 26", "CALLE 45", "CALLE 80"])
        self.assertEqual(self.red.autocompletar("CALLE", 2), ["CALLE 100", "CALLE 26"])
        self.red.cerrar("CALLE 100")
        self.assertEqual(self.red.autocompletar("CALLE", 2), ["CALLE 26", "CALLE 45"])
        self.assertEqual(self.red.autocompletar("X", 5), [])
        self.assertEqual(self.red.autocompletar("C", 0), [])

    # R3
    def test_rango(self):
        self.assertEqual(self.red.rango("CALLE 26", "CALLE 80"), ["CALLE 26", "CALLE 45", "CALLE 80"])
        self.red.cerrar("CALLE 45")
        self.assertEqual(self.red.rango("CALLE 26", "CALLE 80"), ["CALLE 26", "CALLE 80"])
        self.assertEqual(self.red.rango("Z", "A"), [])
        self.assertEqual(self.red.rango("B", "BZ"), ["B"])

    # R4
    def test_proximo_bus(self):
        self.assertEqual(self.red.proximo_bus("A", "R1", "05:30"), "06:00")
        self.assertEqual(self.red.proximo_bus("A", "R1", "06:00"), "06:00")   # justo a la hora
        self.assertEqual(self.red.proximo_bus("A", "R1", "08:00"), "05:00")   # día siguiente
        self.assertEqual(self.red.proximo_bus("C", "R2", "00:30"), "01:10")   # 25:10 -> 01:10
        self.assertIsNone(self.red.proximo_bus("D", "R1", "06:00"))            # sin horarios
        self.assertIsNone(self.red.proximo_bus("A", "R2", "06:00"))            # R2 no para en A
        self.red.cerrar("A")
        self.assertIsNone(self.red.proximo_bus("A", "R1", "05:30"))

    # R5
    def test_viaje(self):
        self.assertEqual(self.red.viaje("A", "D"), [("R1", "A", "D", 3)])
        self.assertEqual(self.red.viaje("A", "E"), [("R3", "A", "E", 1)])
        # A -> F: R1 hasta C (2) + R2 hasta F (2) = 4, contra R3 hasta E (1) + ... E no tiene ruta a F
        # salvo R2 desde E (1) -> R3 A->E (1) + R2 E->F (1) = 2
        self.assertEqual(self.red.viaje("A", "F"), [("R3", "A", "E", 1), ("R2", "E", "F", 1)])
        self.assertIsNone(self.red.viaje("D", "A"))                 # las rutas van en un sentido
        self.assertIsNone(self.red.viaje("A", "CALLE 80"))          # no hay conexión
        self.assertEqual(self.red.viaje("A", "A"), [])
        self.red.cerrar("E")                                         # ya no se transborda en E
        self.assertEqual(self.red.viaje("A", "F"), [("R1", "A", "C", 2), ("R2", "C", "F", 2)])
        self.red.cerrar("C")
        self.assertIsNone(self.red.viaje("A", "F"))
        self.assertEqual(self.red.viaje("A", "D"), [("R1", "A", "D", 3)])   # pasa por C sin parar

    # R6
    def test_ranking(self):
        # buses: A=4 (R1:3, R3:1), CALLE 26=4, C=3, E=2, B=1, CALLE 45=1
        self.assertEqual(self.red.ranking(3), ["A", "CALLE 26", "C"])
        self.red.cerrar("A")
        self.assertEqual(self.red.ranking(3), ["CALLE 26", "C", "E"])
        self.red.quitar_parada("R4", "CALLE 26")
        self.assertEqual(self.red.ranking(2), ["C", "E"])
        self.red.deshacer()
        self.assertEqual(self.red.ranking(1), ["CALLE 26"])
        self.assertEqual(self.red.ranking(0), [])

    # R7
    def test_editar_rutas(self):
        self.assertEqual(self.red.recorrido("R1"), ["A", "B", "C", "D"])
        self.assertEqual(self.red.recorrido("R1", al_reves=True), ["D", "C", "B", "A"])
        self.assertTrue(self.red.agregar_parada("R1", "E", "B"))
        self.assertEqual(self.red.recorrido("R1"), ["A", "B", "E", "C", "D"])
        self.assertTrue(self.red.agregar_parada("R1", "F", None))
        self.assertEqual(self.red.recorrido("R1"), ["F", "A", "B", "E", "C", "D"])
        self.assertTrue(self.red.agregar_parada("R1", "NUEVA", "D"))
        self.assertEqual(self.red.recorrido("R1")[-1], "NUEVA")
        self.assertEqual(self.red.estado("NUEVA"), (True, True))
        self.assertFalse(self.red.agregar_parada("R1", "A", "B"))      # ya está en la ruta
        self.assertFalse(self.red.agregar_parada("R1", "X", "Z"))      # despues_de no está
        self.assertFalse(self.red.agregar_parada("R9", "X", "A"))      # ruta no existe
        self.assertTrue(self.red.quitar_parada("R1", "C"))
        self.assertEqual(self.red.recorrido("R1"), ["F", "A", "B", "E", "D", "NUEVA"])
        self.assertFalse(self.red.quitar_parada("R1", "C"))
        self.assertIsNone(self.red.recorrido("R9"))
        # A -> E: ahora también por R1 (2 paradas), pero R3 sigue siendo mejor (1)
        self.assertEqual(self.red.viaje("A", "E"), [("R3", "A", "E", 1)])

    def test_quitar_parada_afecta_viaje_y_bus(self):
        self.red.quitar_parada("R1", "C")
        self.assertIsNone(self.red.proximo_bus("C", "R1", "06:00"))
        self.assertEqual(self.red.viaje("A", "D"), [("R1", "A", "D", 2)])

    # R9
    def test_deshacer_rehacer(self):
        self.red.cerrar("B")
        self.red.agregar_parada("R2", "NUEVA", "E")
        self.red.quitar_parada("R1", "A")
        self.assertTrue(self.red.deshacer())
        self.assertEqual(self.red.recorrido("R1"), ["A", "B", "C", "D"])
        self.assertTrue(self.red.deshacer())
        self.assertEqual(self.red.recorrido("R2"), ["C", "E", "F"])
        self.assertEqual(self.red.estado("NUEVA"), (False, False))      # se deshizo su creación
        self.assertEqual(self.red.autocompletar("NUE", 5), [])
        self.assertTrue(self.red.rehacer())
        self.assertEqual(self.red.recorrido("R2"), ["C", "E", "NUEVA", "F"])
        self.assertTrue(self.red.deshacer())
        self.assertTrue(self.red.deshacer())
        self.assertEqual(self.red.estado("B"), (True, True))
        self.assertFalse(self.red.deshacer())
        self.red.cerrar("D")                                             # cambio nuevo
        self.assertFalse(self.red.rehacer())                             # borró lo de rehacer
        self.assertTrue(self.red.deshacer())
        self.assertEqual(self.red.estado("D"), (True, True))

    def test_cambios_fallidos_no_se_registran(self):
        self.assertFalse(self.red.reabrir("A"))      # ya estaba abierta
        self.assertFalse(self.red.deshacer())


class TestFila(unittest.TestCase):
    def test_basico(self):
        self.assertEqual(simular_fila([0, 0, 1, 2, 2, 3, 10, 10, 11], 5, 2),
                         [0, 0, 4, 3, 8, 7, 5, 5, 9])

    def test_desordenado_y_vacio(self):
        self.assertEqual(simular_fila([3, 1, 2], 5, 1), [12, 4, 8])
        self.assertEqual(simular_fila([], 5, 1), [])

    def test_hueco_largo(self):
        self.assertEqual(simular_fila([0, 1000], 5, 10), [0, 0])

    def test_grande(self):
        rnd = random.Random(3)
        llegadas = sorted(rnd.randint(0, 3600) for _ in range(200000))
        esperas = simular_fila(llegadas, 60, 150)
        self.assertEqual(len(esperas), 200000)
        self.assertTrue(all(e >= 0 for e in esperas))


if __name__ == "__main__":
    unittest.main()
