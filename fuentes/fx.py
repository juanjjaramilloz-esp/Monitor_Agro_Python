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
from datetime import date, timedelta

import pandas as pd
import yfinance as yf

from config import GEOGRAFIA_PAIS, MONEDA, TICKER_FX

COLUMNAS = ["fecha", "geografia", "variable", "valor", "unidad", "fuente"]


def obtener(
    desde: date | None = None,
    hasta: date | None = None,
) -> pd.DataFrame:
    """Devuelve el cierre reciente o una serie diaria histórica de USD/COP."""
    if (desde is None) != (hasta is None):
        raise ValueError("fx: desde y hasta deben proporcionarse juntos")
    if desde is not None and hasta is not None and desde > hasta:
        raise ValueError("fx: desde no puede ser posterior a hasta")

    try:
        parametros = {
            "interval": "1d",
            "progress": False,
            "auto_adjust": True,
        }
        if desde is None:
            parametros["period"] = "5d"
        else:
            parametros["start"] = desde.isoformat()
            # yfinance interpreta end como límite exclusivo.
            parametros["end"] = (hasta + timedelta(days=1)).isoformat()

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            datos = yf.download(TICKER_FX, **parametros)

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

        if desde is None:
            close = close.iloc[[-1]]

        filas = [
            {
                "fecha": pd.to_datetime(fecha).date(),
                "geografia": GEOGRAFIA_PAIS,
                "variable": "fx_usd_local",
                "valor": float(valor),
                "unidad": f"{MONEDA}/USD",
                "fuente": "yfinance",
            }
            for fecha, valor in close.items()
        ]
        return pd.DataFrame(filas, columns=COLUMNAS)

    except Exception as e:
        print(f"  AVISO: {TICKER_FX} — error al descargar: {e}")
        return pd.DataFrame(columns=COLUMNAS)


if __name__ == "__main__":
    df = obtener()
    print("\nfuentes.fx — resultado")
    print(f"  shape : {df.shape}")
    print(f"  tipos :\n{df.dtypes}")
    print(f"\n{df.head(10)}")
