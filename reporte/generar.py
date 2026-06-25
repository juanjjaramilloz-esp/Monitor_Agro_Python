"""Genera un brief ejecutivo neutral y trazable a partir de las series visuales."""

from datetime import date

import pandas as pd

from config import CATALOGO_VARIABLES, FUENTES_COMERCIALES
from procesar.proyeccion import ResultadoEscenario


VARIABLES_BRIEF = [
    "precio_interno_referencia",
    "precio_cafe_arabica",
    "fx_usd_local",
    "produccion_nacional",
]


def _numero(valor: float, decimales: int = 1) -> str:
    texto = f"{valor:,.{decimales}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def _cop(valor: float) -> str:
    return f"{_numero(valor, 0)} COP"


def _porcentaje(valor: float | None) -> str:
    if valor is None or pd.isna(valor):
        return "sin dato comparable"
    return f"{_numero(float(valor), 1)}%"


def _cambio_entre(primero: float, ultimo: float) -> float | None:
    if primero == 0:
        return None
    return (ultimo / primero - 1) * 100


def _cambio_observaciones(
    serie: pd.DataFrame,
    fecha_actual: pd.Timestamp,
    periodos: int,
) -> float | None:
    ordenada = serie.sort_values("fecha_dato").reset_index(drop=True)
    posiciones = ordenada.index[ordenada["fecha_dato"].eq(fecha_actual)]
    if len(posiciones) == 0 or posiciones[-1] < periodos:
        return None
    posicion = int(posiciones[-1])
    anterior = float(ordenada.iloc[posicion - periodos]["valor"])
    return _cambio_entre(anterior, float(ordenada.iloc[posicion]["valor"]))


def _lineas_serie(
    tabla_completa: pd.DataFrame,
    periodo: pd.DataFrame,
    variable: str,
) -> list[str]:
    metadatos = CATALOGO_VARIABLES[variable]
    fuente = FUENTES_COMERCIALES[variable]
    completa = tabla_completa[tabla_completa["variable"].eq(variable)].sort_values(
        "fecha_dato"
    )
    seleccion = periodo[periodo["variable"].eq(variable)].sort_values("fecha_dato")
    etiqueta = metadatos["etiqueta"]
    if seleccion.empty:
        return [
            f"### {etiqueta}",
            "",
            "- Sin dato publicado dentro del periodo seleccionado.",
            f"- Cadencia: {completa.iloc[-1]['cadencia'] if not completa.empty else 'sin dato'}.",
            f"- Fuente: {fuente['nombre']}.",
            "",
        ]

    primera = seleccion.iloc[0]
    ultima = seleccion.iloc[-1]
    decimales = int(metadatos["decimales"])
    cambio_periodo = _cambio_entre(float(primera["valor"]), float(ultima["valor"]))
    fecha_ultima = pd.Timestamp(ultima["fecha_dato"])
    lineas = [
        f"### {etiqueta}",
        "",
        f"- Valor más reciente: {_numero(float(ultima['valor']), decimales)} {ultima['unidad']}.",
        f"- Fecha del dato: {fecha_ultima:%d/%m/%Y}.",
        f"- Variación dentro del periodo: {_porcentaje(cambio_periodo)}.",
    ]
    if variable == "produccion_nacional":
        lineas.extend(
            [
                f"- Variación mensual: {_porcentaje(ultima['cambio_1m_pct'])}.",
                f"- Variación interanual: {_porcentaje(ultima['cambio_12m_pct'])}.",
            ]
        )
    else:
        lineas.extend(
            [
                f"- Variación semanal: {_porcentaje(ultima['cambio_1s_pct'])}.",
                f"- Variación de 4 semanas: {_porcentaje(ultima['cambio_4s_pct'])}.",
                f"- Variación anual (52 observaciones): "
                f"{_porcentaje(_cambio_observaciones(completa, fecha_ultima, 52))}.",
            ]
        )
    lineas.extend(
        [
            f"- Cadencia: {ultima['cadencia']}.",
            f"- Fuente: {fuente['nombre']}.",
            f"- Cobertura disponible: "
            f"{pd.Timestamp(completa['fecha_dato'].min()):%d/%m/%Y} a "
            f"{pd.Timestamp(completa['fecha_dato'].max()):%d/%m/%Y}.",
            "",
        ]
    )
    return lineas


