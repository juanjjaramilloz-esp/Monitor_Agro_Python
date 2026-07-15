"""Carga, regeneración y caché de los datos consumidos por Streamlit."""

import os
from pathlib import Path

import pandas as pd
import streamlit as st
import yfinance as yf

from config import TICKER_CAFE_ARABICA, TICKER_FX
from procesar.calibracion_fnc import RUTA_CALIBRACION_FNC
from procesar.historico import RUTA_DIARIO
from procesar.visualizacion import RUTA_SERIES, series_necesitan_regenerarse
from procesar.visualizacion import ejecutar as preparar_visualizacion

COLUMNAS_NUMERICAS_VISUALES = [
    "valor",
    "indice_base_100",
    "cambio_1s_absoluto",
    "cambio_1s_pct",
    "cambio_4s_pct",
    "cambio_1m_pct",
    "cambio_12m_pct",
    "promedio_movil_4s",
    "promedio_movil_12s",
    "anomalia_z_52s",
    "ranking_departamental",
    "percentil_departamental",
    "diferencia_mediana_departamentos",
]


@st.cache_data(show_spinner=False)
def leer_series(ruta: str, marca_tiempo: float) -> pd.DataFrame:
    """Lee el derivado visual y tolera columnas nuevas ausentes en cachés viejas."""
    del marca_tiempo
    tabla = pd.read_csv(ruta, parse_dates=["semana_fin", "fecha_dato"])
    for columna in COLUMNAS_NUMERICAS_VISUALES:
        if columna not in tabla.columns:
            tabla[columna] = pd.NA
        tabla[columna] = pd.to_numeric(tabla[columna], errors="coerce")
    return tabla


def cargar_datos() -> pd.DataFrame:
    """Regenera el derivado visual cuando el histórico cambió y lo carga."""
    ruta = Path(RUTA_SERIES)
    if series_necesitan_regenerarse():
        preparar_visualizacion()
    return leer_series(str(ruta), ruta.stat().st_mtime)


@st.cache_data(show_spinner=False)
def leer_historico_diario(ruta: str, marca_tiempo: float) -> pd.DataFrame:
    """Carga las observaciones diarias usadas para calibrar el estimador."""
    del marca_tiempo
    return pd.read_csv(ruta, parse_dates=["fecha"])


def cargar_historico_diario() -> pd.DataFrame:
    """Carga el histórico diario o falla con una explicación accionable."""
    ruta = Path(RUTA_DIARIO)
    if not ruta.exists():
        raise FileNotFoundError(f"No existe el histórico diario: {ruta}")
    return leer_historico_diario(str(ruta), ruta.stat().st_mtime)


def cargar_calibracion_fnc() -> pd.DataFrame:
    """Carga referencias oficiales coherentes; permite respaldo si no existen."""
    ruta = Path(RUTA_CALIBRACION_FNC)
    if not ruta.exists():
        return pd.DataFrame()
    return pd.read_csv(ruta, parse_dates=["fecha"])


@st.cache_data(ttl=300, show_spinner=False)
def precios_intradia() -> dict[str, tuple[float, str]]:
    """Consulta los últimos precios Yahoo; se desactiva en validaciones offline."""
    if os.environ.get("PULSO_CAFETERO_OFFLINE") == "1":
        return {}

    precios: dict[str, tuple[float, str]] = {}
    for clave, ticker in (("cafe", TICKER_CAFE_ARABICA), ("fx", TICKER_FX)):
        try:
            historial = yf.Ticker(ticker).history(period="1d", interval="1m")
            cierres = historial["Close"].dropna()
            if cierres.empty:
                continue
            momento = cierres.index[-1]
            if momento.tzinfo is not None:
                momento = momento.tz_convert("America/Bogota")
            precios[clave] = (float(cierres.iloc[-1]), f"{momento:%d/%m %H:%M}")
        except Exception:
            continue
    return precios
