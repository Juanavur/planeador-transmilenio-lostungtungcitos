# Planeador de viajes TransMilenio

Proyecto final de Estructuras de Datos y Algoritmos. Universidad de La Sabana.

Es una app para buscar estaciones, planear viajes y ver a qué hora pasa el bus, con la red
real de TransMilenio (GTFS de julio de 2021). Toda la lógica está en el paquete `motor/`,
escrito en Python puro con estructuras propias.

## Cómo arrancar

Requisito: Python 3.10 o superior.

```bash
python app/servidor.py
```

Ese es el **comando único**. No hay que instalar nada: la app usa solo la librería estándar
de Python (un servidor `http.server` y una página HTML con JavaScript, sin dependencias) y se
abre sola en http://localhost:8501. Ya trae los CSV generados en `datos/`.

Por qué no usamos Streamlit ni pandas en la app: en Windows con *Control inteligente de
aplicaciones* activado, esas librerías traen archivos `.dll` sin firmar que el sistema bloquea.
Sin dependencias, la app arranca en cualquier computador con Python.

La app tiene seis pestañas: **Estaciones** (R1–R3), **Viajar** (R4–R6), **Operar la red**
(R7–R9), **Fila de abordaje** (R10), **Rendimiento** (R11) y **Datos**, una tabla con las
estaciones, las rutas y los horarios que tiene cargados el motor, con búsqueda, orden por
columna y descarga en CSV.

Otros comandos útiles:

```bash
python -m unittest discover -s app/pruebas -v           # pruebas del motor
python app/herramientas/revisar_prohibidos.py           # verifica que motor/ no use nada prohibido
python app/herramientas/medir.py 1000 2000 4000 8000    # rendimiento por consola (lo mismo que el panel)
python datos/convertir_gtfs.py gtfs.zip                 # regenerar los CSV desde el GTFS (necesita pandas)
```

## Contrato del motor

El script de pruebas hace `from motor import Red, simular_fila` y llama exactamente esto:

| Llamada | Req. | Devuelve |
|---|---|---|
| `Red(carpeta)` | carga | lee `estaciones.csv`, `rutas.csv` y `horarios.csv` de la carpeta |
| `red.estado(nombre)` | R1 | `(existe, abierta)`, dos booleanos |
| `red.autocompletar(prefijo, k)` | R2 | lista de hasta k nombres abiertos, en orden alfabético |
| `red.rango(desde, hasta)` | R3 | lista de nombres abiertos entre los dos, incluidos, en orden alfabético |
| `red.proximo_bus(estacion, ruta, hora)` | R4 | `"HH:MM"` del siguiente bus (el primero del día siguiente si ya no hay), o `None` |
| `red.viaje(origen, destino)` | R5 | lista de tramos `(ruta, sube_en, baja_en, paradas)`: uno si es directo, dos con transbordo; `[]` si origen = destino; `None` si no hay viaje |
| `red.ranking(k)` | R6 | lista de las k estaciones abiertas con más buses al día (empates: alfabético) |
| `red.agregar_parada(ruta, nueva, despues_de)` | R7 | `True` si se hizo (`despues_de=None` la pone al inicio) |
| `red.quitar_parada(ruta, estacion)` | R7 | `True` si se hizo |
| `red.recorrido(ruta, al_reves=False)` | R7 | lista de estaciones en su sentido o al revés, o `None` si la ruta no existe |
| `red.cerrar(nombre)`, `red.reabrir(nombre)` | R8 | `True` si cambió algo |
| `red.deshacer()`, `red.rehacer()` | R9 | `True` si había algo que deshacer o rehacer |
| `simular_fila(llegadas, frecuencia, capacidad)` | R10 | lista con la espera de cada pasajero, en el orden de `llegadas` |

Si el enunciado pide otro formato de retorno, se cambia solo la última línea de cada
método en `motor/red.py`; las estructuras no cambian.

## Entregables (diapositiva 13)

| Pide el profesor | Dónde está |
|---|---|
| El paquete `motor/` con el contrato completo | `motor/` |
| El front, web o de escritorio | `app/` (web: `python app/servidor.py`) |
| El script del GTFS a los tres CSV, y los CSV ya generados | `datos/convertir_gtfs.py` y `datos/*.csv` |
| README.md con las decisiones (R12) y el comando único | este archivo |
| integrantes.md con los nombres y qué requisitos hizo cada uno | `integrantes.md` |
| Git desde la primera semana, con commits de todos | el historial del repositorio |

