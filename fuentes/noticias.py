"""
Fuente y caché de noticias de agroexportación (GDELT DOC 2.0, sin key).

Contrato de salida (ver CLAUDE.md, sección 5):
    fecha     : date
    geografia : str   — "COLOMBIA" (consulta nacional)
    titulo    : str
    url       : str
    fuente    : str   — "gdelt"
    idioma    : str
    tono      : float — opcional
    categoria : str   — opcional

``obtener()`` conserva el contrato de las fuentes y nunca propaga un fallo de
red. ``actualizar_cache()`` es el punto de entrada de la automatización: hace
varios intentos, versiona solo consultas no vacías y, si GDELT limita la
petición, devuelve la última consulta útil que aún esté dentro de tolerancia.
El comentario de IA lee ese archivo; nunca consulta GDELT directamente.
"""

import time
from collections.abc import Callable
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
from gdeltdoc import Filters, GdeltDoc

from config import (
    ARCHIVO_NOTICIAS,
    GEOGRAFIA_PAIS,
    IDIOMA_NOTICIAS,
    NOTICIAS_CACHE_MAX_EDAD_DIAS,
    NOTICIAS_DIAS_ATRAS,
    NOTICIAS_ESPERA_REINTENTO_SEGUNDOS,
    NOTICIAS_MAX_REGISTROS,
    NOTICIAS_REINTENTOS,
    PAIS_FIPS,
    TERMINOS_NOTICIAS,
)

COLUMNAS = ["fecha", "geografia", "titulo", "url", "fuente", "idioma", "tono", "categoria"]


def _tabla_vacia() -> pd.DataFrame:
    return pd.DataFrame(columns=COLUMNAS)


def _normalizar_fecha(serie: pd.Series) -> pd.Series:
    """Convierte fechas de GDELT a objetos date; valores inválidos quedan NaN."""
    return pd.to_datetime(serie, errors="coerce", utc=True).dt.date


def _normalizar_articulos(articulos: pd.DataFrame) -> pd.DataFrame:
    """Adapta las columnas de GDELT al contrato de noticias del proyecto."""
    if articulos.empty:
        return _tabla_vacia()

    df = pd.DataFrame(
        {
            "fecha": _normalizar_fecha(
                articulos.get("seendate", pd.Series(dtype=str))
            ),
            "geografia": GEOGRAFIA_PAIS,
            "titulo": articulos.get("title", pd.Series(dtype=str)),
            "url": articulos.get("url", pd.Series(dtype=str)),
            "fuente": "gdelt",
            "idioma": articulos.get("language", pd.Series(dtype=str)),
            "tono": float("nan"),
            "categoria": pd.NA,
        }
    )
    df = df.dropna(subset=["fecha", "titulo", "url"])
    return df[COLUMNAS]


def _normalizar_cache(tabla: pd.DataFrame) -> pd.DataFrame:
    """Valida el CSV persistido y lo devuelve con el contrato vigente."""
    if tabla.empty or not set(COLUMNAS).issubset(tabla.columns):
        return _tabla_vacia()
    resultado = tabla[COLUMNAS].copy()
    resultado["fecha"] = _normalizar_fecha(resultado["fecha"])
    resultado = resultado.dropna(subset=["fecha", "titulo", "url"])
    return resultado.drop_duplicates(subset=["geografia", "url"])


def _consultar() -> pd.DataFrame:
    """Realiza una consulta a GDELT; los reintentos se gestionan fuera."""
    filtros = Filters(
        timespan=f"{NOTICIAS_DIAS_ATRAS}d",
        keyword=TERMINOS_NOTICIAS,
        country=PAIS_FIPS,
        language=IDIOMA_NOTICIAS,
        num_records=NOTICIAS_MAX_REGISTROS,
    )
    articulos = GdeltDoc().article_search(filtros)
    resultado = _normalizar_articulos(articulos)
    return resultado.drop_duplicates(subset=["geografia", "url"])[COLUMNAS]


def _consultar_con_reintentos(
    consultar: Callable[[], pd.DataFrame] | None = None,
    dormir: Callable[[float], None] | None = None,
) -> tuple[pd.DataFrame, Exception | None, int]:
    """Consulta GDELT con espera exponencial y devuelve el último error."""
    consultar = consultar or _consultar
    dormir = dormir or time.sleep
    ultimo_error: Exception | None = None

    for intento in range(1, NOTICIAS_REINTENTOS + 1):
        try:
            return consultar(), None, intento
        except Exception as error:  # noqa: BLE001 - la fuente nunca rompe el pipeline
            ultimo_error = error
            if intento < NOTICIAS_REINTENTOS:
                espera = NOTICIAS_ESPERA_REINTENTO_SEGUNDOS * (2 ** (intento - 1))
                print(
                    "  AVISO: GDELT falló "
                    f"({type(error).__name__}); reintento {intento + 1}/"
                    f"{NOTICIAS_REINTENTOS} en {espera} s."
                )
                dormir(espera)

    return _tabla_vacia(), ultimo_error, NOTICIAS_REINTENTOS


def obtener() -> pd.DataFrame:
    """Devuelve noticias recientes y conserva el contrato si GDELT falla."""
    resultado, error, _ = _consultar_con_reintentos()
    if error is not None:
        print(
            "  AVISO: error al consultar GDELT tras reintentos "
            f"({type(error).__name__}): {error}"
        )
    return resultado


def guardar_cache(
    noticias: pd.DataFrame,
    ruta: Path = ARCHIVO_NOTICIAS,
) -> pd.DataFrame:
    """Versiona una consulta útil; una tabla vacía nunca borra el respaldo."""
    resultado = _normalizar_cache(noticias)
    if resultado.empty:
        return resultado
    resultado = resultado.sort_values("fecha", ascending=False)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    resultado.to_csv(ruta, index=False, date_format="%Y-%m-%d")
    return resultado


def cargar_cache(
    ruta: Path = ARCHIVO_NOTICIAS,
    hoy: date | None = None,
) -> pd.DataFrame:
    """Carga el último éxito si contiene noticias suficientemente recientes."""
    if not ruta.exists():
        return _tabla_vacia()
    try:
        resultado = _normalizar_cache(pd.read_csv(ruta))
    except (OSError, pd.errors.ParserError, UnicodeDecodeError):
        return _tabla_vacia()
    if resultado.empty:
        return resultado
    limite = (hoy or date.today()) - timedelta(days=NOTICIAS_CACHE_MAX_EDAD_DIAS)
    return resultado[resultado["fecha"].ge(limite)].reset_index(drop=True)


def actualizar_cache(
    ruta: Path = ARCHIVO_NOTICIAS,
) -> pd.DataFrame:
    """Refresca el caché o usa el último éxito reciente como respaldo."""
    resultado, error, intentos = _consultar_con_reintentos()
    if error is None and not resultado.empty:
        guardado = guardar_cache(resultado, ruta)
        print(f"Noticias GDELT actualizadas: {ruta} ({len(guardado)} filas; {intentos} intento(s)).")
        return guardado

    respaldo = cargar_cache(ruta)
    motivo = "consulta vacía" if error is None else type(error).__name__
    if respaldo.empty:
        print(f"Noticias GDELT sin datos ni respaldo vigente ({motivo}).")
    else:
        print(
            f"Noticias GDELT: se usa el último respaldo vigente "
            f"({len(respaldo)} filas) por {motivo}."
        )
    return respaldo


if __name__ == "__main__":
    df = actualizar_cache()
    print("fuentes.noticias - resultado disponible")
    print(f"  shape : {df.shape}")
    print(f"  tipos :\n{df.dtypes}")
    print(f"\n{df.head(15)}")