def _lectura_conjunta(periodo: pd.DataFrame) -> list[str]:
    lineas = [
        "## Lectura conjunta neutral",
        "",
        "Movimientos observados dentro del periodo; no implican causalidad:",
        "",
    ]
    for variable in VARIABLES_BRIEF[:3]:
        serie = periodo[periodo["variable"].eq(variable)].sort_values("fecha_dato")
        etiqueta = CATALOGO_VARIABLES[variable]["etiqueta"]
        if len(serie) < 2:
            lineas.append(f"- {etiqueta}: sin dos observaciones comparables.")
            continue
        cambio = _cambio_entre(float(serie.iloc[0]["valor"]), float(serie.iloc[-1]["valor"]))
        if cambio is None:
            lineas.append(f"- {etiqueta}: sin comparación válida.")
            continue
        direccion = "subió" if cambio > 0 else "bajó" if cambio < 0 else "no cambió"
        lineas.append(f"- {etiqueta}: {direccion} {_numero(abs(cambio), 1)}%.")
    lineas.extend(["", ""])
    return lineas


def generar(
    tabla: pd.DataFrame,
    inicio: date | pd.Timestamp,
    fin: date | pd.Timestamp,
    fecha_generacion: date | None = None,
) -> str:
    """Genera un brief Markdown para el rango inclusivo solicitado."""
    if fecha_generacion is None:
        fecha_generacion = date.today()
    datos = tabla.copy()
    datos["semana_fin"] = pd.to_datetime(datos["semana_fin"])
    datos["fecha_dato"] = pd.to_datetime(datos["fecha_dato"])
    inicio_ts = pd.Timestamp(inicio)
    fin_ts = pd.Timestamp(fin)
    if inicio_ts > fin_ts:
        raise ValueError("brief: inicio no puede ser posterior a fin")

    periodo = datos[
        datos["variable"].isin(VARIABLES_BRIEF)
        & datos["semana_fin"].between(inicio_ts, fin_ts)
    ].copy()
    lineas = [
        "# Brief de consulta — Herramienta Consultas y Reportes",
        "",
        f"**Periodo seleccionado:** {inicio_ts:%d/%m/%Y} a {fin_ts:%d/%m/%Y}  ",
        f"**Fecha de generación:** {fecha_generacion:%d/%m/%Y}",
        "",
        "## Resumen por serie",
        "",
    ]
    for variable in VARIABLES_BRIEF:
        lineas.extend(_lineas_serie(datos, periodo, variable))
    lineas.extend(_lectura_conjunta(periodo))
    lineas.extend(
        [
            "## Alcance y limitaciones",
            "",
            "- La producción nacional se publica mensualmente y no se rellena como dato semanal.",
            "- El clima usa una coordenada municipal de referencia y no representa toda la variación departamental.",
            "- Algunas series dependen de scraping o archivos descargables que pueden cambiar de estructura.",
            "- El brief describe movimientos estadísticos; no asigna oportunidad, riesgo ni causalidad.",
            "",
        ]
    )
    return "\n".join(lineas)