## Estructura del repositorio

```
motor/                     ← todo lo que resuelve requisitos (solo list, str, csv, time, random)
  __init__.py              from motor import Red, simular_fila
  red.py                   clase Red: R1 a R9
  fila.py                  simular_fila: R10
  tabla_hash.py            tabla hash propia (reemplaza dict)
  avl.py                   árbol AVL (orden alfabético)
  lista_doble.py           lista doblemente enlazada (recorrido de cada ruta)
  pila_cola.py             pila (deshacer/rehacer) y cola circular (fila)
  ordenar.py               merge sort y búsqueda binaria propios
  horas.py                 "HH:MM" <-> minutos
app/                       ← el front (solo llama al motor)
  servidor.py              servidor web con solo librería estándar: traduce peticiones a llamadas del motor
  index.html               la página: pestañas, tabla de datos, gráficas SVG y panel de rendimiento (R11)
  herramientas/            generador de redes sintéticas, medición, revisor de prohibidos
  pruebas/                 pruebas del motor con una red pequeña hecha a mano
datos/                     ← la conversión y los datos
  convertir_gtfs.py        script GTFS -> 3 CSV (con pandas)
  estaciones.csv           nombre
  rutas.csv                ruta, orden, estacion
  horarios.csv             ruta, estacion, hora
README.md                  este archivo (decisiones R12 + comando para arrancar)
integrantes.md             quién hizo qué requisito
```

---

## R12 · Decisiones

**Notación:** n = estaciones de la red · m = paradas de una ruta · h = veces que una ruta pasa
por una estación en el día · k = resultados pedidos · P = pasajeros · L = largo de una clave (texto).

### Estructuras base (las usan varios requisitos)

| Estructura | Archivo | Operaciones y costo |
|---|---|---|
| Tabla hash con encadenamiento y rehash al 75 % | `tabla_hash.py` | obtener / poner / eliminar: **O(1) promedio** (O(L) por calcular el hash; los nombres son cortos). El rehash es O(n), pero solo ocurre cuando n se duplica, así que amortizado sigue siendo O(1) |
| Árbol AVL | `avl.py` | insertar / buscar O(log n); recorrer m nombres desde uno dado: O(log n + m) |
| Lista doblemente enlazada | `lista_doble.py` | insertar después de un nodo / eliminar nodo O(1); recorrer O(m) |
| Pila con nodos | `pila_cola.py` | apilar / desapilar / vaciar O(1) |
| Cola con arreglo circular | `pila_cola.py` | encolar / desencolar O(1) amortizado |
| Merge sort de abajo hacia arriba | `ordenar.py` | O(n log n) siempre y estable |
| Búsqueda binaria (primer ≥ x) | `ordenar.py` | O(log n) |

### Por requisito

#### R1 · Buscar una estación (`estado`)
- **Estructura:** tabla hash de nombre a `Estacion`. Cada estación tiene las banderas `abierta` y `existe`.
- **Algoritmo:** una consulta a la tabla. Devuelve `(existe, abierta)`.
- **O grande:** O(1) promedio, con n = estaciones.
- **Descartada:** búsqueda binaria en un arreglo ordenado o en el AVL, que cuesta O(log n). Como es la consulta que más se usa en la app, se escogió la opción que no crece con n. El orden alfabético ya lo da el AVL para R2 y R3.

#### R2 · Autocompletar (`autocompletar(prefijo, k)`)
- **Estructura:** AVL ordenado por nombre.
- **Algoritmo:** todos los nombres que empiezan por el prefijo P son ≥ P y quedan seguidos en orden alfabético. Se baja hasta el primer nombre ≥ P, que cuesta O(log n). Desde ahí se recorre en inorden con pila explícita y se para cuando hay k estaciones abiertas o cuando un nombre ya no empieza por P.
- **O grande:** O(log n + k + c), donde c = estaciones cerradas que se saltan dentro del prefijo.
- **Descartadas:**
  - Trie: es bueno para prefijos, pero no resuelve R3 y gasta mucha más memoria (un nodo por letra).
  - Arreglo ordenado con búsqueda binaria: daría lo mismo, pero `agregar_parada` puede crear estaciones nuevas, y meterlas en un arreglo ordenado cuesta O(n). En el AVL cuesta O(log n).

