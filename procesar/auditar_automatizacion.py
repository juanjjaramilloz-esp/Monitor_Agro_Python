"""Comprueba que una corrida automática dejó artefactos suficientemente frescos."""

import json
import os
from datetime import date
from pathlib import Path

import pandas as pd

from config import (
    ARCHIVO_COMENTARIO_IA,
    AUTOMATIZACION_MAX_RETRASO_CALIBRACION_DIAS,
    AUTOMATIZACION_MAX_RETRASO_COMENTARIO_DIAS,
    AUTOMATIZACION_MAX_RETRASO_DIARIO_DIAS,
    AUTOMATIZACION_MAX_RETRASO_SEMANAL_DIAS,
)
from procesar.calibracion_fnc import RUTA_CALIBRACION_FNC
from procesar.historico import RUTA_DIARIO, RUTA_SEMANAL

SERIES_DIARIAS_CRITICAS = [
    "fx_usd_local",
    "precio_cafe_arabica",
    "precio_interno_referencia",
    "precipitacion",
]
SERIES_SEMANALES_CRITICAS = [
    "fx_usd_local",
    "precio_cafe_arabica",
    "precio_interno_referencia",
    "precipitacion_semanal",
]


def _fecha_maxima(
    tabla: pd.DataFrame,
    columna_fecha: str,
    variable: str,
) -> date | None:
    """Devuelve la fecha máxima válida de una variable o None si falta."""
    if tabla.empty or not {columna_fecha, "variable"}.issubset(tabla.columns):
        return None
    fechas = pd.to_datetime(
        tabla.loc[tabla["variable"].eq(variable), columna_fecha],
        errors="coerce",
    ).dropna()
    return fechas.max().date() if not fechas.empty else None


def _comprobar_fecha(
    nombre: str,
    fecha: date | None,
    hoy: date,
    max_retraso: int,
    errores: list[str],
    fechas: dict[str, date | None],
) -> None:
    fechas[nombre] = fecha
    if fecha is None:
        errores.append(f"{nombre}: no tiene una fecha válida")
        return
    retraso = (hoy - fecha).days
    if retraso < 0:
        errores.append(f"{nombre}: fecha futura {fecha.isoformat()}")
    elif retraso > max_retraso:
        errores.append(
            f"{nombre}: último dato {fecha.isoformat()} ({retraso} días; máximo {max_retraso})"
        )


def evaluar_frescura(
    diario: pd.DataFrame,
    semanal: pd.DataFrame,
    calibracion: pd.DataFrame,
    fecha_comentario: date | None,
    hoy: date | None = None,
    auditar_comentario: bool = True,
) -> tuple[dict[str, date | None], list[str]]:
    """Evalúa fechas críticas sin leer ni escribir archivos."""
    hoy = hoy or date.today()
    fechas: dict[str, date | None] = {}
    errores: list[str] = []

    for variable in SERIES_DIARIAS_CRITICAS:
        _comprobar_fecha(
            f"diario/{variable}",
            _fecha_maxima(diario, "fecha", variable),
            hoy,
            AUTOMATIZACION_MAX_RETRASO_DIARIO_DIAS,
            errores,
            fechas,
        )
    for variable in SERIES_SEMANALES_CRITICAS:
        _comprobar_fecha(
            f"semanal/{variable}",
            _fecha_maxima(semanal, "semana_fin", variable),
            hoy,
            AUTOMATIZACION_MAX_RETRASO_SEMANAL_DIAS,
            errores,
            fechas,
        )

    fecha_calibracion = None
    if not calibracion.empty and "fecha" in calibracion:
        serie = pd.to_datetime(calibracion["fecha"], errors="coerce").dropna()
        fecha_calibracion = serie.max().date() if not serie.empty else None
    _comprobar_fecha(
        "calibracion_fnc",
        fecha_calibracion,
        hoy,
        AUTOMATIZACION_MAX_RETRASO_CALIBRACION_DIAS,
        errores,
        fechas,
    )
    if auditar_comentario:
        _comprobar_fecha(
            "comentario_ia",
            fecha_comentario,
            hoy,
            AUTOMATIZACION_MAX_RETRASO_COMENTARIO_DIAS,
            errores,
            fechas,
        )
    else:
        fechas["comentario_ia (sin secret configurado)"] = fecha_comentario
    return fechas, errores


def _leer_csv(ruta: Path) -> pd.DataFrame:
    if not ruta.exists():
        return pd.DataFrame()
    return pd.read_csv(ruta)


def _leer_fecha_comentario(ruta: Path = ARCHIVO_COMENTARIO_IA) -> date | None:
    try:
        contenido = json.loads(ruta.read_text(encoding="utf-8"))
        return pd.Timestamp(contenido["fecha_generacion"]).date()
    except (OSError, KeyError, ValueError, json.JSONDecodeError):
        return None


def main() -> None:
    auditar_comentario = os.environ.get("AUDITAR_COMENTARIO_IA", "true").lower() not in {
        "0",
        "false",
        "no",
    }
    fechas, errores = evaluar_frescura(
        _leer_csv(RUTA_DIARIO),
        _leer_csv(RUTA_SEMANAL),
        _leer_csv(RUTA_CALIBRACION_FNC),
        _leer_fecha_comentario(),
        auditar_comentario=auditar_comentario,
    )
    print("Salud de la automatización:")
    for nombre, fecha in fechas.items():
        valor = fecha.isoformat() if fecha else "SIN DATO"
        print(f"  {nombre}: {valor}")
    if errores:
        detalle = "\n".join(f"- {error}" for error in errores)
        raise SystemExit(f"Automatización sin frescura suficiente:\n{detalle}")
    print("Automatización saludable: todos los artefactos están dentro de tolerancia.")


if __name__ == "__main__":
    main()
