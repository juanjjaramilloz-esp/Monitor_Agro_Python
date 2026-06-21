"""
Fuente: tipos de cambio USD/moneda local.

Contrato de salida (ver CLAUDE.md, sección 4):
    fecha    : date
    pais     : str  — código ISO3
    variable : str  — "fx_usd_local"
    valor    : float
    unidad   : str  — "<MONEDA>/USD" (ej. "COP/USD")
    fuente   : str  — "yfinance"

Decisión de diseño: se usa yfinance para las cinco monedas (BRL, MXN, COP,
PEN, HNL) en lugar del enfoque híbrido Frankfurter + yfinance. Motivo:
yfinance cubre las cinco y ya es dependencia del proyecto; la consistencia
metodológica prima sobre usar la fuente "oficial" solo para dos de ellas.
Diagnóstico previo (experimento_fx.py) confirmó que Frankfurter no cubre
COP, PEN ni HNL.

Limitación conocida: yfinance raspa Yahoo Finance y puede romperse sin
aviso. Si un ticker falla, se omite esa fila y se imprime una advertencia.
"""

import warnings
from datetime import date

import pandas as pd
import yfinance as yf

from config import PAISES

COLUMNAS = ["fecha", "pais", "variable", "valor", "unidad", "fuente"]


def obtener() -> pd.DataFrame:
    """Devuelve el tipo de cambio USD→moneda local más reciente para cada país."""
    filas: list[dict] = []

    for pais in PAISES:
        ticker = pais["ticker_fx"]
        iso3 = pais["iso3"]
        moneda = pais["moneda"]

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                datos = yf.download(ticker, period="5d", interval="1d", progress=False, auto_adjust=True)

            if datos.empty:
                print(f"  AVISO: {ticker} ({iso3}) — yfinance no devolvió datos.")
                continue

            # yfinance devuelve MultiIndex ('Price', 'Ticker'); extraemos Close.
            close = datos["Close"]
            if isinstance(close, pd.DataFrame):
                close = close.iloc[:, 0]
            close = close.dropna()
            if close.empty:
                print(f"  AVISO: {ticker} ({iso3}) — sin valores de cierre.")
                continue
            valor = float(close.iloc[-1])
            fecha_dato = close.index[-1].date()

            filas.append({
                "fecha": fecha_dato,
                "pais": iso3,
                "variable": "fx_usd_local",
                "valor": valor,
                "unidad": f"{moneda}/USD",
                "fuente": "yfinance",
            })

        except Exception as e:
            print(f"  AVISO: {ticker} ({iso3}) — error al descargar: {e}")

    return pd.DataFrame(filas, columns=COLUMNAS)


if __name__ == "__main__":
    df = obtener()
    print("\nfuentes.fx — resultado")
    print(f"  shape : {df.shape}")
    print(f"  tipos :\n{df.dtypes}")
    print(f"\n{df.head(10)}")