#### R3 · Listar un rango (`rango(desde, hasta)`)
- **Estructura:** el mismo AVL.
- **Algoritmo:** se arranca en el primer nombre ≥ `desde` y se recorre en inorden hasta pasar `hasta`, saltando las cerradas. El rango incluye los dos extremos. Si `desde > hasta`, devuelve `[]`.
- **O grande:** O(log n + m), con m = estaciones dentro del rango.
- **Descartada:** recorrer todas las estaciones y filtrar, que cuesta O(n) aunque el rango sea pequeño.

#### R4 · Próximo bus (`proximo_bus(estacion, ruta, hora)`)
- **Estructura:** tabla hash con clave compuesta `"RUTA|ESTACION"` que guarda un arreglo de minutos ordenado. Se ordena una sola vez al cargar, con merge sort, y solo si no viene ordenado.
- **Algoritmo:** búsqueda binaria del primer horario ≥ hora. Si ya no hay más buses ese día, devuelve el primero del día siguiente. Devuelve `"HH:MM"`, o `None` si la estación está cerrada, la ruta no para ahí o no tiene horarios.
- **O grande:** O(log h). No depende de n.
- **Descartada:** recorrer el arreglo, que cuesta O(h). Las troncales pasan cientos de veces al día; en los datos reales h llega a 375.

#### R5 · Planear un viaje (`viaje(origen, destino)`)
- **Estructuras:** las listas dobles de las rutas, más una tabla hash temporal.
- **Algoritmo:** combina dos recorridos, porque no hay un algoritmo del curso que lo haga tal cual.
  1. **Desde el destino, hacia atrás:** por cada ruta que para en el destino, se camina por los punteros `ant`. En una tabla hash se anota cada estación abierta T con cuántas paradas le faltan para llegar al destino y por qué ruta. Es como un BFS de un solo nivel hacia atrás.
  2. **Desde el origen, hacia adelante:** por cada ruta que para en el origen, se camina por `sig` contando paradas j. Si se llega al destino, hay un viaje directo. Si se pasa por una T de la tabla y la ruta es otra, hay un transbordo con total = j + paradas anotadas.
  3. Gana el que tenga menos paradas. Si empatan, gana el directo, y después se desempata por nombre de ruta.
- **Formato:** `[(ruta, sube_en, baja_en, paradas)]` para un directo, o dos tramos con transbordo. Devuelve `[]` si origen = destino y `None` si no hay viaje.
- **Regla con estaciones cerradas:** no se sube, baja ni transborda en una estación cerrada. Si el bus pasa por una cerrada, igual cuenta como parada recorrida, porque el bus pasa por ahí aunque no pare.
- **O grande:** O(L_o + L_d), la suma de las longitudes de las rutas que pasan por el origen y por el destino. No depende de n.
- **Descartada:** BFS sobre toda la red con estados (estación, ruta). Es más general, pero cuesta más y limitarlo a un solo transbordo es más difícil. **Si piden dos transbordos, ese sería el camino.**

#### R6 · Ranking (`ranking(k)`)
- **Estructura:** un arreglo de estaciones ordenado por buses al día de mayor a menor (empates en orden alfabético), guardado como cache con una bandera de "sucio".
- **Algoritmo:** la consulta recorre el arreglo desde el inicio, salta las cerradas y para al juntar k. Cerrar o reabrir **no** obliga a reordenar, porque las cerradas solo se saltan. Agregar o quitar paradas, y deshacerlo, cambia los conteos y marca el cache como sucio; la siguiente consulta lo reconstruye con merge sort.
- **Buses al día:** filas de `horarios.csv` de esa estación, sumando solo las rutas que hoy paran ahí. Se actualiza en O(1) al agregar o quitar paradas.
- **O grande:** consulta O(k + c); reconstrucción O(n log n), solo después de una edición.
- **Descartada:** construir un heap en cada consulta, O(n + k log n). El enunciado dice que se consulta muy seguido y cambia poco, así que conviene pagar el orden una vez y dejar la consulta en O(k).

