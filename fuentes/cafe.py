"""
Fuente: precio del café (futuro ICE Coffee C, arábica).

Contrato de salida (ver CLAUDE.md, sección 4):
    fecha    : date
    geografia: str  — "GLOBAL" (precio internacional, no por geografía)
    variable : str  — "precio_cafe_arabica"
    valor    : float
    unidad   : str  — "USc/lb"
    fuente   : str  — "yfinance"

Limitación conocida: yfinance raspa Yahoo Finance y puede romperse sin aviso.
Alpha Vantage cubre solo frecuencia mensual y requiere API key (.env).
"""

from datetime import date, timedelta

import pandas as pd
import yfinance as yf

from config import GEOGRAFIA_GLOBAL, TICKER_CAFE_ARABICA


COLUMNAS = ["fecha", "geografia", "variable", "valor", "unidad", "fuente"]


def obtener(
    desde: date | None = None,
    hasta: date | None = None,
) -> pd.DataFrame:
    """Devuelve el cierre reciente o una serie diaria histórica de café."""
    if (desde is None) != (hasta is None):
        raise ValueError("cafe: desde y hasta deben proporcionarse juntos")
    if desde is not None and hasta is not None and desde > hasta:
        raise ValueError("cafe: desde no puede ser posterior a hasta")

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
            parametros["end"] = (hasta + timedelta(days=1)).isoformat()

        datos = yf.download(TICKER_CAFE_ARABICA, **parametros)

        if datos.empty:
            print(f"  AVISO: {TICKER_CAFE_ARABICA} - yfinance no devolvio datos.")
            return pd.DataFrame(columns=COLUMNAS)

        # yfinance es la fuente mas fragil del proyecto: raspa Yahoo Finance
        # y puede cambiar su estructura. Para un ticker suele devolver MultiIndex.
        cierre = datos["Close"]
        if isinstance(cierre, pd.DataFrame):
            cierre = cierre.iloc[:, 0]
        cierre = cierre.dropna()

        if cierre.empty:
            print(f"  AVISO: {TICKER_CAFE_ARABICA} - sin valores de cierre.")
            return pd.DataFrame(columns=COLUMNAS)

        if desde is None:
            cierre = cierre.iloc[[-1]]

        filas = [
            {
                "fecha": pd.to_datetime(fecha).date(),
                "geografia": GEOGRAFIA_GLOBAL,
                "variable": "precio_cafe_arabica",
                "valor": float(valor),
                "unidad": "USc/lb",
                "fuente": "yfinance",
            }
            for fecha, valor in cierre.items()
        ]
        return pd.DataFrame(filas, columns=COLUMNAS)

    except Exception as e:
        print(f"  AVISO: {TICKER_CAFE_ARABICA} - error al descargar: {e}")
        return pd.DataFrame(columns=COLUMNAS)


if __name__ == "__main__":
    df = obtener()
    print("fuentes.cafe - resultado")
    print(f"  shape : {df.shape}")
    print(f"  tipos :\n{df.dtypes}")
    print(f"\n{df.head()}")
