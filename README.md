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
