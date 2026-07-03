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

import unicodedata
from urllib.parse import urljoin

import requests

from config import URL_PRECIO_INTERNO_FNC

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


def _sin_tildes(texto: str) -> str:
    """Quita tildes y diacríticos para comparar nombres de forma robusta."""
    normalizado = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in normalizado if not unicodedata.combining(c))


def _normalizar(texto: str) -> str:
    """Normaliza un texto (sin tildes, sin espacios extremos, minúsculas)."""
    return _sin_tildes(texto).strip().lower()


def buscar_url_excel(sopa, patron: str, base: str = URL_PRECIO_INTERNO_FNC) -> str | None:
    """Devuelve el último `.xlsx` enlazado en la página cuyo href contiene `patron`.

    El emparejamiento es insensible a mayúsculas/minúsculas. Se usa para los
    tres descargables FNC (precio/producción comparten patrón; exportaciones
    usa el suyo), evitando repetir la misma lógica en cada fuente.
    """
    patron_norm = patron.lower()
    candidatos = [
        urljoin(base, str(enlace["href"]))
        for enlace in sopa.find_all("a", href=True)
        if patron_norm in str(enlace["href"]).lower()
        and ".xlsx" in str(enlace["href"]).lower()
    ]
    return candidatos[-1] if candidatos else None


def buscar_hoja(nombres_hojas, prefijo: str) -> str | None:
    """Primera hoja cuyo nombre empieza por `prefijo`, sin tildes ni mayúsculas.

    Unifica el criterio de las tres fuentes FNC (antes cada una comparaba de
    forma distinta), tolerando variaciones de tildes y capitalización.
    """
    objetivo = _normalizar(prefijo)
    return next(
        (nombre for nombre in nombres_hojas if _normalizar(nombre).startswith(objetivo)),
        None,
    )
