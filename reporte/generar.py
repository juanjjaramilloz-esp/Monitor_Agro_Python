"""Genera un brief ejecutivo neutral y trazable a partir de las series visuales."""

from datetime import date

import pandas as pd

from config import CATALOGO_VARIABLES, FUENTES_COMERCIALES
from procesar.proyeccion import ModeloPrecioFNC, ResultadoEscenario


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
    modelo: ModeloPrecioFNC,
    precio_fnc_observado: float,
    fecha_precio_fnc: date | pd.Timestamp,
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
        "| Variable | Valor |",
        "| --- | --- |",
        f"| Último precio FNC observado | {_numero(precio_fnc_observado, 0)} "
        f"COP/carga ({f_fnc:%d/%m/%Y}) |",
        f"| Tasa de cambio USD/COP del escenario | {_numero(tasa_cambio_escenario, 2)} |",
        f"| Café ICE Coffee C del escenario | {_numero(precio_ny_escenario, 2)} US¢/lb |",
        f"| Costo de producción | {_numero(costo_produccion, 0)} COP/carga |",
        f"| Volumen | {cargas} carga{plural} de 125 kg |",
        *(
            [
                f"| Factor de rendimiento | {_numero(factor_rendimiento, 0)} "
                f"(referencia {_numero(factor_referencia, 0)}) |"
            ]
            if factor_rendimiento is not None and factor_referencia is not None
            else []
        ),
        "",
        "## Resultados",
        "",
        f"- Precio interno FNC estimado: {_cop(resultado.precio_fnc_estimado)} por carga "
        f"({_numero(resultado.diferencia_fnc_observado_pct, 1)}% frente al último observado).",
        f"- Margen bruto por carga: {_cop(resultado.margen_por_carga)} "
        f"({_numero(resultado.margen_sobre_ingreso_pct, 1)}% del ingreso).",
        f"- Ingreso por {cargas} carga{plural}: {_cop(resultado.ingreso_total)}.",
        f"- Costo total supuesto: {_cop(resultado.costo_total)}.",
        f"- Margen bruto total: {_cop(resultado.margen_total)} ({retorno}).",
        "",
        "## Metodología",
        "",
        "Precio FNC estimado = USD/COP escenario × Coffee C escenario × "
        "coeficiente calibrado"
        + (
            " × (factor referencia ÷ factor de rendimiento)"
            if factor_rendimiento is not None and factor_referencia is not None
            else ""
        )
        + ".",
        "",
        (
            f"El coeficiente se deriva del precio interno, Coffee C y TRM que la FNC "
            f"publicó conjuntamente el {modelo.fecha_fin_calibracion:%d/%m/%Y}."
            if modelo.calibracion_oficial
            else (
                f"El coeficiente se calibra con {modelo.observaciones_calibracion} fechas "
                f"comparables recientes ({modelo.fecha_inicio_calibracion:%d/%m/%Y} a "
                f"{modelo.fecha_fin_calibracion:%d/%m/%Y}) y pondera más las "
                "observaciones más nuevas."
            )
        )
        + " El ajuste por factor de rendimiento es aproximado, no la fórmula "
        "oficial de la FNC. El margen bruto resta el costo por carga editable y lo "
        "multiplica por el número de cargas.",
        "",
        "## Alcance y limitaciones",
        "",
        f"- Validación caminando: error absoluto medio de "
        f"{_numero(modelo.error_absoluto_medio, 0)} COP/carga "
        f"({_numero(modelo.error_porcentual_medio, 2)}%) sobre "
        f"{modelo.observaciones_validacion} observaciones.",
        "- Es una estimación estadística; el precio FNC observado no se usa como entrada ni piso.",
        "- Margen bruto, antes de impuestos, logística, financiación, prima por calidad y "
        "otros costos no incluidos.",
        "- No modela prima, calidad, pasilla ni acopio por separado.",
        f"- Costo de referencia nacional ({costo_fuente}): {_numero(costo_referencia, 0)} "
        f"COP/carga, dato de {pd.Timestamp(costo_fecha):%m/%Y}; editable porque no "
        "representa cada finca.",
        "",
    ]
    return "\n".join(lineas)
