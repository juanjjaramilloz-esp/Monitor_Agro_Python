"""Genera un brief ejecutivo neutral y trazable a partir de las series visuales."""

from datetime import date

import pandas as pd

from config import CATALOGO_VARIABLES, FUENTES_COMERCIALES


VARIABLES_BRIEF = [
    "precio_interno_referencia",
    "precio_cafe_arabica",
    "fx_usd_local",
    "produccion_nacional",
]


def _numero(valor: float, decimales: int = 1) -> str:
    texto = f"{valor:,.{decimales}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


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
        "# Brief de consulta — Monitor Agro Colombia",
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
