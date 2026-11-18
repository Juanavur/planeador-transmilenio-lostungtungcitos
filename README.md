# Planeador de viajes TransMilenio

Proyecto final de Estructuras de Datos y Algoritmos. Universidad de La Sabana. Equipo Los Tungtungcitos.

Es una app para buscar estaciones, planear viajes y ver a qué hora pasa el bus, con la red real de TransMilenio (GTFS de julio de 2021). Toda la lógica está en el paquete `motor/`, escrito en Python puro con estructuras propias.

## App desplegada

[https://planeador-transmilenio-lostungtungcitos.onrender.com/](https://planeador-transmilenio-lostungtungcitos.onrender.com/)

*(Nota: al estar en el plan gratuito de Render, si lleva un rato sin usarse puede tardar unos 30–50 segundos en despertar la primera vez que se abre).*

En Render la configuración es: build command `echo "Listo"` y start command `python app/servidor.py`. El servidor detecta la variable `PORT`; cuando existe, escucha en `0.0.0.0` y no abre el navegador. En local sigue usando `127.0.0.1:8501`.

## Cómo arrancar en local

Requisito: Python 3.10 o superior.

```bash
python app/servidor.py
```

Ese es el **comando único**. No hay que instalar nada: la app usa solo la librería estándar de Python (un servidor `http.server` y una página HTML con JavaScript, sin dependencias) y se abre sola en http://localhost:8501. Ya trae los CSV generados en `datos/`.

Por qué no usamos Streamlit ni pandas en la app: en Windows con *Control inteligente de aplicaciones* activado, esas librerías traen archivos `.dll` sin firmar que el sistema bloquea. Sin dependencias, la app arranca en cualquier computador con Python.

La app tiene siete pestañas: **Viajar** (R4–R6), **Mapa** (la red vista desde arriba, con la posición real de cada estación), **Estaciones** (R1–R3), **Operar la red** (R7–R9), **Hora pico** (R10), **Rendimiento** (R11) y **Datos**, una tabla con las estaciones, las rutas y los horarios que tiene cargados el motor, con búsqueda, orden por columna y descarga en CSV.

Otros comandos útiles:

```bash
python -m unittest discover -s app/pruebas -v            # pruebas del motor
python app/herramientas/revisar_prohibidos.py            # verifica que motor/ no use nada prohibido
python app/herramientas/medir.py 1000 2000 4000 8000     # rendimiento por consola (lo mismo que el panel)
python app/herramientas/pendientes.py 10000 20000 40000 80000   # medianas y pendientes con los tamaños de la rúbrica (~2 min)
python datos/convertir_gtfs.py gtfs.zip                  # regenerar los CSV desde el GTFS (necesita pandas)
```

## Contrato del motor

El script de pruebas hace `from motor import Red, simular_fila` y llama exactamente esto:

| Llamada | Req. | Devuelve |
|---|---|---|
| `Red(carpeta)` | carga | lee `estaciones.csv`, `rutas.csv` y `horarios.csv` de la carpeta (todas las estaciones abiertas) |
| `red.estado(nombre)` | R1 | `"ABIERTA"`, `"CERRADA"` o `"NO EXISTE"` |
| `red.autocompletar(prefijo, k)` | R2 | lista de hasta `k` estaciones abiertas que empiezan por `prefijo`, en orden alfabético (`[]` si no hay) |
| `red.rango(desde, hasta)` | R3 | lista de estaciones abiertas entre los dos nombres (inclusive), en orden alfabético |
| `red.proximo_bus(estacion, ruta, hora)` | R4 | `"HH:MM"` del siguiente bus de esa ruta en esa estación, o `None` si no hay más ese día |
| `red.viaje(origen, destino)` | R5 | lista de tramos `(ruta, sube_en, baja_en)`: 1 tramo si es directo, 2 si hay transbordo; el viaje con menos paradas (`[]` si `origen == destino`, `None` si no hay viaje) |
| `red.ranking(k)` | R6 | lista de `(nombre, buses_por_dia)` de las `k` estaciones abiertas con más buses, de mayor a menor |
| `red.agregar_parada(ruta, nueva, despues_de)` | R7 | `True` si la agregó justo después de `despues_de` (`None` al inicio), `False` si no se pudo |
| `red.quitar_parada(ruta, estacion)` | R7 | `True` si la quitó, `False` si no estaba |
| `red.recorrido(ruta, al_reves=False)` | R7 | lista de nombres en orden (`[]` si la ruta no existe) |
| `red.cerrar(nombre)`, `red.reabrir(nombre)` | R8 | `True` si cambió el estado, `False` si no existe o ya estaba así |
| `red.deshacer()`, `red.rehacer()` | R9 | `True` si deshizo o rehizo algo, `False` si no había nada |
| `simular_fila(llegadas, frecuencia, capacidad)` | R10 | lista con el segundo en que salió el bus de cada persona, en el mismo orden de `llegadas` |

## Entregables (diapositiva 13)

| Pide el profesor | Dónde está |
|---|---|
| El paquete `motor/` con el contrato completo | `motor/` |
| El front, web o de escritorio | `app/` (local: `python app/servidor.py` · web: [Render](https://planeador-transmilenio-lostungtungcitos.onrender.com/)) |
| El script del GTFS a los tres CSV, y los CSV ya generados | `datos/convertir_gtfs.py` y `datos/*.csv` |
| README.md con las decisiones (R12) y el comando único | este archivo |
| integrantes.md con los nombres y qué requisitos hizo cada uno | `integrantes.md` |
| Git desde la primera semana, con commits de todos | el historial del repositorio |

## Estructura del repositorio

```text
motor/                      ← todo lo que resuelve requisitos (solo list, str, csv, time, random)
  __init__.py               from motor import Red, simular_fila
  red.py                    clase Red: R1 a R9
  fila.py                   simular_fila: R10
  tabla_hash.py             tabla hash propia (reemplaza dict)
  avl.py                    árbol AVL (orden alfabético)
  lista_doble.py            lista doblemente enlazada (recorrido de cada ruta)
  pila_cola.py              pila (deshacer/rehacer) y cola circular (fila)
  ordenar.py                merge sort y búsqueda binaria propios
  horas.py                  "HH:MM" <-> minutos
app/                        ← el front (solo llama al motor)
  servidor.py               servidor web con solo librería estándar: traduce peticiones a llamadas del motor
  fondo_mapa.jpg            fondo del mapa (© colaboradores de OpenStreetMap)
  icono.png                 ícono de la app (pestaña del navegador y vista previa al compartir el link)
  index.html                la página: pestañas, tabla de datos, gráficas SVG y panel de rendimiento (R11)
  herramientas/             generador de redes sintéticas, medición, revisor de prohibidos
  pruebas/                  pruebas del motor con una red pequeña hecha a mano
datos/                      ← la conversión y los datos
  convertir_gtfs.py         script GTFS -> 3 CSV (con pandas)
  estaciones.csv            nombre
  rutas.csv                 ruta, orden, estacion
  horarios.csv              ruta, estacion, hora
  coordenadas.csv           estacion, lat, lon (solo para dibujar el mapa; el motor no lo lee)
README.md                   este archivo (decisiones R12 + comando para arrancar)
integrantes.md              quién hizo qué requisito
```

---

## R12 · Decisiones

**Notación:** $n$ = número total de estaciones de la red · $m$ = paradas de una ruta (o estaciones dentro de un rango en R3) · $h$ = pasadas al día de una ruta por una estación · $k$ = cantidad de resultados pedidos · $P$ = pasajeros en la simulación · $L$ = largo de una clave de texto.

### Estructuras base (las usan varios requisitos)

| Estructura | Archivo | Operaciones y costo |
|---|---|---|
| Tabla hash con encadenamiento y rehash al 75 % | `tabla_hash.py` | obtener / poner / eliminar: **$O(1)$ promedio** ($O(L)$ por calcular el hash; los nombres son cortos). El rehash es $O(n)$, pero solo ocurre cuando $n$ se duplica, así que amortizado sigue siendo $O(1)$. |
| Árbol AVL | `avl.py` | insertar / buscar $O(\log n)$; recorrer $m$ nombres desde uno dado: $O(\log n + m)$. |
| Lista doblemente enlazada | `lista_doble.py` | insertar después de un nodo / eliminar nodo $O(1)$; recorrer $O(m)$. |
| Pila con nodos | `pila_cola.py` | apilar / desapilar / vaciar $O(1)$. |
| Cola con arreglo circular | `pila_cola.py` | encolar / desencolar $O(1)$ amortizado. |
| Merge sort de abajo hacia arriba | `ordenar.py` | $O(n \log n)$ siempre y estable. |
| Búsqueda binaria (primer ≥ x) | `ordenar.py` | $O(\log n)$. |

### Por requisito

#### R1 · Buscar una estación (`estado(nombre)`)
- **Estructura:** tabla hash de nombre a `Estacion`. Cada estación tiene las banderas `abierta` y `existe`.
- **Algoritmo:** una consulta directa a la tabla hash. Devuelve `"ABIERTA"`, `"CERRADA"` o `"NO EXISTE"`.
- **O grande:** $O(1)$ promedio, donde $n$ = total de estaciones de la red.
- **Descartada:** búsqueda binaria en un arreglo ordenado o en el AVL, que cuesta $O(\log n)$. Como es la consulta más frecuente de la app, se escogió la opción constante respecto a $n$. El orden alfabético ya lo mantiene el AVL para R2 y R3.

#### R2 · Autocompletar (`autocompletar(prefijo, k)`)
- **Estructura:** AVL ordenado por nombre.
- **Algoritmo:** todos los nombres que empiezan por el prefijo son $\ge$ al prefijo y quedan contiguos en orden alfabético. Se baja hasta el primer nombre $\ge$ prefijo, que cuesta $O(\log n)$. Desde ahí se recorre en inorden con pila explícita y se detiene al reunir $k$ estaciones abiertas o cuando un nombre ya no empieza por el prefijo.
- **O grande:** $O(\log n + k + c)$, donde $n$ = total de estaciones de la red, $k$ = resultados pedidos y $c$ = estaciones cerradas que se saltan dentro del prefijo.
- **Descartadas:**
  - Trie: es rápido para prefijos, pero no resuelve rangos (R3) de forma directa y consume mucha más memoria (un nodo por carácter).
  - Arreglo ordenado con búsqueda binaria: daría el mismo tiempo de consulta, pero `agregar_parada` puede crear estaciones nuevas, y mantener el arreglo ordenado costaría $O(n)$ por inserción. En el AVL cuesta $O(\log n)$.

#### R3 · Listar un rango (`rango(desde, hasta)`)
- **Estructura:** el mismo AVL ordenado por nombre.
- **Algoritmo:** se ubica el primer nodo $\ge$ `desde` en $O(\log n)$ y se avanza en recorrido inorden hasta superar `hasta`, filtrando las estaciones cerradas. Incluye ambos extremos y devuelve `[]` si `desde > hasta`.
- **O grande:** $O(\log n + m)$, donde $n$ = total de estaciones de la red y $m$ = estaciones dentro del intervalo `[desde, hasta]`.
- **Descartada:** recorrer todas las estaciones y filtrar, que cuesta $O(n)$ incluso cuando el rango es pequeño.

#### R4 · Próximo bus (`proximo_bus(estacion, ruta, hora)`)
- **Estructura:** tabla hash con clave compuesta `"RUTA|ESTACION"` que guarda un arreglo ordenado de minutos desde medianoche. Se ordena una sola vez al cargar con merge sort (solo si no viene ordenado del CSV).
- **Algoritmo:** búsqueda binaria (`primer_mayor_igual`) del primer horario $\ge$ `hora`. Si no hay más buses ese día (o si la estación está cerrada/no existe o la ruta no pasa por ahí), devuelve `None`.
- **O grande:** $O(\log h)$, donde $h$ = pasadas al día de esa ruta en esa estación (independiente del total $n$ de estaciones de la red).
- **Descartada:** búsqueda lineal sobre los horarios, que cuesta $O(h)$. Las rutas troncales pasan cientos de veces al día (en los datos reales $h$ llega a 375).

#### R5 · Planear un viaje (`viaje(origen, destino)`)
- **Estructuras:** listas doblemente enlazadas de las rutas más una tabla hash temporal de estaciones de transbordo.
- **Algoritmo:** búsqueda bidireccional acotada a máximo 1 transbordo. Se combinan dos recorridos porque ningún algoritmo del curso resuelve esto tal cual:
  1. **Desde el destino, hacia atrás:** por cada ruta que pasa por `destino`, se recorren los punteros `ant`. En una tabla hash se registra cada estación abierta $T$ con la menor cantidad de paradas hasta `destino` y su ruta asociada. Es como un BFS de un solo nivel hacia atrás.
  2. **Desde el origen, hacia adelante:** por cada ruta que pasa por `origen`, se recorren los punteros `sig` contando paradas $j$. Si se alcanza `destino`, se evalúa como viaje directo (1 tramo). Si se pasa por una estación $T$ presente en la tabla con otra ruta, se evalúa como viaje con transbordo (2 tramos) con costo total $j + \text{paradas}(T \to \text{destino})$.
  3. Se elige el candidato con menor número total de paradas; en caso de empate, se prefiere el directo (1 tramo) y luego el orden alfabético de los nombres de ruta.
- **Formato:** `[(ruta, sube_en, baja_en)]` para directo, o dos tuplas para transbordo. Devuelve `[]` si `origen == destino` y `None` si alguna estación está cerrada/no existe o no hay viaje.
- **Regla con estaciones cerradas:** no se aborda, desciende ni transborda en una estación cerrada, aunque el bus sí la atraviesa y cuenta en el total de paradas recorridas.
- **O grande:** $O(L_o + L_d)$, donde $L_o$ y $L_d$ son las sumas de paradas de las rutas que pasan por `origen` y `destino` (no depende del total $n$ de estaciones de la red).
- **Descartada:** BFS general sobre el grafo completo de estados `(estación, ruta)`, que es más costoso cuando solo se permiten 0 o 1 transbordos. **Si piden dos transbordos, ese sería el camino.**

#### R6 · Ranking (`ranking(k)`)
- **Estructura:** arreglo cacheado de estaciones ordenadas de mayor a menor por `buses_por_dia` (desempate alfabético), acompañado de una bandera `_ranking_sucio`.
- **Algoritmo:** `ranking(k)` lee desde el inicio del arreglo saltando estaciones cerradas hasta completar $k$ tuplas `(nombre, buses_por_dia)`. Cerrar o reabrir estaciones (R8) no altera el orden relativo ni obliga a reordenar. Solo `agregar_parada` o `quitar_parada` (y su deshacer/rehacer) modifican los conteos y marcan el caché como sucio para reconstruirlo con merge sort en la siguiente consulta.
- **Buses al día:** son las filas de `horarios.csv` de esa estación, sumando solo las rutas que hoy paran ahí. Se actualiza en $O(1)$ al agregar o quitar paradas.
- **O grande:** consulta $O(k + c)$ (donde $c$ = estaciones cerradas saltadas al inicio, independiente de $n$); reconstrucción tras ediciones $O(n \log n)$, donde $n$ = total de estaciones de la red.
- **Descartada:** reconstruir un heap en cada consulta, $O(n + k \log n)$, o reordenar las $n$ estaciones en cada consulta, $O(n \log n)$. El ranking se consulta con frecuencia y cambia poco, así que conviene pagar el orden una sola vez y dejar la consulta en $O(k)$.

#### R7 · Editar rutas (`agregar_parada`, `quitar_parada`, `recorrido`)
- **Estructura:** cada ruta tiene una `ListaDoble` con el orden de paradas y una `TablaHash` (`estación -> NodoParada`).
- **Algoritmo:** la tabla entrega el nodo de referencia en $O(1)$ y la inserción o eliminación reconecta los punteros `ant` y `sig` en $O(1)$. `recorrido` recorre `sig` (o `ant` si `al_reves=True`) devolviendo la lista de nombres, o `[]` si la ruta no existe.
- **Reglas:**
  - `despues_de=None` inserta al inicio de la ruta.
  - Si `nueva` no existía en la red, se crea y se inserta en el AVL en $O(\log n)$.
  - `agregar_parada` devuelve `False` si la ruta no existe, si la estación ya está en la ruta o si `despues_de` no está en ella.
- **O grande:** `agregar_parada` y `quitar_parada` en $O(1)$ promedio ($O(\log n)$ si crea una estación nueva en el AVL de $n$ estaciones); `recorrido` en $O(m)$, donde $m$ = paradas de esa ruta.
- **Descartada:** arreglos dinámicos (`list`) con `insert` o `pop(i)`, que cuestan $O(m)$ por edición al desplazar elementos. Los operadores editan todo el tiempo.

#### R8 · Cerrar y reabrir (`cerrar(nombre)`, `reabrir(nombre)`)
- **Estructura:** bandera booleana `abierta` dentro de `Estacion`, indexada en la `TablaHash` principal.
- **Algoritmo:** consulta en $O(1)$ y cambio de estado de la bandera. Todas las operaciones de consulta verifican `visible()` antes de usar una estación, así que la cerrada desaparece de búsquedas, autocompletado, rangos, ranking y viajes sin borrar nodos del AVL ni reordenar nada. Devuelve `False` si la estación no existe o ya estaba en ese estado; ese caso no se registra para deshacer.
- **O grande:** $O(1)$ promedio respecto a $n$ (total de estaciones).
- **Descartada:** sacar la estación del AVL y del ranking y volverla a meter en cada cierre o reapertura. Costaría $O(\log n)$ en el AVL, obligaría a reconstruir el ranking ($O(n \log n)$) y complicaría deshacer.

#### R9 · Deshacer y rehacer (`deshacer()`, `rehacer()`)
- **Estructura:** dos pilas (`_deshacer` y `_rehacer`) implementadas con nodos enlazados que almacenan cambios reversibles (patrón *command*). Cada cambio guarda lo necesario para revertirse:
  - `cerrar` ↔ `reabrir`;
  - `agregar` guarda si creó la estación;
  - `quitar` guarda cuál era la parada anterior, para volver a ponerla en el mismo sitio.
- **Algoritmo:** `deshacer()` desapila el último cambio, ejecuta la operación inversa y lo apila en `_rehacer`. `rehacer()` hace el proceso simétrico. Cualquier acción mutadora nueva vacía `_rehacer` en $O(1)$. Si se deshace la creación de una estación, queda con `existe=False` y deja de aparecer en todo.
- **O grande:** $O(1)$ promedio por operación respecto a $n$ (total de estaciones); $O(\log n)$ si hay que recrear una estación en el AVL.
- **Descartada:** clonar el estado completo de la red antes de cada operación, lo que consumiría $O(n)$ en tiempo y memoria por cada cambio.

#### R10 · Fila de abordaje (`simular_fila(llegadas, frecuencia, capacidad)`)
- **Estructura:** cola FIFO implementada sobre un arreglo circular (`Cola` en `pila_cola.py`).
- **Algoritmo:** los buses salen en `frecuencia`, `2*frecuencia`, `3*frecuencia`, … Se procesan los pasajeros en orden cronológico de llegada (conservando su índice original para responder en el mismo orden de `llegadas`). En cada salida se encolan quienes llegaron hasta ese instante (quien llega justo a la hora del bus alcanza a subirse) y abordan hasta `capacidad` personas en orden de llegada, registrando el segundo de salida del bus. Si dos llegan al mismo tiempo, sube primero el que aparece antes en la lista. Si la fila está vacía, el reloj salta directamente al múltiplo de `frecuencia` correspondiente a la siguiente llegada, sin iterar buses vacíos.
- **O grande:** $O(P + B)$ cuando `llegadas` ya está ordenada, o $O(P \log P + B)$ si requiere ordenamiento previo con merge sort, donde $P$ = cantidad de pasajeros y $B$ = cantidad de buses despachados con pasajeros.
- **Descartadas:**
  - `list.pop(0)`: cuesta $O(P)$ por desencolado, degradando la simulación a $O(P^2)$.
  - Cola con nodos enlazados: aunque es $O(1)$ teórico, en la medición crecía más que lineal con cientos de miles de pasajeros, porque instanciar un objeto por pasajero sobrecarga el recolector de basura de Python. El arreglo circular almacena enteros directamente.

---

## R11 · Panel de rendimiento

La pestaña **📈 Rendimiento** de la app genera redes sintéticas de tamaño $n$, $2n$, $4n$, … (`app/herramientas/generar_red.py`), corre cada operación cientos de veces y grafica el tiempo medido junto a la curva esperada (anclada en el punto más grande). Al lado compara la última duplicación, de $n$ a $2n$, que es el mismo método del script del profesor, y dice si coincide, con la explicación.

### Mediciones con los tamaños de la rúbrica (10 000 a 80 000 estaciones)

El panel limita $n$ a 32 000, así que las redes de 10 000, 20 000, 40 000 y 80 000 estaciones se midieron con `app/herramientas/pendientes.py`, corrido en un Codespace de GitHub (Linux, Python 3.14). Cada celda es la **mediana** de 150 a 2 000 llamadas individuales con consultas al azar distintas en cada llamada, que es el caso más desfavorable para la memoria caché (R10: mediana de 3 repeticiones). Todo va en microsegundos por llamada, salvo la carga, que va en segundos. La **pendiente** es la inclinación de la recta $\log(\text{tiempo})$ contra $\log(n)$ en las cuatro redes: 0 es constante y 1 es lineal.

Los tiempos absolutos dependen de la máquina; lo que importa es la forma de la curva. Una segunda corrida en otra máquina (Linux, Python 3.13) dio tiempos entre 1.5 y 2 veces menores, y en las dos corridas todas las operaciones constantes o logarítmicas quedaron con pendiente menor que 0.6.

| Operación | Esperado | n=10 000 | n=20 000 | n=40 000 | n=80 000 | Pendiente | Comentario |
|---|---|---|---|---|---|---|---|
| Carga `Red(carpeta)` (s) | $O(n \log n)$ | 2.07 | 4.42 | 8.45 | 17.27 | 1.01 | Solo se mide cuánto tarda. Los horarios son casi todo el archivo |
| R1 estado | $O(1)$ | 2.18 | 2.46 | 2.54 | 2.62 | 0.08 | Sí. La tabla hash se redimensiona (factor de carga ≤ 0.75), por eso se mantiene casi plana |
| R2 autocompletar k=10, prefijo de 1 letra | $O(\log n + k)$ | 3.62 | 3.67 | 3.70 | 3.71 | 0.01 | Sí. Siempre hay más de $k$ coincidencias |
| R2 autocompletar k=10, prefijo de 3 letras | $O(\log n + k)$ | 2.96 | 3.21 | 3.60 | 6.58 | 0.36 | La consulta típica tiene menos de $k$ coincidencias (mediana de 2 en 10 000 y de 5 en 80 000), y una red más grande tiene más estaciones por prefijo. Crece el tamaño de la respuesta, no la búsqueda |
| R3 rango (~11 resultados) | $O(\log n + m)$ | 4.58 | 6.18 | 6.47 | 7.96 | 0.25 | $m$ es fijo. El $\log n$ solo sube un 22 % entre 10 000 y 80 000; el resto es, muy probablemente, memoria caché (un AVL grande no cabe en ella) |
| R4 próximo bus | $O(\log h)$ | 11.14 | 12.57 | 17.55 | 12.83 | 0.11 | $h$ no crece con $n$. El punto de 40 000 es un pico de ruido de la máquina compartida |
| R6 ranking k=10, sin cambios | $O(k)$ | 1.21 | 1.26 | 1.27 | 1.28 | 0.03 | Sí |
| R6 ranking k=10, con 200 cerradas en la cima | $O(k + c)$ | 10.13 | 10.85 | 11.06 | 10.60 | 0.02 | Sí. Depende de $c$, no de $n$ |
| R6 ranking k=10, justo después de editar una ruta | $O(n \log n)$ | 25 358 | 55 862 | 146 745 | 464 465 | 1.40 | Es la reconstrucción del ranking que se documenta en R6. Solo pasa en la primera consulta después de `agregar_parada` o `quitar_parada`; cerrar y reabrir nunca la provocan |
| R7 agregar_parada | $O(1)$ | 24.96 | 26.20 | 27.41 | 28.43 | 0.06 | Sí |
| R7 quitar_parada | $O(1)$ | 11.52 | 12.05 | 12.37 | 14.58 | 0.11 | Sí |
| R7 recorrido | $O(m)$ | 1.93 | 2.38 | 3.05 | 4.24 | 0.37 | $m$ (paradas por ruta) no crece con $n$; la variación es de caché |
| R8 cerrar | $O(1)$ | 2.31 | 2.55 | 4.76 | 3.01 | 0.20 | Sí. El punto de 40 000 es un pico de ruido de la máquina compartida |
| R8 reabrir | $O(1)$ | 2.40 | 2.41 | 3.52 | 2.75 | 0.11 | Sí |
| R9 deshacer (historial largo) | $O(1)$ | 2.58 | 2.66 | 2.71 | 2.73 | 0.03 | Sí |
| R9 rehacer (historial largo) | $O(1)$ | 2.21 | 2.23 | 2.23 | 2.30 | 0.02 | Sí |
| R10 fila, $P = 10n$, llegadas ordenadas | $O(P)$ | 80 471 | 158 661 | 334 176 | 724 240 | 1.06 | Sí. Al duplicar $P$ el tiempo se duplica |
| R10 fila, $P = 10n$, llegadas desordenadas | $O(P \log P)$ | 385 511 | 1 055 171 | 2 626 257 | 6 150 199 | 1.33 | Incluye el merge sort. La pendiente teórica de $n \log n$ en este rango ronda 1.1; el resto es, muy probablemente, acceso aleatorio a memoria |

R5 no se incluye, porque no entra en la medición de eficiencia.

### Mediciones del panel (2 000 a 32 000 estaciones)

Promedios de cientos de llamadas, en microsegundos por llamada, con $n$ de 2 000 a 32 000:

| Operación | Esperado | n=2000 | n=8000 | n=32000 | ¿Coincide? |
|---|---|---|---|---|---|
| R1 estado | $O(1)$ | 2.1 | 3.4 | 3.3 | Sí. Sube un poco de 2 000 a 8 000 por la memoria caché del procesador; después se estabiliza |
| R2 autocompletar k=10 | $O(\log n + k)$ | 3.6 | 4.5 | 3.9 | Sí |
| R3 rango (~10 resultados) | $O(\log n + m)$ | 4.0 | 11.3 | 10.5 | Sí. Mismo efecto de caché: un árbol más grande no cabe en la caché |
| R4 próximo bus | $O(\log h)$ | 12.6 | 16.4 | 15.8 | Sí. $h$ no crece con $n$ |
| R6 ranking k=10 | $O(k)$ | 1.1 | 1.1 | 1.2 | Sí |
| R7 agregar + quitar | $O(1)$ | 30.8 | 33.8 | 34.4 | Sí |
| R8 cerrar + reabrir | $O(1)$ | 11.4 | 6.0 | 6.4 | Sí. El primer punto incluye calentamiento |
| R9 deshacer + rehacer | $O(1)$ | 10.5 | 4.0 | 5.4 | Sí |
| R10 fila (50n pasajeros) | $O(P)$ | 216 716 | 856 058 | 2 471 211 | Sí. Al duplicar $P$ el tiempo se duplica aproximadamente |

**Por qué una $O(1)$ no da una línea perfectamente plana:** con redes más grandes los datos no caben en la memoria caché del procesador, y cada acceso tarda un poco más. Ese costo no viene del algoritmo: se estabiliza en vez de seguir creciendo. Si el algoritmo fuera $O(n)$, al duplicar $n$ el tiempo se duplicaría siempre.

---

## Datos: del GTFS a los tres CSV

`datos/convertir_gtfs.py` usa pandas, que está permitido fuera del motor. Decisiones:

Fuente: GTFS estático de TransMilenio del 14 de julio de 2021 ([datos abiertos de movilidad de Bogotá](https://datos.movilidadbogota.gov.co/datasets/6def68cda70c43ab8d93d74f43c5915a/about)).

1. **Solo el sistema troncal** por defecto (`route_desc == TRONCAL`). Así quedan 124 estaciones, 89 rutas y unas 95 000 pasadas al día. Con `--todo` se agregan alimentadores y SITP: 6 403 paradas y 2,3 millones de horarios. El motor carga esa red en unos 7 s.
2. **Vagones → estación.** En el GTFS una estación aparece como varios stops (por ejemplo "Calle 85 B - 4 ó 6" o "Portal 80 T-1A"). Se quita el sufijo de vagón o plataforma y quedan unidas, para que un transbordo dentro de la misma estación funcione.
3. **Nombres** en mayúsculas, sin tildes (Ñ → N), sin espacios dobles y sin repetidos. Fuera del troncal, cada parada conserva su código para no fusionar paradas lejanas que se llaman igual.
4. **Un solo día de servicio.** Se usa lunes, un día hábil, para que "buses al día" sea un día de verdad y no la suma de lunes, sábado y domingo. Se puede cambiar con `--dia`.
5. **Cada ruta va en un solo sentido.** En TransMilenio cada `route_id` ya va en un sentido (B74 va al norte y J74 al sur). El orden de paradas es el patrón más frecuente entre sus viajes; si hay empate, el más largo. Una estación repetida dentro de la ruta se deja solo la primera vez.
6. **Horas como 25:10.** Se pasan a la hora real del reloj con módulo 24 (25:10 → 01:10) y se truncan a minutos. El motor también aplica el módulo por si la red del profesor trae horas así. En R4, `proximo_bus` busca el siguiente bus dentro del día actual y devuelve `None` si ya no hay más ese día.
7. **Coordenadas para el mapa.** La posición de cada estación es el promedio de las de sus vagones. Van en `coordenadas.csv`, aparte de los tres CSV del contrato: el motor solo lee esos tres, y el mapa de la app usa este cuarto archivo únicamente para dibujar.
8. **Fondo del mapa.** `app/fondo_mapa.jpg` son 154 mosaicos de OpenStreetMap (zoom 14) descargados una sola vez y unidos en una imagen, para que el mapa funcione sin internet. El mapa usa la misma proyección (Web Mercator), así cada estación cae sobre su calle. Datos y mapa: © colaboradores de OpenStreetMap ([licencia](https://www.openstreetmap.org/copyright)).

---

## Reglas del motor

Dentro de `motor/` solo se usan `list` (como arreglo), `str`, `csv`, `time` y `random`. No se usan `dict`, `set`, `sorted`, `.sort()`, `min`, `max`, `x in lista`, `.index()`, `.count()`, `bisect`, `heapq`, `collections`, `functools` ni `os`. El revisor `app/herramientas/revisar_prohibidos.py` lo comprueba con el árbol sintáctico de Python, y es más estricto que la regla: también marca `in` sobre textos.

Ninguna regla del sistema está en el front. La app solo llama al motor; lo único que hace por su cuenta es pasar a mayúsculas lo que escribe la persona.

## App desplegada

Puedes probar la aplicación aquí:

https://planeador-transmilenio-lostungtungcitos.onrender.com/

*(Nota: al estar en el plan gratuito de Render, si lleva un rato sin usarse puede tardar unos 30–50 segundos en despertar la primera vez que se abre).*

En Render la configuración es: build command `echo "Listo"` y start command `python app/servidor.py`.