def generar_informe_simulador(
    *,
    precio_fnc_base: float,
    tasa_cambio_base: float,
    precio_ny_base: float,
    fecha_precio_fnc: date | pd.Timestamp,
    fecha_tasa_cambio: date | pd.Timestamp,
    fecha_precio_ny: date | pd.Timestamp,
    tasa_cambio_escenario: float,
    precio_ny_escenario: float,
    costo_produccion: float,
    cargas: int,
    resultado: ResultadoEscenario,
    costo_referencia: float,
    costo_fecha: date | pd.Timestamp,
    costo_fuente: str,
    factor_rendimiento: float | None = None,
    factor_referencia: float | None = None,
    fecha_generacion: date | None = None,
) -> str:
    """Genera un informe Markdown con los supuestos y resultados del escenario."""
    if fecha_generacion is None:
        fecha_generacion = date.today()
    f_fnc = pd.Timestamp(fecha_precio_fnc)
    f_fx = pd.Timestamp(fecha_tasa_cambio)
    f_ny = pd.Timestamp(fecha_precio_ny)
    plural = "s" if cargas != 1 else ""
    retorno = (
        f"{_numero(resultado.retorno_sobre_costo_pct, 1)}% sobre costo"
        if not pd.isna(resultado.retorno_sobre_costo_pct)
        else "sin dato de retorno sobre costo"
    )
    lineas = [
        "# Informe del simulador — Herramienta Consultas y Reportes",
        "",
        f"**Fecha de generación:** {fecha_generacion:%d/%m/%Y}",
        "",
        "Escenario de exploración construido por la persona usuaria. No es un pronóstico.",
        "",
        "## Supuestos del escenario",
        "",
        "| Variable | Valor base | Escenario |",
        "| --- | --- | --- |",
        f"| Precio interno FNC (COP/carga 125 kg) | {_numero(precio_fnc_base, 0)} "
        f"({f_fnc:%d/%m/%Y}) | — |",
        f"| Tasa de cambio USD/COP | {_numero(tasa_cambio_base, 2)} ({f_fx:%d/%m/%Y}) | "
        f"{_numero(tasa_cambio_escenario, 2)} |",
        f"| Café ICE Coffee C (US¢/lb) | {_numero(precio_ny_base, 2)} ({f_ny:%d/%m/%Y}) | "
        f"{_numero(precio_ny_escenario, 2)} |",
        f"| Costo de producción (COP/carga 125 kg) | {_numero(costo_produccion, 0)} | — |",
        f"| Volumen (cargas de 125 kg) | {cargas} | — |",
        *(
            [
                f"| Factor de rendimiento | {_numero(factor_referencia, 0)} (referencia) "
                f"| {_numero(factor_rendimiento, 0)} |"
            ]
            if factor_rendimiento is not None and factor_referencia is not None
            else []
        ),
        "",
        "## Resultados",
        "",
        f"- Precio interno FNC proyectado: {_cop(resultado.precio_fnc_proyectado)} por carga "
        f"({_numero(resultado.cambio_precio_fnc_pct, 1)}% frente a la base).",
        f"- Margen bruto por carga: {_cop(resultado.margen_por_carga)} "
        f"({_numero(resultado.margen_sobre_ingreso_pct, 1)}% del ingreso).",
        f"- Ingreso por {cargas} carga{plural}: {_cop(resultado.ingreso_total)}.",
        f"- Costo total supuesto: {_cop(resultado.costo_total)}.",
        f"- Margen bruto total: {_cop(resultado.margen_total)} ({retorno}).",
        "",
        "## Metodología",
        "",
        "Precio FNC proyectado = precio FNC base × (USD/COP escenario ÷ USD/COP base) "
        "× (Coffee C escenario ÷ Coffee C base)"
        + (
            " × (factor referencia ÷ factor de rendimiento)"
            if factor_rendimiento is not None and factor_referencia is not None
            else ""
        )
        + ".",
        "",
        "El ajuste por factor de rendimiento es aproximado, no la fórmula oficial de "
        "la FNC. El margen bruto resta el costo por carga editable y lo multiplica por "
        "el número de cargas.",
        "",
        "## Alcance y limitaciones",
        "",
        "- No es un pronóstico: desplaza proporcionalmente el último precio FNC observado.",
        "- Margen bruto, antes de impuestos, logística, financiación, prima por calidad y "
        "otros costos no incluidos.",
        "- No modela prima, calidad, pasilla, factor de rendimiento ni acopio por separado.",
        f"- Costo de referencia nacional ({costo_fuente}): {_numero(costo_referencia, 0)} "
        f"COP/carga, dato de {pd.Timestamp(costo_fecha):%m/%Y}; editable porque no "
        "representa cada finca.",
        "",
    ]
    return "\n".join(lineas)
