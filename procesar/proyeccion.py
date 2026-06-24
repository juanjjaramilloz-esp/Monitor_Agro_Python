"""Simulación transparente de escenarios para precio interno y margen."""

from dataclasses import dataclass

import pandas as pd


VARIABLES_BASE = {
    "precio_fnc": "precio_interno_referencia",
    "tasa_cambio": "fx_usd_local",
    "precio_ny": "precio_cafe_arabica",
}


@dataclass(frozen=True)
class BasesProyeccion:
    """Últimas observaciones disponibles usadas para anclar el escenario."""

    precio_fnc: float
    tasa_cambio: float
    precio_ny: float
    fecha_precio_fnc: pd.Timestamp
    fecha_tasa_cambio: pd.Timestamp
    fecha_precio_ny: pd.Timestamp


@dataclass(frozen=True)
class ResultadoEscenario:
    """Resultados económicos simples para un conjunto de supuestos."""

    precio_fnc_proyectado: float
    cambio_precio_fnc_pct: float
    ingreso_total: float
    costo_total: float
    margen_por_carga: float
    margen_total: float
    margen_sobre_ingreso_pct: float
    retorno_sobre_costo_pct: float


def obtener_bases(tabla: pd.DataFrame) -> BasesProyeccion:
    """Extrae la última observación válida de cada serie requerida."""
    valores: dict[str, tuple[float, pd.Timestamp]] = {}
    for nombre, variable in VARIABLES_BASE.items():
        serie = tabla[tabla["variable"].eq(variable)].copy()
        if serie.empty:
            raise ValueError(f"proyeccion: falta la serie {variable}")
        serie["fecha_dato"] = pd.to_datetime(serie["fecha_dato"], errors="coerce")
        serie["valor"] = pd.to_numeric(serie["valor"], errors="coerce")
        serie = serie.dropna(subset=["fecha_dato", "valor"]).sort_values("fecha_dato")
        if serie.empty:
            raise ValueError(f"proyeccion: la serie {variable} no tiene datos válidos")
        ultima = serie.iloc[-1]
        valores[nombre] = (float(ultima["valor"]), pd.Timestamp(ultima["fecha_dato"]))

    return BasesProyeccion(
        precio_fnc=valores["precio_fnc"][0],
        tasa_cambio=valores["tasa_cambio"][0],
        precio_ny=valores["precio_ny"][0],
        fecha_precio_fnc=valores["precio_fnc"][1],
        fecha_tasa_cambio=valores["tasa_cambio"][1],
        fecha_precio_ny=valores["precio_ny"][1],
    )


def proyectar_precio_fnc(
    precio_fnc_base: float,
    tasa_cambio_base: float,
    precio_ny_base: float,
    tasa_cambio_escenario: float,
    precio_ny_escenario: float,
) -> float:
    """
    Desplaza el precio FNC proporcionalmente al producto Coffee C × USD/COP.

    El precio FNC observado sirve como ancla. La prima, calidad, pasilla,
    factor de rendimiento y costos de acopio no se modelan por separado.
    """
    valores = [
        precio_fnc_base,
        tasa_cambio_base,
        precio_ny_base,
        tasa_cambio_escenario,
        precio_ny_escenario,
    ]
    if any(valor <= 0 for valor in valores):
        raise ValueError("proyeccion: todos los precios y tasas deben ser positivos")
    factor_fx = tasa_cambio_escenario / tasa_cambio_base
    factor_cafe = precio_ny_escenario / precio_ny_base
    return float(precio_fnc_base * factor_fx * factor_cafe)


def calcular_escenario(
    precio_fnc_base: float,
    tasa_cambio_base: float,
    precio_ny_base: float,
    tasa_cambio_escenario: float,
    precio_ny_escenario: float,
    costo_produccion_carga: float,
    cargas: int,
) -> ResultadoEscenario:
    """Calcula precio proyectado, ingresos, costos y margen bruto estimado."""
    if costo_produccion_carga < 0:
        raise ValueError("proyeccion: el costo de producción no puede ser negativo")
    if cargas <= 0:
        raise ValueError("proyeccion: cargas debe ser positivo")

    precio = proyectar_precio_fnc(
        precio_fnc_base,
        tasa_cambio_base,
        precio_ny_base,
        tasa_cambio_escenario,
        precio_ny_escenario,
    )
    margen_carga = precio - costo_produccion_carga
    ingreso_total = precio * cargas
    costo_total = costo_produccion_carga * cargas
    margen_total = margen_carga * cargas
    cambio_pct = (precio / precio_fnc_base - 1) * 100
    margen_ingreso = margen_carga / precio * 100 if precio else 0.0
    retorno_costo = (
        margen_carga / costo_produccion_carga * 100
        if costo_produccion_carga
        else float("nan")
    )
    return ResultadoEscenario(
        precio_fnc_proyectado=precio,
        cambio_precio_fnc_pct=cambio_pct,
        ingreso_total=ingreso_total,
        costo_total=costo_total,
        margen_por_carga=margen_carga,
        margen_total=margen_total,
        margen_sobre_ingreso_pct=margen_ingreso,
        retorno_sobre_costo_pct=retorno_costo,
    )


def crear_matriz_sensibilidad(
    precio_fnc_base: float,
    tasa_cambio_base: float,
    precio_ny_base: float,
    tasas_cambio: list[float],
    precios_ny: list[float],
) -> pd.DataFrame:
    """Construye una matriz de precios FNC proyectados para dos variables."""
    filas = []
    for precio_ny in precios_ny:
        for tasa_cambio in tasas_cambio:
            filas.append(
                {
                    "precio_ny": float(precio_ny),
                    "tasa_cambio": float(tasa_cambio),
                    "precio_fnc_proyectado": proyectar_precio_fnc(
                        precio_fnc_base,
                        tasa_cambio_base,
                        precio_ny_base,
                        tasa_cambio,
                        precio_ny,
                    ),
                }
            )
    return pd.DataFrame(filas)
