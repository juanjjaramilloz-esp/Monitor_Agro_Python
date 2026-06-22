"""
Fuente: tipo de cambio USD/COP.

Contrato de salida (ver CLAUDE.md, sección 4):
    fecha    : date
    geografia: str  — "COLOMBIA"
    variable : str  — "fx_usd_local"
    valor    : float
    unidad   : str  — "COP/USD"
    fuente   : str  — "yfinance"

Tras el pivote a Colombia el FX relevante es uno solo: USD/COP (config.TICKER_FX).
Se usa yfinance porque Frankfurter/BCE no cubre COP; yfinance ya es dependencia
del proyecto.

Limitación conocida: yfinance raspa Yahoo Finance y puede romperse sin aviso.
Si el ticker falla, se devuelve un DataFrame vacío con las columnas correctas.
"""

import warnings

import pandas as pd
import yfinance as yf

from config import GEOGRAFIA_PAIS, MONEDA, TICKER_FX

COLUMNAS = ["fecha", "geografia", "variable", "valor", "unidad", "fuente"]


def obtener() -> pd.DataFrame:
    """Devuelve el tipo de cambio USD→COP más reciente (una sola fila)."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            datos = yf.download(TICKER_FX, period="5d", interval="1d", progress=False, auto_adjust=True)

        if datos.empty:
            print(f"  AVISO: {TICKER_FX} — yfinance no devolvió datos.")
            return pd.DataFrame(columns=COLUMNAS)

        # yfinance devuelve MultiIndex ('Price', 'Ticker'); extraemos Close.
        close = datos["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
        close = close.dropna()
        if close.empty:
            print(f"  AVISO: {TICKER_FX} — sin valores de cierre.")
            return pd.DataFrame(columns=COLUMNAS)

        fila = {
            "fecha": close.index[-1].date(),
            "geografia": GEOGRAFIA_PAIS,
            "variable": "fx_usd_local",
            "valor": float(close.iloc[-1]),
            "unidad": f"{MONEDA}/USD",
            "fuente": "yfinance",
        }
        return pd.DataFrame([fila], columns=COLUMNAS)

    except Exception as e:
        print(f"  AVISO: {TICKER_FX} — error al descargar: {e}")
        return pd.DataFrame(columns=COLUMNAS)


if __name__ == "__main__":
    df = obtener()
    print("\nfuentes.fx — resultado")
    print(f"  shape : {df.shape}")
    print(f"  tipos :\n{df.dtypes}")
    print(f"\n{df.head(10)}")