#### R7 · Editar rutas (`agregar_parada`, `quitar_parada`, `recorrido`)
- **Estructura:** cada ruta es una lista doblemente enlazada más una tabla hash de estación a nodo.
- **Algoritmo:** la tabla da el nodo de `despues_de` en O(1) y se reconectan cuatro punteros. Para quitar, se busca el nodo y se reconectan sus vecinos. `recorrido` sigue `sig`, o `ant` si `al_reves=True`.
- **Reglas:**
  - `despues_de=None` pone la parada al inicio.
  - Si `nueva` no existía como estación, se crea y entra al AVL en O(log n).
  - Devuelve `False` si la ruta no existe, si la estación ya está en la ruta o si `despues_de` no está.
- **O grande:** agregar y quitar O(1) (O(log n) solo si se crea una estación); recorrido O(m).
- **Descartada:** `list` de Python con `insert` o `pop(i)`, que cuesta O(m) por edición porque corre los elementos. Los operadores editan todo el tiempo.

#### R8 · Cerrar y reabrir (`cerrar`, `reabrir`)
- **Estructura:** la bandera `abierta` de cada `Estacion`, que se encuentra con la tabla hash.
- **Algoritmo:** cambiar la bandera. Todos los requisitos preguntan por `visible()` antes de usar una estación, así que la cerrada desaparece de búsquedas, autocompletado, rangos, ranking y viajes sin mover nada. Devuelve `False` si no había nada que cambiar; ese caso no se registra para deshacer.
- **O grande:** O(1).
- **Descartada:** sacar la estación de las estructuras y volverla a meter. Sería O(log n) en el AVL, obligaría a reordenar el ranking y complicaría deshacer.

#### R9 · Deshacer y rehacer (`deshacer`, `rehacer`)
- **Estructura:** dos pilas de "cambios" (patrón *command*). Cada cambio guarda lo necesario para revertirse:
  - `cerrar` ↔ `reabrir`;
  - `agregar` guarda si creó la estación;
  - `quitar` guarda cuál era la parada anterior, para volver a ponerla en el mismo sitio.
- **Algoritmo:** deshacer saca el cambio de la pila de deshacer, aplica su inverso y lo pasa a la pila de rehacer. Rehacer hace lo contrario. Todo cambio nuevo vacía la pila de rehacer en O(1). Si se deshace la creación de una estación, queda con `existe=False` y deja de aparecer en todo.
- **O grande:** O(1) por operación (O(log n) si se recrea una estación).
- **Descartada:** guardar copias de toda la red en cada cambio. Funciona, pero cuesta O(n) en tiempo y memoria por cambio.

#### R10 · Fila de abordaje (`simular_fila(llegadas, frecuencia, capacidad)`)
- **Estructura:** cola FIFO con arreglo circular.
- **Algoritmo:** los buses salen en 0, f, 2f, … En cada salida se encolan los que ya llegaron y se suben hasta `capacidad` en orden de llegada. Si dos llegan al mismo tiempo, sube primero el que aparece antes en la lista. Quien llega justo a la hora del bus alcanza a subirse. Cuando la fila está vacía, se salta directo al bus de la siguiente llegada, sin simular buses vacíos. Devuelve `esperas[i]`, lo que esperó el pasajero i.
- **O grande:** O(P + B), con B = buses que salen con gente. Si `llegadas` viene desordenada, se ordena primero: O(P log P).
- **Descartadas:**
  - `list.pop(0)`: cada pop es O(P), así que la simulación sería O(P²).
  - Cola con nodos enlazados: en la teoría también es O(1), pero en la medición crecía más que lineal con cientos de miles de pasajeros, porque crear un objeto por pasajero hace trabajar de más al recolector de basura de Python. El arreglo circular solo guarda números.

---

## R11 · Panel de rendimiento

La pestaña **📈 Rendimiento** de la app genera redes sintéticas de tamaño n, 2n, 4n, …
(`app/herramientas/generar_red.py`), corre cada operación cientos de veces y grafica el tiempo
medido junto a la curva esperada (anclada en el punto más grande). Al lado compara la última
duplicación, de n a 2n, que es el mismo método del script del profesor, y dice si coincide,
con la explicación.

Mediciones de referencia, en microsegundos por llamada, con n de 2 000 a 32 000:

| Operación | Esperado | n=2000 | n=8000 | n=32000 | ¿Coincide? |
|---|---|---|---|---|---|
| R1 estado | O(1) | 2.1 | 3.4 | 3.3 | Sí. Sube un poco de 2 000 a 8 000 por la memoria caché del procesador; después se estabiliza |
| R2 autocompletar k=10 | O(log n + k) | 3.6 | 4.5 | 3.9 | Sí |
| R3 rango (~10 resultados) | O(log n + m) | 4.0 | 11.3 | 10.5 | Sí. Mismo efecto de caché: un árbol más grande no cabe en la caché |
| R4 próximo bus | O(log h) | 12.6 | 16.4 | 15.8 | Sí. h no crece con n |
| R6 ranking k=10 | O(k) | 1.1 | 1.1 | 1.2 | Sí |
| R7 agregar + quitar | O(1) | 30.8 | 33.8 | 34.4 | Sí |
| R8 cerrar + reabrir | O(1) | 11.4 | 6.0 | 6.4 | Sí. El primer punto incluye calentamiento |
| R9 deshacer + rehacer | O(1) | 10.5 | 4.0 | 5.4 | Sí |
| R10 fila (50n pasajeros) | O(P) | 216 716 | 856 058 | 2 471 211 | Sí. Al duplicar P el tiempo se duplica aproximadamente |

**Por qué una O(1) no da una línea perfectamente plana:** con redes más grandes los datos no
caben en la memoria caché del procesador, y cada acceso tarda un poco más. Ese costo no viene
del algoritmo: se estabiliza en vez de seguir creciendo. Si el algoritmo fuera O(n), al duplicar
n el tiempo se duplicaría siempre.

---

## Datos: del GTFS a los tres CSV

`datos/convertir_gtfs.py` usa pandas, que está permitido fuera del motor. Decisiones:

Fuente: GTFS estático de TransMilenio del 14 de julio de 2021 ([datos abiertos de movilidad de Bogotá](https://datos.movilidadbogota.gov.co/datasets/6def68cda70c43ab8d93d74f43c5915a/about)).

1. **Solo el sistema troncal** por defecto (`route_desc == TRONCAL`). Así quedan 124 estaciones, 89 rutas y unas 95 000 pasadas al día. Con `--todo` se agregan alimentadores y SITP: 6 403 paradas y 2,3 millones de horarios. El motor carga esa red en unos 7 s.
2. **Vagones → estación.** En el GTFS una estación aparece como varios stops (por ejemplo "Calle 85 B - 4 ó 6" o "Portal 80 T-1A"). Se quita el sufijo de vagón o plataforma y quedan unidas, para que un transbordo dentro de la misma estación funcione.
3. **Nombres** en mayúsculas, sin tildes (Ñ → N), sin espacios dobles y sin repetidos. Fuera del troncal, cada parada conserva su código para no fusionar paradas lejanas que se llaman igual.
4. **Un solo día de servicio.** Se usa lunes, un día hábil, para que "buses al día" sea un día de verdad y no la suma de lunes, sábado y domingo. Se puede cambiar con `--dia`.
5. **Cada ruta va en un solo sentido.** En TransMilenio cada `route_id` ya va en un sentido (B74 va al norte y J74 al sur). El orden de paradas es el patrón más frecuente entre sus viajes; si hay empate, el más largo. Una estación repetida dentro de la ruta se deja solo la primera vez.
6. **Horas como 25:10.** Se pasan a la hora real del reloj con módulo 24 (25:10 → 01:10) y se truncan a minutos. Por eso, en R4, si ya no hay buses ese día, se devuelve el primero del día siguiente. El motor también aplica el módulo por si la red del profesor trae horas así.

## Reglas del motor

Dentro de `motor/` solo se usan `list` (como arreglo), `str`, `csv`, `time` y `random`. No se
usan `dict`, `set`, `sorted`, `.sort()`, `min`, `max`, `x in lista`, `.index()`, `.count()`,
`bisect`, `heapq`, `collections`, `functools` ni `os`. El revisor
`app/herramientas/revisar_prohibidos.py` lo comprueba con el árbol sintáctico de Python, y es más
estricto que la regla: también marca `in` sobre textos.

Ninguna regla del sistema está en el front. La app solo llama al motor; lo único que hace por
su cuenta es pasar a mayúsculas lo que escribe la persona.
