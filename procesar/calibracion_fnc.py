"""Persiste la calibración diaria coherente publicada por la FNC."""

from pathlib import Path

import pandas as pd

from config import DIR_HISTORICO
from fuentes import referencia_mercado_fnc


RUTA_CALIBRACION_FNC = DIR_HISTORICO / "calibracion_fnc.csv"
COLUMNAS = [
    "fecha",
    "precio_fnc",
    "tasa_cambio",
    "precio_ny",
    "coeficiente_implicito",
    "fuente",
]


def preparar(tabla: pd.DataFrame) -> pd.DataFrame:
    """Convierte la salida larga de la fuente en una fila de calibración."""
    requeridas = {
        "precio_interno_referencia",
        "fx_fnc_calculo",
        "precio_cafe_fnc_calculo",
    }
    if tabla.empty or not requeridas.issubset(set(tabla["variable"])):
        return pd.DataFrame(columns=COLUMNAS)
    fechas = pd.to_datetime(tabla["fecha"], errors="coerce").dropna().unique()
    if len(fechas) != 1:
        return pd.DataFrame(columns=COLUMNAS)

    valores = tabla.set_index("variable")["valor"]
    precio_fnc = float(valores["precio_interno_referencia"])
    tasa_cambio = float(valores["fx_fnc_calculo"])
    precio_ny = float(valores["precio_cafe_fnc_calculo"])
    if min(precio_fnc, tasa_cambio, precio_ny) <= 0:
        return pd.DataFrame(columns=COLUMNAS)
    return pd.DataFrame(
        [
            {
                "fecha": pd.Timestamp(fechas[0]).date(),
                "precio_fnc": precio_fnc,
                "tasa_cambio": tasa_cambio,
                "precio_ny": precio_ny,
                "coeficiente_implicito": precio_fnc / (tasa_cambio * precio_ny),
                "fuente": "FNC",
            }
        ],
        columns=COLUMNAS,
    )


def guardar(nueva: pd.DataFrame, ruta: Path = RUTA_CALIBRACION_FNC) -> pd.DataFrame:
    """Combina la referencia nueva de forma idempotente y guarda el CSV."""
    if nueva.empty:
        return pd.read_csv(ruta) if ruta.exists() else nueva
    existente = pd.read_csv(ruta) if ruta.exists() else pd.DataFrame(columns=COLUMNAS)
    resultado = pd.concat([existente, nueva], ignore_index=True)
    resultado["fecha"] = pd.to_datetime(resultado["fecha"], errors="coerce")
    resultado = (
        resultado.dropna(subset=["fecha"])
        .drop_duplicates(subset=["fecha"], keep="last")
        .sort_values("fecha")
    )
    resultado["fecha"] = resultado["fecha"].dt.date
    ruta.parent.mkdir(parents=True, exist_ok=True)
    resultado.to_csv(ruta, index=False, encoding="utf-8")
    return resultado


def ejecutar() -> pd.DataFrame:
    """Consulta la FNC y actualiza la serie local de calibraciones."""
    nueva = preparar(referencia_mercado_fnc.obtener())
    if nueva.empty:
        print("Calibración FNC: fuente vacía; se conserva el archivo existente.")
        return guardar(nueva)
    resultado = guardar(nueva)
    print(f"Calibración FNC actualizada: {RUTA_CALIBRACION_FNC} ({len(resultado)} filas)")
    return resultado


if __name__ == "__main__":
    ejecutar()
