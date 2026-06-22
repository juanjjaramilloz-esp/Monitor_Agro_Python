"""
Fase 2 — Unir fuentes numéricas en una tabla semanal y archivar el snapshot.

Esquema de salida:
    fecha_snapshot : date  — fecha en que se generó el snapshot (igual para todas las filas)
    fecha_dato     : date  — fecha real del dato según la fuente
    geografia      : str   — "GLOBAL" (café), "COLOMBIA" (FX, precio interno) o
                             nombre de departamento cafetero (clima)
    variable       : str   — nombre del indicador
    valor          : float
    unidad         : str
    fuente         : str

Decisión de fechas (ver CONTEXTO_IAS.md):
  - FX, café y precio interno: datos puntuales; se usa la fecha del dato como
    fecha_dato. No se agrega ni redondea.
  - Clima: la fuente devuelve ~8 días diarios por departamento. Se agrega a
    cuatro variables semanales; fecha_dato = la fecha más reciente de la ventana.
  - fecha_snapshot = datetime.now().date() al momento de correr la unión;
    permite reconstruir qué datos había disponibles en cada corrida semanal.
"""

from datetime import date
from typing import Optional

import pandas as pd

from config import DIR_SNAPSHOTS
from fuentes import cafe, clima, fx, precio_interno

COLUMNAS = ["fecha_snapshot", "fecha_dato", "geografia", "variable", "valor", "unidad", "fuente"]


def _agregar_clima(df_clima: pd.DataFrame, fecha_snapshot: date) -> pd.DataFrame:
    """Convierte el clima diario en cuatro variables semanales por departamento."""
    if df_clima.empty:
        return pd.DataFrame(columns=COLUMNAS)

    filas: list[dict] = []

    for departamento, grupo in df_clima.groupby("geografia"):
        fecha_dato = grupo["fecha"].max()

        def _serie(var: str) -> pd.Series:
            return grupo.loc[grupo["variable"] == var, "valor"]

        temp_min = _serie("temp_min")
        temp_max = _serie("temp_max")

        # Punto medio diario para el promedio semanal
        medios = (temp_min.values + temp_max.values[:len(temp_min)]) / 2 if not temp_min.empty and not temp_max.empty else pd.Series(dtype=float)

        agregados = [
            ("precipitacion_semanal", _serie("precipitacion").sum() if not _serie("precipitacion").empty else float("nan"), "mm"),
            ("temp_min_semanal",      temp_min.min() if not temp_min.empty else float("nan"),                               "°C"),
            ("temp_max_semanal",      temp_max.max() if not temp_max.empty else float("nan"),                               "°C"),
            ("temp_promedio_semanal", float(pd.Series(medios).mean()) if len(medios) > 0 else float("nan"),                "°C"),
        ]

        for variable, valor, unidad in agregados:
            filas.append({
                "fecha_snapshot": fecha_snapshot,
                "fecha_dato":     fecha_dato,
                "geografia":      departamento,
                "variable":       variable,
                "valor":          round(float(valor), 4),
                "unidad":         unidad,
                "fuente":         "open-meteo",
            })

    return pd.DataFrame(filas, columns=COLUMNAS)


def _puntual_a_semanal(df: pd.DataFrame, fecha_snapshot: date) -> pd.DataFrame:
    """Añade fecha_snapshot a una fuente puntual (FX, café o precio interno)."""
    if df.empty:
        return pd.DataFrame(columns=COLUMNAS)

    out = df.rename(columns={"fecha": "fecha_dato"}).copy()
    out.insert(0, "fecha_snapshot", fecha_snapshot)
    return out[COLUMNAS]


def unir(fecha_snapshot: Optional[date] = None) -> pd.DataFrame:
    """
    Llama las cuatro fuentes numéricas (FX, café, precio interno, clima),
    las une en una tabla semanal tidy y guarda el snapshot en datos/snapshots/.

    Parámetros
    ----------
    fecha_snapshot : date, opcional
        Fecha que identifica el snapshot. Por defecto es hoy.
        Se puede sobrescribir en pruebas para reproducibilidad.
    """
    if fecha_snapshot is None:
        fecha_snapshot = date.today()

    partes: list[pd.DataFrame] = []

    df_fx = fx.obtener()
    partes.append(_puntual_a_semanal(df_fx, fecha_snapshot))

    df_cafe = cafe.obtener()
    partes.append(_puntual_a_semanal(df_cafe, fecha_snapshot))

    df_precio_interno = precio_interno.obtener()
    partes.append(_puntual_a_semanal(df_precio_interno, fecha_snapshot))

    df_clima = clima.obtener()
    partes.append(_agregar_clima(df_clima, fecha_snapshot))

    partes_con_datos = [p for p in partes if not p.empty]
    if not partes_con_datos:
        print("  AVISO: todas las fuentes devolvieron vacío; snapshot no guardado.")
        return pd.DataFrame(columns=COLUMNAS)

    tabla = pd.concat(partes_con_datos, ignore_index=True)

    DIR_SNAPSHOTS.mkdir(parents=True, exist_ok=True)
    ruta = DIR_SNAPSHOTS / f"snapshot_{fecha_snapshot}.csv"
    tabla.to_csv(ruta, index=False, encoding="utf-8")
    print(f"  Snapshot guardado: {ruta}  ({len(tabla)} filas)")

    return tabla


if __name__ == "__main__":
    tabla = unir()
    print("\nprocesar.unir — resultado")
    print(f"  shape : {tabla.shape}")
    print(f"  tipos :\n{tabla.dtypes}")
    print(f"\n{tabla.to_string(max_rows=30)}")
