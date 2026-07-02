"""Descargas compartidas de la página y archivos de la FNC.

Cuatro fuentes (precio_interno, produccion, exportaciones y
referencia_mercado_fnc) consultan la misma página de estadísticas cafeteras y,
en dos casos, el mismo Excel. Este módulo centraliza la descarga con una caché
por proceso para pedir cada URL una sola vez por corrida (main.py, historico o
workflow), reduciendo el riesgo de bloqueo por el WAF de la FNC.

Las descargas fallidas no se cachean: la excepción se propaga y cada fuente
conserva su manejo de error del contrato (DataFrame vacío con columnas
correctas).
"""

import requests

# Cabecera de navegador: algunos WAF rechazan el User-Agent por defecto de requests.
CABECERAS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

_CACHE_TEXTO: dict[str, str] = {}
_CACHE_BINARIO: dict[str, bytes] = {}


def descargar_texto(url: str, timeout: int = 30) -> str:
    """Devuelve el HTML de la URL, descargándolo una sola vez por proceso."""
    if url not in _CACHE_TEXTO:
        respuesta = requests.get(url, headers=CABECERAS, timeout=timeout)
        respuesta.raise_for_status()
        _CACHE_TEXTO[url] = respuesta.text
    return _CACHE_TEXTO[url]


def descargar_binario(url: str, timeout: int = 60) -> bytes:
    """Devuelve el contenido binario (Excel) de la URL con caché por proceso."""
    if url not in _CACHE_BINARIO:
        respuesta = requests.get(url, headers=CABECERAS, timeout=timeout)
        respuesta.raise_for_status()
        _CACHE_BINARIO[url] = respuesta.content
    return _CACHE_BINARIO[url]


def limpiar_cache() -> None:
    """Vacía las cachés; útil en pruebas o para forzar una descarga fresca."""
    _CACHE_TEXTO.clear()
    _CACHE_BINARIO.clear()
