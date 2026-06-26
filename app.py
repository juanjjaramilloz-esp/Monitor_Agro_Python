"""Kit de consulta, reporte y simulación del Monitor Agro Colombia."""

from io import BytesIO
from math import ceil, floor
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config import (
    CATALOGO_VARIABLES,
    COLORES_INTERFAZ,
    COSTO_PRODUCCION_FECHA,
    COSTO_PRODUCCION_FUENTE,
    COSTO_PRODUCCION_REFERENCIA,
    COSTO_PRODUCCION_URL,
    FACTOR_RENDIMIENTO_RANGO,
    FACTOR_RENDIMIENTO_REFERENCIA,
    FUENTES_COMERCIALES,
    PERIODOS_VISUALIZACION,
    PROYECCION_CARGAS_MAXIMAS,
    PROYECCION_CARGAS_PREDETERMINADAS,
    PROYECCION_PUNTOS_MATRIZ,
    PROYECCION_RANGO_FACTOR_CAFE,
    PROYECCION_RANGO_FACTOR_FX,
)
from procesar.proyeccion import (
    ResultadoEscenario,
    calibrar_modelo,
    calcular_escenario,
    crear_matriz_sensibilidad,
    obtener_bases,
    obtener_bases_calibracion,
)
from procesar.historico import RUTA_DIARIO
from procesar.calibracion_fnc import RUTA_CALIBRACION_FNC
from procesar.visualizacion import (
    RUTA_SERIES,
    ejecutar as preparar_visualizacion,
    incorporar_referencia_comercial_actual,
    preparar_descarga_comercial,
    series_necesitan_regenerarse,
)
from reporte.generar import generar_informe_simulador
from reporte.pdf import generar_pdf_brief


CONFIG_GRAFICO = {
    "displaylogo": False,
    "responsive": True,
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
}


# Paso de los botones +/- del simulador: la tasa de cambio se mueve de a 20 COP
# y el Coffee C de a 2,5 US¢/lb, escalas legibles para el escenario.
PASO_FX = 20.0
PASO_CAFE = 2.5


# Las fuentes usan unidades "de máquina" en el contrato de datos; aquí se
# traducen a etiquetas legibles solo al mostrarlas, sin tocar el esquema.
UNIDADES_LEGIBLES = {
    "COP/carga_125kg": "COP/carga",
    "USc/lb": "US¢/lb",
}


def _unidad_legible(unidad: str) -> str:
    """Traduce la unidad técnica del contrato a una etiqueta legible en la UI."""
    return UNIDADES_LEGIBLES.get(unidad, unidad)


# --- Internacionalización (español / inglés) ------------------------------
# La interfaz es bilingüe. El selector de idioma fija `IDIOMA` ("es"/"en") y
# todos los textos visibles salen de `TEXTOS` vía `_t()`. Las etiquetas de
# datos que viven en español en `config.py` (nombres de indicadores, fuentes,
# cadencias, métodos) se traducen aquí con mapas de presentación, sin tocar el
# contrato ni los CSV. Los números ya se formatean por idioma en `_numero` y en
# los separadores de Plotly; las fechas se mantienen en dd/mm/aaaa en ambos.
IDIOMAS = {"Español": "es", "English": "en"}
IDIOMA = "es"

TEXTOS = {
    "titulo": {
        "es": "Herramienta Consultas y Reportes",
        "en": "Consultation and Reporting Tool",
    },
    "subtitulo": {
        "es": (
            "Kit de consulta y reporte para integrar, comparar y exportar "
            "evidencia comercial del café colombiano · {semanas} semanas "
            "cerradas hasta {ultima} · referencia comercial al {referencia}"
        ),
        "en": (
            "Consultation and reporting kit to integrate, compare and export "
            "commercial evidence on Colombian coffee · {semanas} closed weeks "
            "through {ultima} · commercial reference as of {referencia}"
        ),
    },
    "introduccion": {
        "es": (
            "Explore series para análisis, informes y reuniones. El panorama "
            "nacional permite leer conjuntamente precio interno FNC, Coffee C y "
            "USD/COP, y el simulador estima precio interno y margen bajo "
            "distintos supuestos."
        ),
        "en": (
            "Explore the series for analysis, reports and meetings. The "
            "national overview reads the FNC internal price, Coffee C and "
            "USD/COP together, and the simulator estimates the internal price "
            "and margin under different assumptions."
        ),
    },
    "filtros": {"es": "Filtros", "en": "Filters"},
    # --- Barra lateral ---
    "rango_analisis": {"es": "Rango de análisis", "en": "Analysis range"},
    "periodo_predefinido": {"es": "Periodo predefinido", "en": "Preset period"},
    "fechas_personalizadas": {"es": "Fechas personalizadas", "en": "Custom dates"},
    "periodo": {"es": "Periodo", "en": "Period"},
    "fechas_cierre": {"es": "Fechas de cierre", "en": "Closing dates"},
    "autor": {"es": "Autor: Juan José Jaramillo", "en": "Author: Juan José Jaramillo"},
    # --- Pestañas ---
    "tab_panorama": {"es": "Panorama nacional", "en": "National overview"},
    "tab_simulador": {"es": "Simulador", "en": "Simulator"},
    # --- Panorama ---
    "sub_lectura": {"es": "Lectura conjunta comercial", "en": "Joint commercial reading"},
    "cap_lectura": {
        "es": (
            "Movimiento descriptivo de las tres series. Las variaciones no "
            "implican causalidad ni califican el resultado como favorable o "
            "desfavorable."
        ),
        "en": (
            "Descriptive movement of the three series. The changes imply no "
            "causality and do not qualify the result as favorable or "
            "unfavorable."
        ),
    },
    "cap_base100": {
        "es": (
            "Índice base 100 desde enero de 2023: permite comparar dirección y "
            "magnitud relativa entre series con unidades distintas."
        ),
        "en": (
            "Base-100 index since January 2023: lets you compare direction and "
            "relative magnitude across series with different units."
        ),
    },
    "md_variaciones": {"es": "**Variaciones por indicador**", "en": "**Changes by indicator**"},
    "sub_prodexp": {
        "es": "Producción y exportaciones mensuales",
        "en": "Monthly production and exports",
    },
    "sub_exportar": {
        "es": "Exportar para informes y reuniones",
        "en": "Export for reports and meetings",
    },
    "btn_excel": {
        "es": "Descargar series comerciales (Excel)",
        "en": "Download commercial series (Excel)",
    },
    "help_excel": {
        "es": "Incluye valores, variaciones, unidad, fuente, alcance y fecha real del dato.",
        "en": "Includes values, changes, unit, source, scope and the real data date.",
    },
    "btn_pdf": {
        "es": "Descargar brief del periodo (PDF)",
        "en": "Download period brief (PDF)",
    },
    "help_pdf": {
        "es": "Documento con las gráficas, las variaciones y las fuentes del periodo.",
        "en": "Document with the period's charts, changes and sources.",
    },
    "exp_cobertura": {
        "es": "Cobertura y metodología comercial",
        "en": "Commercial coverage and methodology",
    },
    "md_cobertura": {
        "es": (
            "Las tres series se comparan semanalmente, pero conservan su unidad "
            "y la fecha real del dato. El índice base 100 facilita comparar "
            "tendencias; no convierte las variables a una misma unidad ni "
            "demuestra causalidad."
        ),
        "en": (
            "The three series are compared weekly, but keep their unit and the "
            "real data date. The base-100 index helps compare trends; it does "
            "not convert the variables to a common unit nor prove causality."
        ),
    },
    # --- Métricas de mercado / comparación ---
    "comparar_variacion": {"es": "Comparar variación", "en": "Compare change"},
    "opt_mensual": {"es": "Mensual", "en": "Monthly"},
    "opt_semanal": {"es": "Semanal", "en": "Weekly"},
    "help_comparar": {
        "es": (
            "Mensual compara el último valor con el de hace ~4 semanas; "
            "Semanal lo compara con el cierre de la semana anterior."
        ),
        "en": (
            "Monthly compares the latest value with the one ~4 weeks ago; "
            "Weekly compares it with the previous week's close."
        ),
    },
    "vs_semana_anterior": {"es": "vs semana anterior", "en": "vs previous week"},
    "vs_mes_anterior": {"es": "vs mes anterior", "en": "vs previous month"},
    # --- Tabla de variaciones ---
    "col_indicador": {"es": "Indicador", "en": "Indicator"},
    "col_semanal": {"es": "Semanal", "en": "Weekly"},
    "col_mensual_4": {"es": "Mensual (4 sem.)", "en": "Monthly (4 wks)"},
    "col_anual_52": {"es": "Anual (52 sem.)", "en": "Yearly (52 wks)"},
    "sin_dato": {"es": "Sin dato", "en": "No data"},
    # --- Producción y exportaciones ---
    "info_no_prod": {
        "es": "No hay un dato mensual de producción publicado dentro del periodo elegido.",
        "en": "No monthly production figure published within the selected period.",
    },
    "metric_prod": {
        "es": "Producción nacional · mensual",
        "en": "National production · monthly",
    },
    "unid_mil_sacos": {"es": "mil sacos de 60 kg", "en": "thousand 60 kg bags"},
    "help_prod": {
        "es": "Producción registrada de café verde equivalente publicada por la FNC.",
        "en": "Registered green-equivalent coffee production published by the FNC.",
    },
    "metric_mes_dato": {"es": "Mes del dato", "en": "Data month"},
    "delta_vs_mes": {
        "es": "{cambio}% frente al mes anterior",
        "en": "{cambio}% vs previous month",
    },
    "cambio_interanual": {
        "es": "**Cambio interanual:** ",
        "en": "**Year-on-year change:** ",
    },
    "fuente_fnc": {"es": "**Fuente:** FNC", "en": "**Source:** FNC"},
    "info_no_exp": {
        "es": "No hay exportaciones mensuales publicadas dentro del periodo elegido.",
        "en": "No monthly exports published within the selected period.",
    },
    "info_no_meses": {
        "es": "No hay meses comunes para comparar producción y exportaciones.",
        "en": "No common months to compare production and exports.",
    },
    "prod_no_exportada": {
        "es": "Producción no exportada en el mismo mes",
        "en": "Production not exported in the same month",
    },
    "exp_sobre_prod": {
        "es": "Exportaciones por encima de la producción del mes",
        "en": "Exports above the month's production",
    },
    "help_diferencia": {
        "es": (
            "Diferencia descriptiva entre dos flujos mensuales. No equivale a "
            "inventario: puede incluir café producido en otros meses, rezagos "
            "logísticos y diferencias de registro."
        ),
        "en": (
            "Descriptive difference between two monthly flows. It is not "
            "inventory: it may include coffee produced in other months, "
            "logistical lags and registration differences."
        ),
    },
    "cap_diferencia": {
        "es": (
            "Un valor positivo indica producción superior a las exportaciones "
            "del mismo mes; uno negativo indica exportaciones superiores. La "
            "diferencia no mide directamente reservas ni consumo interno."
        ),
        "en": (
            "A positive value means production above exports in the same month; "
            "a negative one means exports above production. The difference does "
            "not directly measure reserves or domestic consumption."
        ),
    },
    # --- Tabla de cobertura ---
    "col_ultimo_dato": {"es": "Último dato", "en": "Latest data"},
    "col_unidad": {"es": "Unidad", "en": "Unit"},
    "col_fuente": {"es": "Fuente", "en": "Source"},
    "col_alcance": {"es": "Alcance", "en": "Scope"},
    "col_cadencia": {"es": "Cadencia", "en": "Cadence"},
    "col_tratamiento": {"es": "Tratamiento semanal", "en": "Weekly treatment"},
    # --- Pie de página ---
    "foot_fuentes": {
        "es": (
            "Fuentes: FNC, Open-Meteo y Yahoo Finance vía yfinance. "
            "Visualización exploratoria; no contiene score de oportunidad o riesgo."
        ),
        "en": (
            "Sources: FNC, Open-Meteo and Yahoo Finance via yfinance. "
            "Exploratory visualization; it contains no opportunity or risk score."
        ),
    },
    "foot_copyright": {
        "es": "© 2026 Juan José Jaramillo · Todos los derechos reservados.",
        "en": "© 2026 Juan José Jaramillo · All rights reserved.",
    },
    # --- Gráficas ---
    "chart_mercado_titulo": {
        "es": "Evolución comercial comparable · base 100",
        "en": "Comparable commercial evolution · base 100",
    },
    "hov_indice": {"es": "Índice", "en": "Index"},
    "hov_valor": {"es": "Valor", "en": "Value"},
    "chart_prod_titulo": {
        "es": "Producción nacional registrada · una barra por mes",
        "en": "Registered national production · one bar per month",
    },
    "name_prod": {"es": "Producción mensual", "en": "Monthly production"},
    "chart_exp_titulo": {
        "es": "Exportaciones colombianas de café · una barra por mes",
        "en": "Colombian coffee exports · one bar per month",
    },
    "name_exp": {"es": "Exportaciones mensuales", "en": "Monthly exports"},
    "chart_dif_titulo": {
        "es": "Diferencia mensual · producción menos exportaciones",
        "en": "Monthly difference · production minus exports",
    },
    "hov_produccion": {"es": "Producción", "en": "Production"},
    "hov_exportaciones": {"es": "Exportaciones", "en": "Exports"},
    "hov_diferencia": {"es": "Diferencia", "en": "Difference"},
    "hov_mil_sacos": {"es": "mil sacos", "en": "thousand bags"},
    "yaxis_miles_sacos": {
        "es": "Miles de sacos de 60 kg",
        "en": "Thousand 60 kg bags",
    },
    "chart_resultado_titulo": {
        "es": "Precio y costo por carga de 125 kg",
        "en": "Price and cost per 125 kg load",
    },
    "barra_costo_medio": {"es": "Costo medio", "en": "Average cost"},
    "barra_ultimo_fnc": {"es": "Último FNC observado", "en": "Last observed FNC"},
    "barra_precio_estimado": {"es": "Precio estimado", "en": "Estimated price"},
    "hov_cop_carga": {"es": "COP/carga", "en": "COP/load"},
    "chart_sens_titulo": {
        "es": "Mapa de sensibilidad del precio FNC estimado",
        "en": "Sensitivity map of the estimated FNC price",
    },
    "sens_xaxis": {
        "es": "Tasa de cambio (COP/USD)",
        "en": "Exchange rate (COP/USD)",
    },
    "sens_yaxis": {"es": "Coffee C (US¢/lb)", "en": "Coffee C (US¢/lb)"},
    "hov_precio_fnc_estimado": {
        "es": "Precio FNC estimado",
        "en": "Estimated FNC price",
    },
    "name_escenario": {"es": "Escenario elegido", "en": "Chosen scenario"},
    # --- Simulador ---
    "sub_estimador": {
        "es": "Estimador de precio interno y margen",
        "en": "Internal price and margin estimator",
    },
    "cap_estimador": {
        "es": (
            "Ingrese supuestos de Coffee C y USD/COP para estimar el precio "
            "interno FNC. El precio FNC observado ya no es una entrada ni "
            "funciona como piso."
        ),
        "en": (
            "Enter Coffee C and USD/COP assumptions to estimate the FNC "
            "internal price. The observed FNC price is no longer an input nor a "
            "floor."
        ),
    },
    "exp_calibracion": {
        "es": "Calibración y metodología",
        "en": "Calibration and methodology",
    },
    "calib_oficial": {
        "es": (
            "Calibración oficial FNC del {fecha}: precio interno, Coffee C y TRM "
            "publicados juntos para evitar mezclar fuentes u horas de cierre. Si "
            "esa referencia falla, el respaldo estadístico tiene un error "
            "histórico medio de ${mae} por carga ({mape}%)."
        ),
        "en": (
            "Official FNC calibration of {fecha}: internal price, Coffee C and "
            "TRM published together to avoid mixing sources or closing times. If "
            "that reference fails, the statistical fallback has a mean historical "
            "error of ${mae} per load ({mape}%)."
        ),
    },
    "calib_respaldo": {
        "es": (
            "Calibración de respaldo: {obs} fechas comparables, de {inicio} a "
            "{fin}. Validación caminando sobre {val} observaciones: error "
            "absoluto medio ${mae} por carga ({mape}%)."
        ),
        "en": (
            "Fallback calibration: {obs} comparable dates, from {inicio} to "
            "{fin}. Walk-forward validation over {val} observations: mean "
            "absolute error ${mae} per load ({mape}%)."
        ),
    },
    "formula": {
        "es": (
            "**Fórmula:** USD/COP escenario × Coffee C escenario × coeficiente "
            "calibrado × (factor referencia ÷ factor de rendimiento). El "
            "coeficiente se recalcula con los últimos datos diarios comparables y "
            "pondera más los recientes. Resume prima, conversiones y otros "
            "componentes que no se modelan por separado; no reproduce la fórmula "
            "oficial de la FNC."
        ),
        "en": (
            "**Formula:** scenario USD/COP × scenario Coffee C × calibrated "
            "coefficient × (reference factor ÷ yield factor). The coefficient is "
            "recomputed with the latest comparable daily data and weights recent "
            "points more. It summarizes premium, conversions and other "
            "components not modeled separately; it does not reproduce the FNC's "
            "official formula."
        ),
    },
    "ctrl_tasa": {
        "es": "Tasa de cambio del escenario · COP/USD",
        "en": "Scenario exchange rate · COP/USD",
    },
    "ctrl_coffee": {
        "es": "Coffee C del escenario · US¢/lb",
        "en": "Scenario Coffee C · US¢/lb",
    },
    "cap_dos_campos": {
        "es": (
            "Escriba los valores del escenario en estos dos campos. El mapa de "
            "sensibilidad de abajo es para explorar: pase el mouse sobre cada "
            "celda para ver el precio estimado."
        ),
        "en": (
            "Type the scenario values in these two fields. The sensitivity map "
            "below is for exploring: hover over each cell to see the estimated "
            "price."
        ),
    },
    "ctrl_costo": {
        "es": "Costo de producción · COP por carga de 125 kg",
        "en": "Production cost · COP per 125 kg load",
    },
    "help_costo": {
        "es": "Referencia nacional FEPCafé; edítela para representar otro supuesto.",
        "en": "FEPCafé national reference; edit it to represent another assumption.",
    },
    "ctrl_volumen": {
        "es": "Volumen del escenario · cargas de 125 kg",
        "en": "Scenario volume · 125 kg loads",
    },
    "ctrl_factor": {"es": "Factor de rendimiento", "en": "Yield factor"},
    "help_factor": {
        "es": (
            "Kg de café pergamino seco por carga de excelso; 94 es la referencia "
            "FNC. Un factor menor (mejor rendimiento) sube el precio recibido; "
            "uno mayor lo baja. Ajuste aproximado, no la fórmula oficial."
        ),
        "en": (
            "Kg of dry parchment coffee per load of excelso; 94 is the FNC "
            "reference. A lower factor (better yield) raises the received price; "
            "a higher one lowers it. Approximate adjustment, not the official "
            "formula."
        ),
    },
    "btn_restablecer": {
        "es": "↺ Restablecer valores predeterminados",
        "en": "↺ Reset to defaults",
    },
    "help_restablecer": {
        "es": "Vuelve los controles del escenario a los últimos valores disponibles.",
        "en": "Returns the scenario controls to the latest available values.",
    },
    "metric_precio_estimado": {"es": "Precio FNC estimado", "en": "Estimated FNC price"},
    "delta_vs_observado": {
        "es": "{valor}% frente al último observado",
        "en": "{valor}% vs the last observed",
    },
    "metric_margen_carga": {
        "es": "Margen bruto por carga",
        "en": "Gross margin per load",
    },
    "delta_del_ingreso": {"es": "{valor}% del ingreso", "en": "{valor}% of revenue"},
    "metric_margen_total": {"es": "Margen bruto total", "en": "Total gross margin"},
    "delta_sobre_costo": {"es": "{valor}% sobre el costo", "en": "{valor}% over cost"},
    "ingreso_por": {"es": "Ingreso por {n} {unidad}", "en": "Revenue from {n} {unidad}"},
    "cuenta_costo": {"es": "− Costo total supuesto", "en": "− Assumed total cost"},
    "cuenta_margen": {
        "es": "= Margen bruto del escenario",
        "en": "= Scenario gross margin",
    },
    "cap_bruto": {
        "es": (
            "Resultado **bruto**: ingreso proyectado menos costo de producción "
            "supuesto. Antes de impuestos, logística, financiación, prima por "
            "calidad y otros costos no incluidos."
        ),
        "en": (
            "**Gross** result: projected revenue minus assumed production cost. "
            "Before taxes, logistics, financing, quality premium and other "
            "costs not included."
        ),
    },
    "btn_informe": {
        "es": "Descargar informe del escenario (Markdown)",
        "en": "Download scenario report (Markdown)",
    },
    "help_informe": {
        "es": "Guarda los supuestos actuales, los resultados, la metodología y las limitaciones.",
        "en": "Saves the current assumptions, results, methodology and limitations.",
    },
    "info_costo": {
        "es": (
            "Costo medio inicial: ${costo} COP por carga, referencia nacional "
            "con dato de {fecha}. No representa necesariamente el costo de una "
            "finca particular."
        ),
        "en": (
            "Initial average cost: ${costo} COP per load, national reference "
            "with data from {fecha}. It does not necessarily represent a "
            "particular farm's cost."
        ),
    },
    "fuente_costo": {"es": "**Fuente del costo:** ", "en": "**Cost source:** "},
    "cap_margen_sim": {
        "es": (
            "El margen es una simulación bruta: precio estimado menos costo de "
            "producción supuesto. No incluye prima modelada, impuestos, "
            "logística, financiación, descuentos por calidad ni diferencias "
            "regionales."
        ),
        "en": (
            "The margin is a gross simulation: estimated price minus assumed "
            "production cost. It excludes modeled premium, taxes, logistics, "
            "financing, quality discounts and regional differences."
        ),
    },
}

# Etiquetas de presentación de los indicadores en inglés. El español canónico
# vive en `config.CATALOGO_VARIABLES`; aquí solo se traduce para la UI.
ETIQUETAS_VAR_EN = {
    "fx_usd_local": "USD/COP exchange rate",
    "precio_cafe_arabica": "International arabica coffee price",
    "precio_interno_referencia": "FNC reference internal price",
    "produccion_nacional": "National coffee production",
    "exportaciones_cafe": "Colombian coffee exports",
}
DESCRIPCIONES_VAR_EN = {
    "fx_usd_local": "Colombian pesos per US dollar",
    "precio_cafe_arabica": "ICE Coffee C future in US cents per pound",
    "precio_interno_referencia": "Base price per 125 kg load of dry parchment coffee",
    "produccion_nacional": "Monthly registered green-equivalent production",
    "exportaciones_cafe": "Monthly exported green-equivalent volume",
}
FUENTES_NOMBRE_EN = {
    "Federación Nacional de Cafeteros (FNC)": "National Federation of Coffee Growers (FNC)",
    "Yahoo Finance / futuro ICE Coffee C": "Yahoo Finance / ICE Coffee C future",
    "Yahoo Finance / USD-COP": "Yahoo Finance / USD-COP",
}
ALCANCE_EN = {"Colombia": "Colombia", "Global": "Global"}
CADENCIA_EN = {
    "Mensual": "Monthly",
    "Semanal": "Weekly",
    "Semanal (último cierre disponible)": "Weekly (last available close)",
    "Semanal (último dato disponible)": "Weekly (last available datum)",
}
METODO_EN = {
    "produccion_nacional": (
        "Monthly registered production; each row keeps the published month, no "
        "weekly fill."
    ),
    "exportaciones_cafe": (
        "Monthly exported volume; each row keeps the published month, no weekly "
        "fill."
    ),
    "precio_interno_referencia": (
        "Daily internal price; the last available value of each week is kept."
    ),
    "precio_cafe_arabica": (
        "Daily close of the KC=F future; the last available value of each week "
        "is kept."
    ),
    "fx_usd_local": (
        "Daily close of USDCOP=X; the last available value of each week is kept."
    ),
}
PERIODOS_EN = {
    "3 meses": "3 months",
    "6 meses": "6 months",
    "1 año": "1 year",
    "3 años": "3 years",
    "Todo": "All",
}


def _t(clave: str) -> str:
    """Texto en el idioma activo; cae al español si falta la traducción."""
    return TEXTOS[clave].get(IDIOMA, TEXTOS[clave]["es"])


def _etiqueta_var(codigo: str) -> str:
    """Nombre del indicador en el idioma activo."""
    if IDIOMA == "en" and codigo in ETIQUETAS_VAR_EN:
        return ETIQUETAS_VAR_EN[codigo]
    return CATALOGO_VARIABLES[codigo]["etiqueta"]


def _descripcion_var(codigo: str) -> str:
    """Descripción del indicador en el idioma activo."""
    if IDIOMA == "en" and codigo in DESCRIPCIONES_VAR_EN:
        return DESCRIPCIONES_VAR_EN[codigo]
    return CATALOGO_VARIABLES[codigo]["descripcion"]


def _periodo_label(clave: str) -> str:
    """Etiqueta visible de un periodo; el valor interno sigue en español."""
    return PERIODOS_EN[clave] if IDIOMA == "en" and clave in PERIODOS_EN else clave


def _carga_palabra(cantidad: int) -> str:
    """Palabra 'carga(s)'/'load(s)' según cantidad e idioma."""
    if IDIOMA == "en":
        return "load" if cantidad == 1 else "loads"
    return "carga" if cantidad == 1 else "cargas"


# Mapa inverso etiqueta-español → etiqueta-inglés, para traducir en pantalla las
# tablas que se construyen en español (las mismas que alimentan el PDF).
ETIQUETA_ES_A_EN = {
    CATALOGO_VARIABLES[codigo]["etiqueta"]: etiqueta
    for codigo, etiqueta in ETIQUETAS_VAR_EN.items()
}


def _indicador_en(etiqueta_es: str) -> str:
    """Traduce el nombre de un indicador desde su etiqueta en español."""
    return ETIQUETA_ES_A_EN.get(etiqueta_es, etiqueta_es)


def _pct_con_signo(valor: float) -> str:
    """Porcentaje con signo y separadores del idioma activo."""
    return f"{'+' if valor >= 0 else ''}{_numero(valor, 1)}%"


def _metodo(codigo: str) -> str:
    """Tratamiento semanal de la fuente en el idioma activo."""
    if IDIOMA == "en" and codigo in METODO_EN:
        return METODO_EN[codigo]
    return FUENTES_COMERCIALES[codigo]["metodo"]


st.set_page_config(
    page_title="Herramienta Consultas y Reportes",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _estilos() -> None:
    colores = COLORES_INTERFAZ
    st.markdown(
        f"""
        <style>
        :root {{
            --monitor-texto: {colores['texto']};
            --monitor-secundario: {colores['texto_secundario']};
            --monitor-fondo: {colores['fondo']};
            --monitor-sidebar: {colores['sidebar']};
            --monitor-superficie: {colores['superficie']};
            --monitor-borde: {colores['borde']};
            --monitor-acento: {colores['acento']};
        }}
        .stApp {{ background: var(--monitor-fondo); color: var(--monitor-texto); }}
        [data-testid="stHeader"] {{ background: var(--monitor-fondo); }}
        .block-container {{ max-width: 1440px; padding-top: 1.5rem; padding-bottom: 3rem; }}
        h1, h2, h3, p, label {{ color: var(--monitor-texto); letter-spacing: 0; }}
        h1 {{ font-size: 2rem; margin-bottom: 0.25rem; }}
        h2 {{ font-size: 1.35rem; margin-top: 1rem; }}
        h3 {{
            font-size: 1.18rem;
            font-weight: 600;
            margin-top: 1.75rem;
            margin-bottom: 0.4rem;
        }}
        [data-testid="stSidebar"] {{
            background: var(--monitor-sidebar);
            border-right: 1px solid var(--monitor-borde);
        }}
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] label {{ color: var(--monitor-texto) !important; }}
        [data-testid="stMetric"] {{
            background: var(--monitor-superficie);
            border: 1px solid var(--monitor-borde);
            border-left: 4px solid var(--monitor-acento);
            border-radius: 10px;
            padding: 0.9rem 1rem;
            min-height: 128px;
            box-shadow: 0 1px 2px rgba(23, 33, 27, 0.05);
        }}
        [data-testid="stMetricLabel"] {{ color: var(--monitor-secundario) !important; }}
        [data-testid="stMetricValue"] {{
            color: var(--monitor-texto) !important;
            font-size: 1.55rem;
        }}
        [data-testid="stMetricDelta"] {{ color: var(--monitor-secundario) !important; }}
        /* Margen por carga y total: ocultar la flecha (es un ratio, no una
           variación) pero conservar el texto dentro de la tarjeta. */
        .st-key-metrica_margen_carga [data-testid="stMetricDelta"] svg,
        .st-key-metrica_margen_total [data-testid="stMetricDelta"] svg {{ display: none; }}
        .st-key-metrica_margen_carga [data-testid="stMetricDelta"],
        .st-key-metrica_margen_total [data-testid="stMetricDelta"] {{ padding-left: 0; }}
        [data-testid="stPlotlyChart"] {{
            background: var(--monitor-superficie);
            border: 1px solid var(--monitor-borde);
            border-radius: 10px;
            padding: 0.25rem;
            box-shadow: 0 1px 2px rgba(23, 33, 27, 0.05);
        }}
        [data-testid="stExpander"] details {{
            border: 1px solid var(--monitor-borde);
            border-radius: 10px;
            background: var(--monitor-superficie);
        }}
        [data-testid="stDownloadButton"] button {{
            border: 1px solid var(--monitor-acento);
            border-radius: 8px;
            color: var(--monitor-acento);
            background: var(--monitor-superficie);
            font-weight: 600;
            transition: background 120ms ease, color 120ms ease;
        }}
        [data-testid="stDownloadButton"] button:hover {{
            background: var(--monitor-acento);
            color: #FFFFFF;
        }}
        .stTabs [data-baseweb="tab-list"] {{
            gap: 1.5rem;
            border-bottom: 1px solid var(--monitor-borde);
        }}
        .stTabs [data-baseweb="tab"] {{
            color: var(--monitor-secundario) !important;
            padding-left: 0;
            padding-right: 0;
            font-size: 1.02rem;
        }}
        .stTabs [data-baseweb="tab"] p {{ color: inherit !important; font-weight: 500; }}
        .stTabs [aria-selected="true"] {{ color: var(--monitor-acento) !important; }}
        @media (max-width: 768px) {{
            .block-container {{ padding: 1rem 0.8rem 2rem; }}
            h1 {{ font-size: 1.65rem; }}
            [data-testid="stMetric"] {{ min-height: 112px; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def _leer_series(ruta: str, marca_tiempo: float) -> pd.DataFrame:
    del marca_tiempo
    tabla = pd.read_csv(ruta, parse_dates=["semana_fin", "fecha_dato"])
    numericas = [
        "valor",
        "indice_base_100",
        "cambio_1s_absoluto",
        "cambio_1s_pct",
        "cambio_4s_pct",
        "cambio_1m_pct",
        "cambio_12m_pct",
        "promedio_movil_4s",
        "promedio_movil_12s",
        "anomalia_z_52s",
        "ranking_departamental",
        "percentil_departamental",
        "diferencia_mediana_departamentos",
    ]
    for columna in numericas:
        tabla[columna] = pd.to_numeric(tabla[columna], errors="coerce")
    return tabla


def _cargar_datos() -> pd.DataFrame:
    ruta = Path(RUTA_SERIES)
    if series_necesitan_regenerarse():
        preparar_visualizacion()
    return _leer_series(str(ruta), ruta.stat().st_mtime)


@st.cache_data(show_spinner=False)
def _leer_historico_diario(ruta: str, marca_tiempo: float) -> pd.DataFrame:
    """Carga las observaciones diarias usadas para calibrar el estimador."""
    del marca_tiempo
    return pd.read_csv(ruta, parse_dates=["fecha"])


def _cargar_historico_diario() -> pd.DataFrame:
    ruta = Path(RUTA_DIARIO)
    if not ruta.exists():
        raise FileNotFoundError(f"No existe el histórico diario: {ruta}")
    return _leer_historico_diario(str(ruta), ruta.stat().st_mtime)


def _cargar_calibracion_fnc() -> pd.DataFrame:
    """Carga referencias oficiales coherentes; permite respaldo si aún no existen."""
    ruta = Path(RUTA_CALIBRACION_FNC)
    if not ruta.exists():
        return pd.DataFrame()
    return pd.read_csv(ruta, parse_dates=["fecha"])


def _numero(valor: float, decimales: int) -> str:
    """Número con separadores según el idioma activo.

    Base (Python): miles con coma, decimal con punto → inglés directo. Para
    español se intercambian a miles con punto y decimal con coma.
    """
    texto = f"{valor:,.{decimales}f}"
    if IDIOMA == "en":
        return texto
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def _valor_metrica(fila: pd.Series) -> str:
    valor = _numero(float(fila["valor"]), int(fila["decimales"]))
    return f"{valor} {_unidad_legible(fila['unidad'])}"


def _variacion_comparacion(serie: pd.DataFrame, modo: str) -> str | None:
    """Variación del último valor frente a la semana o al mes anterior.

    Semanal: contra el cierre previo (un paso atrás), igual que la lectura
    operativa de las tarjetas. Mensual: contra el último cierre con fecha igual o
    anterior a hace ~28 días, lo que aproxima honestamente "mes contra mes" sin
    depender del punto de referencia diario añadido al final de la serie.
    """
    serie = serie.sort_values("semana_fin")
    valores = serie["valor"].astype(float).tolist()
    if len(valores) < 2:
        return None
    actual = valores[-1]
    if modo == "Semanal":
        base = valores[-2]
        etiqueta = _t("vs_semana_anterior")
    else:
        fechas = pd.to_datetime(serie["semana_fin"])
        objetivo = fechas.iloc[-1] - pd.Timedelta(days=28)
        previos = serie[fechas <= objetivo]
        if previos.empty:
            return None
        base = float(previos["valor"].astype(float).iloc[-1])
        etiqueta = _t("vs_mes_anterior")
    if base == 0:
        return None
    cambio = (actual / base - 1) * 100
    return f"{_numero(cambio, 1)}% {etiqueta}"


def _filtrar_periodo(tabla: pd.DataFrame, semanas: int | None) -> pd.DataFrame:
    if semanas is None:
        return tabla.copy()
    ultima = tabla["semana_fin"].max()
    inicio = ultima - pd.Timedelta(weeks=semanas - 1)
    return tabla[tabla["semana_fin"] >= inicio].copy()


def _filtrar_fechas(
    tabla: pd.DataFrame,
    inicio: pd.Timestamp,
    fin: pd.Timestamp,
) -> pd.DataFrame:
    """Filtra un rango inclusivo de cierres semanales."""
    fechas = pd.to_datetime(tabla["semana_fin"])
    return tabla[(fechas >= inicio) & (fechas <= fin)].copy()


def _layout(figura: go.Figure, altura: int = 400) -> go.Figure:
    colores = COLORES_INTERFAZ
    figura.update_layout(
        height=altura,
        # Separadores según idioma en todo lo que Plotly formatea (hover, ejes,
        # barra de color): el primer carácter es el decimal y el segundo el de
        # miles. Español → ",." (decimal coma, miles punto); inglés → ".,".
        separators=",." if IDIOMA == "es" else ".,",
        margin=dict(l=24, r=20, t=84, b=28),
        paper_bgcolor=colores["superficie"],
        plot_bgcolor=colores["superficie"],
        font=dict(color=colores["texto"], size=12),
        # Título anclado al borde superior izquierdo y leyenda justo encima del
        # área de trazado: el amplio margen superior los separa para que el
        # título nunca se monte sobre las etiquetas de la leyenda.
        title_font=dict(size=16),
        title_x=0,
        title_xanchor="left",
        title_y=0.99,
        title_yanchor="top",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        xaxis=dict(showgrid=False, automargin=True),
        yaxis=dict(gridcolor=colores["rejilla"], zeroline=False, automargin=True),
    )
    return figura


def _grafico_mercado(tabla: pd.DataFrame) -> go.Figure:
    figura = go.Figure()
    mercado = tabla[tabla["categoria"] == "Mercado"]
    for variable, grupo in mercado.groupby("variable", sort=False):
        metadatos = CATALOGO_VARIABLES[variable]
        grupo = grupo.assign(unidad_legible=grupo["unidad"].map(_unidad_legible))
        figura.add_trace(
            go.Scatter(
                x=grupo["semana_fin"],
                y=grupo["indice_base_100"],
                mode="lines",
                name=metadatos["etiqueta"],
                line=dict(color=metadatos["color"], width=2.5),
                customdata=grupo[["valor", "unidad_legible"]],
                hovertemplate=(
                    "%{x|%d %b %Y}<br>" + _t("hov_indice") + ": %{y:.1f}<br>"
                    + _t("hov_valor") + ": %{customdata[0]:,.1f} %{customdata[1]}"
                    "<extra></extra>"
                ),
            )
        )
    figura.add_hline(y=100, line_dash="dot", line_color="#9CA39D", line_width=1)
    figura.update_layout(title=_t("chart_mercado_titulo"))
    return _layout(figura, 430)


def _grafico_produccion(tabla: pd.DataFrame) -> go.Figure:
    datos = tabla[tabla["variable"].eq("produccion_nacional")]
    ancho_barra_ms = 14 * 24 * 60 * 60 * 1000
    figura = go.Figure(
        go.Bar(
            x=datos["fecha_dato"],
            y=datos["valor"],
            width=ancho_barra_ms,
            marker_color=CATALOGO_VARIABLES["produccion_nacional"]["color"],
            marker_line=dict(color="#5B21B6", width=1),
            name=_t("name_prod"),
            hovertemplate=(
                "%{x|%b %Y}<br>%{y:,.1f} " + _t("yaxis_miles_sacos").lower()
                + "<extra></extra>"
            ),
        )
    )
    figura.update_layout(
        title=_t("chart_prod_titulo"),
        xaxis=dict(
            showgrid=False,
            title=None,
            dtick="M1",
            tickformat="%b<br>%Y",
        ),
    )
    return _layout(figura, 350)


def _grafico_exportaciones(tabla: pd.DataFrame) -> go.Figure:
    datos = tabla[tabla["variable"].eq("exportaciones_cafe")]
    ancho_barra_ms = 14 * 24 * 60 * 60 * 1000
    figura = go.Figure(
        go.Bar(
            x=datos["fecha_dato"],
            y=datos["valor"],
            width=ancho_barra_ms,
            marker_color=CATALOGO_VARIABLES["exportaciones_cafe"]["color"],
            marker_line=dict(color="#155E75", width=1),
            name=_t("name_exp"),
            hovertemplate=(
                "%{x|%b %Y}<br>%{y:,.1f} " + _t("yaxis_miles_sacos").lower()
                + "<extra></extra>"
            ),
        )
    )
    figura.update_layout(
        title=_t("chart_exp_titulo"),
        xaxis=dict(showgrid=False, title=None, dtick="M1", tickformat="%b<br>%Y"),
    )
    return _layout(figura, 350)


def _comparar_produccion_exportaciones(tabla: pd.DataFrame) -> pd.DataFrame:
    """Empareja producción y exportaciones únicamente cuando comparten mes."""
    mensuales = tabla[
        tabla["variable"].isin(["produccion_nacional", "exportaciones_cafe"])
    ][["fecha_dato", "variable", "valor"]].copy()
    mensuales["mes"] = pd.to_datetime(mensuales["fecha_dato"]).dt.to_period("M")
    ancho = mensuales.pivot_table(
        index="mes",
        columns="variable",
        values="valor",
        aggfunc="last",
    ).dropna(subset=["produccion_nacional", "exportaciones_cafe"])
    ancho = ancho.reset_index()
    ancho["fecha"] = ancho["mes"].dt.to_timestamp()
    ancho["diferencia"] = (
        ancho["produccion_nacional"] - ancho["exportaciones_cafe"]
    )
    return ancho.sort_values("fecha").reset_index(drop=True)


def _grafico_diferencia_mensual(tabla: pd.DataFrame) -> go.Figure:
    comparacion = _comparar_produccion_exportaciones(tabla)
    colores = comparacion["diferencia"].map(
        lambda valor: COLORES_INTERFAZ["acento"] if valor >= 0 else "#B45309"
    )
    figura = go.Figure(
        go.Bar(
            x=comparacion["fecha"],
            y=comparacion["diferencia"],
            marker_color=colores,
            customdata=comparacion[["produccion_nacional", "exportaciones_cafe"]],
            hovertemplate=(
                "%{x|%b %Y}<br>"
                + _t("hov_produccion") + ": %{customdata[0]:,.1f}<br>"
                + _t("hov_exportaciones") + ": %{customdata[1]:,.1f}<br>"
                + _t("hov_diferencia") + ": %{y:,.1f} " + _t("hov_mil_sacos")
                + "<extra></extra>"
            ),
        )
    )
    figura.add_hline(y=0, line_color=COLORES_INTERFAZ["comparacion"], line_width=1)
    figura.update_layout(
        title=_t("chart_dif_titulo"),
        xaxis=dict(showgrid=False, title=None, dtick="M1", tickformat="%b<br>%Y"),
        yaxis_title=_t("yaxis_miles_sacos"),
        showlegend=False,
    )
    return _layout(figura, 370)


def _grafico_resultado_escenario(
    precio_observado: float,
    precio_estimado: float,
    costo_produccion: float,
) -> go.Figure:
    """Compara costo, último precio observado y precio estimado por carga."""
    valores = [costo_produccion, precio_observado, precio_estimado]
    etiquetas = [
        _t("barra_costo_medio"),
        _t("barra_ultimo_fnc"),
        _t("barra_precio_estimado"),
    ]
    colores = ["#B45309", COLORES_INTERFAZ["comparacion"], COLORES_INTERFAZ["acento"]]
    figura = go.Figure(
        go.Bar(
            x=valores,
            y=etiquetas,
            orientation="h",
            marker_color=colores,
            text=[f"${_numero(valor, 0)}" for valor in valores],
            textposition="outside",
            cliponaxis=False,
            hovertemplate="%{y}<br>$%{x:,.0f} " + _t("hov_cop_carga") + "<extra></extra>",
        )
    )
    figura.update_layout(
        title=_t("chart_resultado_titulo"),
        showlegend=False,
        hovermode="closest",
        xaxis=dict(
            tickprefix="$",
            tickformat=",.0f",
            showgrid=True,
            range=[0, max(valores) * 1.22],
        ),
        yaxis=dict(categoryorder="array", categoryarray=etiquetas[::-1]),
    )
    return _layout(figura, 330)


def _grafico_sensibilidad(
    matriz: pd.DataFrame,
    tasa_escenario: float,
    precio_ny_escenario: float,
) -> go.Figure:
    """Muestra cómo cambia el precio estimado para combinaciones Coffee C–FX."""
    pivote = matriz.pivot(
        index="precio_ny",
        columns="tasa_cambio",
        values="precio_fnc_estimado",
    )
    figura = go.Figure(
        go.Heatmap(
            x=pivote.columns,
            y=pivote.index,
            z=pivote.values,
            colorscale=[
                [0, "#F2E8D5"],
                [0.5, "#8FC1A9"],
                [1, "#176B4D"],
            ],
            colorbar=dict(title=_t("hov_cop_carga"), tickformat=",.0f"),
            # Mapa de solo lectura: el hover muestra el precio estimado de cada
            # celda. No se usa para fijar el escenario porque Streamlit no
            # propaga el clic de un heatmap y un scatter superpuesto colapsa el
            # eje Y; el escenario se fija con los campos numéricos.
            hovertemplate=(
                "USD/COP: %{x:,.0f}<br>"
                "Coffee C: %{y:.1f} US¢/lb<br>"
                + _t("hov_precio_fnc_estimado") + ": $%{z:,.0f}<extra></extra>"
            ),
        )
    )
    figura.add_trace(
        go.Scatter(
            x=[tasa_escenario],
            y=[precio_ny_escenario],
            mode="markers",
            marker=dict(size=14, color="#FFFFFF", line=dict(color="#17211B", width=3)),
            name=_t("name_escenario"),
            hoverinfo="skip",
        )
    )
    figura.update_layout(
        title=_t("chart_sens_titulo"),
        xaxis_title=_t("sens_xaxis"),
        yaxis_title=_t("sens_yaxis"),
        hovermode="closest",
    )
    return _layout(figura, 470)


def _puntos_lineales(minimo: float, maximo: float) -> list[float]:
    """Puntos equidistantes que cubren exactamente el rango de los controles."""
    paso = (maximo - minimo) / (PROYECCION_PUNTOS_MATRIZ - 1)
    return [minimo + indice * paso for indice in range(PROYECCION_PUNTOS_MATRIZ)]


def _ajustar_a_paso(valor: float, minimo: float, maximo: float, paso: float) -> float:
    """Redondea al paso del control y mantiene el valor dentro del rango."""
    ajustado = round(valor / paso) * paso
    return float(min(max(ajustado, minimo), maximo))


def _resumen_cuenta(resultado: ResultadoEscenario, cargas: int) -> None:
    """Muestra la cuenta del escenario: ingreso menos costo es igual a margen."""
    colores = COLORES_INTERFAZ
    naranja = "#B45309"
    color_margen = colores["acento"] if resultado.margen_total >= 0 else "#B91C1C"

    def fila(etiqueta: str, valor: float, color: str, signo: str = "") -> str:
        return (
            "<div style='display:flex;justify-content:space-between;"
            "align-items:baseline;gap:1rem;'>"
            f"<span style='color:{colores['texto_secundario']};'>{etiqueta}</span>"
            f"<span style='color:{color};font-weight:600;"
            "font-variant-numeric:tabular-nums;white-space:nowrap;'>"
            f"{signo}&#36;{_numero(valor, 0)}</span></div>"
        )

    st.markdown(
        "<div style='border:1px solid {borde};border-radius:12px;"
        "padding:14px 16px;background:{fondo};line-height:1.9;'>"
        "{ingreso}{costo}"
        "<div style='border-top:1px solid {borde};margin:8px 0;'></div>"
        "{margen}</div>".format(
            borde=colores["borde"],
            fondo=colores["fondo"],
            ingreso=fila(
                _t("ingreso_por").format(n=cargas, unidad=_carga_palabra(cargas)),
                resultado.ingreso_total,
                colores["texto"],
            ),
            costo=fila(_t("cuenta_costo"), resultado.costo_total, naranja),
            margen=fila(
                _t("cuenta_margen"),
                resultado.margen_total,
                color_margen,
            ),
        ),
        unsafe_allow_html=True,
    )
    st.caption(_t("cap_bruto"))


def _mantener_escenario_en_rango(
    minimo_fx: float,
    maximo_fx: float,
    minimo_cafe: float,
    maximo_cafe: float,
) -> None:
    """Mantiene el escenario guardado dentro del rango vigente de los controles.

    El mapa de sensibilidad es de solo lectura (Streamlit no propaga el clic de
    un heatmap y un scatter superpuesto colapsa el eje Y); el escenario se fija
    con los campos numéricos, pero su valor debe reajustarse si cambia la base.
    """
    st.session_state["sim_tasa"] = _ajustar_a_paso(
        st.session_state["sim_tasa"], minimo_fx, maximo_fx, PASO_FX
    )
    st.session_state["sim_ny"] = _ajustar_a_paso(
        st.session_state["sim_ny"], minimo_cafe, maximo_cafe, PASO_CAFE
    )


def _restablecer_simulador() -> None:
    """Borra el estado del escenario para que vuelva a sus valores iniciales."""
    for clave in (
        "sim_tasa",
        "sim_ny",
        "sim_costo",
        "sim_cargas",
        "sim_factor",
    ):
        st.session_state.pop(clave, None)


def _simulador_proyeccion(
    historico_diario: pd.DataFrame,
    calibracion_fnc: pd.DataFrame,
) -> None:
    """Renderiza el estimador de precio FNC y el margen del escenario."""
    bases = obtener_bases_calibracion(calibracion_fnc) or obtener_bases(
        historico_diario
    )
    modelo = calibrar_modelo(historico_diario, calibracion_fnc)
    st.subheader(_t("sub_estimador"))
    st.caption(_t("cap_estimador"))

    with st.expander(_t("exp_calibracion"), expanded=False):
        if modelo.calibracion_oficial:
            st.caption(
                _t("calib_oficial").format(
                    fecha=f"{modelo.fecha_fin_calibracion:%d/%m/%Y}",
                    mae=_numero(modelo.error_absoluto_medio, 0),
                    mape=_numero(modelo.error_porcentual_medio, 2),
                )
            )
        else:
            st.caption(
                _t("calib_respaldo").format(
                    obs=modelo.observaciones_calibracion,
                    inicio=f"{modelo.fecha_inicio_calibracion:%d/%m/%Y}",
                    fin=f"{modelo.fecha_fin_calibracion:%d/%m/%Y}",
                    val=modelo.observaciones_validacion,
                    mae=_numero(modelo.error_absoluto_medio, 0),
                    mape=_numero(modelo.error_porcentual_medio, 2),
                )
            )
        st.markdown(_t("formula"))

    minimo_fx = float(floor(bases.tasa_cambio * PROYECCION_RANGO_FACTOR_FX[0] / 50) * 50)
    maximo_fx = float(ceil(bases.tasa_cambio * PROYECCION_RANGO_FACTOR_FX[1] / 50) * 50)
    minimo_cafe = float(floor(bases.precio_ny * PROYECCION_RANGO_FACTOR_CAFE[0]))
    maximo_cafe = float(ceil(bases.precio_ny * PROYECCION_RANGO_FACTOR_CAFE[1]))

    st.session_state.setdefault(
        "sim_tasa", _ajustar_a_paso(bases.tasa_cambio, minimo_fx, maximo_fx, PASO_FX)
    )
    st.session_state.setdefault(
        "sim_ny", _ajustar_a_paso(bases.precio_ny, minimo_cafe, maximo_cafe, PASO_CAFE)
    )
    _mantener_escenario_en_rango(minimo_fx, maximo_fx, minimo_cafe, maximo_cafe)

    control_1, control_2 = st.columns(2)
    tasa_escenario = control_1.number_input(
        _t("ctrl_tasa"),
        min_value=minimo_fx,
        max_value=maximo_fx,
        step=PASO_FX,
        format="%.0f",
        key="sim_tasa",
    )
    precio_ny_escenario = control_2.number_input(
        _t("ctrl_coffee"),
        min_value=minimo_cafe,
        max_value=maximo_cafe,
        step=PASO_CAFE,
        format="%.1f",
        key="sim_ny",
    )
    st.caption(_t("cap_dos_campos"))

    st.session_state.setdefault("sim_costo", float(COSTO_PRODUCCION_REFERENCIA))
    st.session_state.setdefault("sim_cargas", int(PROYECCION_CARGAS_PREDETERMINADAS))
    st.session_state.setdefault("sim_factor", float(FACTOR_RENDIMIENTO_REFERENCIA))

    control_3, control_4, control_5 = st.columns(3)
    costo_produccion = control_3.number_input(
        _t("ctrl_costo"),
        min_value=0.0,
        step=10_000.0,
        format="%.0f",
        help=_t("help_costo"),
        key="sim_costo",
    )
    cargas = control_4.slider(
        _t("ctrl_volumen"),
        min_value=1,
        max_value=PROYECCION_CARGAS_MAXIMAS,
        step=1,
        key="sim_cargas",
    )
    factor_rendimiento = control_5.number_input(
        _t("ctrl_factor"),
        min_value=FACTOR_RENDIMIENTO_RANGO[0],
        max_value=FACTOR_RENDIMIENTO_RANGO[1],
        step=1.0,
        format="%.0f",
        help=_t("help_factor"),
        key="sim_factor",
    )

    st.button(
        _t("btn_restablecer"),
        on_click=_restablecer_simulador,
        help=_t("help_restablecer"),
    )

    resultado = calcular_escenario(
        modelo,
        tasa_escenario,
        precio_ny_escenario,
        costo_produccion,
        cargas,
        bases.precio_fnc,
        factor_rendimiento,
        FACTOR_RENDIMIENTO_REFERENCIA,
    )

    metricas = st.columns(4)
    metricas[0].metric(
        _t("metric_precio_estimado"),
        f"${_numero(resultado.precio_fnc_estimado, 0)}",
        (
            _t("delta_vs_observado").format(
                valor=_numero(resultado.diferencia_fnc_observado_pct, 1)
            )
            if pd.notna(resultado.diferencia_fnc_observado_pct)
            else None
        ),
        delta_color="off",
    )
    # Margen por carga y margen total muestran ratios (% del ingreso, % sobre el
    # costo), no variaciones; van dentro de la tarjeta con `delta`, pero se les
    # oculta la flecha por CSS (clases st-key-*) porque no indican subida/bajada.
    with metricas[1].container(key="metrica_margen_carga"):
        st.metric(
            _t("metric_margen_carga"),
            f"${_numero(resultado.margen_por_carga, 0)}",
            _t("delta_del_ingreso").format(
                valor=_numero(resultado.margen_sobre_ingreso_pct, 1)
            ),
            delta_color="off",
        )
    metricas[2].metric(
        _t("ingreso_por").format(n=cargas, unidad=_carga_palabra(cargas)),
        f"${_numero(resultado.ingreso_total, 0)}",
        delta=None,
    )
    with metricas[3].container(key="metrica_margen_total"):
        st.metric(
            _t("metric_margen_total"),
            f"${_numero(resultado.margen_total, 0)}",
            (
                _t("delta_sobre_costo").format(
                    valor=_numero(resultado.retorno_sobre_costo_pct, 1)
                )
                if pd.notna(resultado.retorno_sobre_costo_pct)
                else None
            ),
            delta_color="off",
        )

    grafico_1, grafico_2 = st.columns([0.85, 1.15])
    with grafico_1:
        st.plotly_chart(
            _grafico_resultado_escenario(
                bases.precio_fnc,
                resultado.precio_fnc_estimado,
                costo_produccion,
            ),
            width="stretch",
            theme=None,
            config=CONFIG_GRAFICO,
        )
        _resumen_cuenta(resultado, cargas)
    with grafico_2:
        tasas = _puntos_lineales(minimo_fx, maximo_fx)
        precios_ny = _puntos_lineales(minimo_cafe, maximo_cafe)
        matriz = crear_matriz_sensibilidad(
            modelo,
            tasas,
            precios_ny,
            factor_rendimiento,
            FACTOR_RENDIMIENTO_REFERENCIA,
        )
        st.plotly_chart(
            _grafico_sensibilidad(
                matriz,
                tasa_escenario,
                precio_ny_escenario,
            ),
            width="stretch",
            theme=None,
            config=CONFIG_GRAFICO,
        )

    informe = generar_informe_simulador(
        modelo=modelo,
        precio_fnc_observado=bases.precio_fnc,
        fecha_precio_fnc=bases.fecha_precio_fnc,
        tasa_cambio_escenario=tasa_escenario,
        precio_ny_escenario=precio_ny_escenario,
        costo_produccion=costo_produccion,
        cargas=cargas,
        resultado=resultado,
        costo_referencia=COSTO_PRODUCCION_REFERENCIA,
        costo_fecha=COSTO_PRODUCCION_FECHA,
        costo_fuente=COSTO_PRODUCCION_FUENTE,
        factor_rendimiento=factor_rendimiento,
        factor_referencia=FACTOR_RENDIMIENTO_REFERENCIA,
    )
    st.download_button(
        _t("btn_informe"),
        data=informe.encode("utf-8"),
        file_name=f"informe_simulador_monitor_agro_{pd.Timestamp.today():%Y%m%d}.md",
        mime="text/markdown",
        width="stretch",
        help=_t("help_informe"),
    )

    st.info(
        _t("info_costo").format(
            costo=_numero(COSTO_PRODUCCION_REFERENCIA, 0),
            fecha=f"{COSTO_PRODUCCION_FECHA:%m/%Y}",
        )
    )
    st.markdown(_t("fuente_costo") + f"[{COSTO_PRODUCCION_FUENTE}]({COSTO_PRODUCCION_URL})")
    st.caption(_t("cap_margen_sim"))


def _metricas_mercado(tabla: pd.DataFrame) -> None:
    modo = (
        st.segmented_control(
            _t("comparar_variacion"),
            options=["Mensual", "Semanal"],
            default="Mensual",
            format_func=lambda opcion: _t(
                "opt_mensual" if opcion == "Mensual" else "opt_semanal"
            ),
            key="modo_comparacion_mercado",
            help=_t("help_comparar"),
        )
        or "Mensual"
    )
    ultima = tabla["semana_fin"].max()
    datos = tabla[(tabla["semana_fin"] == ultima) & (tabla["categoria"] == "Mercado")]
    columnas = st.columns(3)
    variables = ["fx_usd_local", "precio_cafe_arabica", "precio_interno_referencia"]
    for columna, variable in zip(columnas, variables):
        serie = tabla[tabla["variable"] == variable].sort_values("semana_fin")
        fila = datos[datos["variable"] == variable].iloc[0]
        columna.metric(
            label=_etiqueta_var(variable),
            value=_valor_metrica(fila),
            delta=_variacion_comparacion(serie, modo),
            delta_color="off",
            chart_data=serie["valor"].tail(12).tolist(),
            chart_type="line",
            help=_descripcion_var(variable),
        )


def _variaciones_mercado(tabla: pd.DataFrame) -> pd.DataFrame:
    """Resume cambios semanales, de 4 semanas y de 52 semanas sin causalidad."""
    filas = []
    for variable in ["precio_interno_referencia", "precio_cafe_arabica", "fx_usd_local"]:
        serie = tabla[tabla["variable"].eq(variable)].sort_values("semana_fin")
        if serie.empty:
            continue
        actual = serie.iloc[-1]

        def cambio(periodos: int) -> float | None:
            if len(serie) <= periodos:
                return None
            anterior = float(serie.iloc[-periodos - 1]["valor"])
            if anterior == 0:
                return None
            return (float(actual["valor"]) / anterior - 1) * 100

        filas.append(
            {
                "Indicador": actual["etiqueta_variable"],
                "Semanal": cambio(1),
                "Mensual (4 sem.)": cambio(4),
                "Anual (52 sem.)": cambio(52),
            }
        )
    return pd.DataFrame(filas)


def _resumen_fuentes_comerciales(tabla: pd.DataFrame) -> pd.DataFrame:
    """Resume cobertura y fecha real del último dato de cada serie comercial."""
    mercado = tabla[tabla["categoria"].isin(["Mercado", "Producción"])].copy()
    indices = mercado.groupby("variable")["semana_fin"].idxmax()
    ultimos = mercado.loc[indices]
    filas = []
    for _, fila in ultimos.iterrows():
        metadatos = FUENTES_COMERCIALES[fila["variable"]]
        fuente = (
            "Federación Nacional de Cafeteros (FNC)"
            if fila["fuente"] == "FNC"
            else metadatos["nombre"]
        )
        filas.append(
            {
                "Indicador": fila["etiqueta_variable"],
                "Último dato": pd.Timestamp(fila["fecha_dato"]).strftime("%d/%m/%Y"),
                "Unidad": _unidad_legible(fila["unidad"]),
                "Fuente": fuente,
                "Alcance": metadatos["alcance"],
                "Cadencia": fila["cadencia"],
            }
        )
    return pd.DataFrame(filas)


def _bloque_produccion_exportaciones(
    tabla_filtrada: pd.DataFrame,
    tabla_completa: pd.DataFrame,
) -> None:
    """Compara los dos flujos mensuales sin inferir cambios de inventarios."""
    periodo = tabla_filtrada[tabla_filtrada["variable"].eq("produccion_nacional")]
    if periodo.empty:
        st.info(_t("info_no_prod"))
        return

    serie = tabla_completa[
        tabla_completa["variable"].eq("produccion_nacional")
    ].sort_values("fecha_dato")
    ultima_periodo = periodo.sort_values("fecha_dato").iloc[-1]
    ultima_completa = serie[serie["fecha_dato"].eq(ultima_periodo["fecha_dato"])].iloc[-1]
    columnas = st.columns([1, 1, 2])
    columnas[0].metric(
        _t("metric_prod"),
        f"{_numero(float(ultima_periodo['valor']), 1)} {_t('unid_mil_sacos')}",
        help=_t("help_prod"),
    )
    cambio_mensual = ultima_completa["cambio_1m_pct"]
    cambio_anual = ultima_completa["cambio_12m_pct"]
    columnas[1].metric(
        _t("metric_mes_dato"),
        pd.Timestamp(ultima_periodo["fecha_dato"]).strftime("%m/%Y"),
        delta=(
            _t("delta_vs_mes").format(cambio=_numero(float(cambio_mensual), 1))
            if pd.notna(cambio_mensual)
            else None
        ),
        delta_color="off",
    )
    columnas[2].markdown(
        _t("cambio_interanual")
        + (f"{_numero(float(cambio_anual), 1)}%" if pd.notna(cambio_anual) else _t("sin_dato"))
        + "  \n"
        + _t("fuente_fnc")
    )
    st.plotly_chart(
        _grafico_produccion(periodo),
        width="stretch",
        theme=None,
        config=CONFIG_GRAFICO,
    )
    exportaciones_periodo = tabla_filtrada[
        tabla_filtrada["variable"].eq("exportaciones_cafe")
    ]
    if exportaciones_periodo.empty:
        st.info(_t("info_no_exp"))
        return
    st.plotly_chart(
        _grafico_exportaciones(exportaciones_periodo),
        width="stretch",
        theme=None,
        config=CONFIG_GRAFICO,
    )

    comparacion = _comparar_produccion_exportaciones(tabla_filtrada)
    if comparacion.empty:
        st.info(_t("info_no_meses"))
        return
    ultima = comparacion.iloc[-1]
    diferencia = float(ultima["diferencia"])
    etiqueta = _t("prod_no_exportada") if diferencia >= 0 else _t("exp_sobre_prod")
    st.metric(
        etiqueta,
        f"{_numero(abs(diferencia), 1)} {_t('unid_mil_sacos')}",
        help=_t("help_diferencia"),
    )
    st.plotly_chart(
        _grafico_diferencia_mensual(tabla_filtrada),
        width="stretch",
        theme=None,
        config=CONFIG_GRAFICO,
    )
    st.caption(_t("cap_diferencia"))


def _metodologia_comercial() -> pd.DataFrame:
    """Devuelve la metodología comercial en el orden visible del catálogo."""
    filas = []
    variables = sorted(
        FUENTES_COMERCIALES,
        key=lambda variable: CATALOGO_VARIABLES[variable]["orden"],
    )
    for variable in variables:
        filas.append(
            {
                _t("col_indicador"): _etiqueta_var(variable),
                _t("col_tratamiento"): _metodo(variable),
            }
        )
    return pd.DataFrame(filas)


def _variaciones_para_pantalla(variaciones: pd.DataFrame):
    """Traduce columnas y nombres de indicador y formatea los % según idioma.

    El DataFrame de origen permanece en español porque también alimenta el PDF;
    aquí solo se prepara la vista en pantalla.
    """
    columnas = {
        "Indicador": _t("col_indicador"),
        "Semanal": _t("col_semanal"),
        "Mensual (4 sem.)": _t("col_mensual_4"),
        "Anual (52 sem.)": _t("col_anual_52"),
    }
    vista = variaciones.copy()
    if IDIOMA == "en":
        vista["Indicador"] = vista["Indicador"].map(_indicador_en)
    vista = vista.rename(columns=columnas)
    columnas_pct = [columnas["Semanal"], columnas["Mensual (4 sem.)"], columnas["Anual (52 sem.)"]]
    return vista.style.format(
        {columna: _pct_con_signo for columna in columnas_pct},
        na_rep=_t("sin_dato"),
    )


def _cobertura_para_pantalla(cobertura: pd.DataFrame) -> pd.DataFrame:
    """Traduce valores y encabezados de la tabla de cobertura para la pantalla."""
    vista = cobertura.copy()
    if IDIOMA == "en":
        vista["Indicador"] = vista["Indicador"].map(_indicador_en)
        vista["Fuente"] = vista["Fuente"].map(lambda v: FUENTES_NOMBRE_EN.get(v, v))
        vista["Alcance"] = vista["Alcance"].map(lambda v: ALCANCE_EN.get(v, v))
        vista["Cadencia"] = vista["Cadencia"].map(lambda v: CADENCIA_EN.get(v, v))
    return vista.rename(
        columns={
            "Indicador": _t("col_indicador"),
            "Último dato": _t("col_ultimo_dato"),
            "Unidad": _t("col_unidad"),
            "Fuente": _t("col_fuente"),
            "Alcance": _t("col_alcance"),
            "Cadencia": _t("col_cadencia"),
        }
    )


def _a_excel(tabla: pd.DataFrame) -> bytes:
    """Serializa la tabla comercial a un archivo Excel (.xlsx) en memoria."""
    hoja = "Commercial series" if IDIOMA == "en" else "Series comerciales"
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        tabla.to_excel(writer, index=False, sheet_name=hoja)
    return buffer.getvalue()


@st.cache_data(show_spinner="Preparando el brief en PDF…")
def _brief_pdf(inicio: pd.Timestamp, fin: pd.Timestamp, marca_datos: float) -> bytes:
    """Genera el PDF del periodo; la caché solo se invalida si cambian los datos."""
    del marca_datos
    periodo = _filtrar_fechas(datos, inicio, fin)
    return generar_pdf_brief(
        inicio=inicio,
        fin=fin,
        periodo=periodo,
        variaciones=_variaciones_mercado(datos_semanales),
        cobertura=_resumen_fuentes_comerciales(periodo),
    )


_estilos()
datos_semanales = _cargar_datos()
historico_diario = _cargar_historico_diario()
calibracion_fnc = _cargar_calibracion_fnc()
bases_actuales = obtener_bases_calibracion(calibracion_fnc) or obtener_bases(
    historico_diario
)
referencia_actual = {
    "precio_interno_referencia": (
        bases_actuales.precio_fnc,
        bases_actuales.fecha_precio_fnc,
    ),
    "fx_usd_local": (
        bases_actuales.tasa_cambio,
        bases_actuales.fecha_tasa_cambio,
    ),
    "precio_cafe_arabica": (
        bases_actuales.precio_ny,
        bases_actuales.fecha_precio_ny,
    ),
}
datos = incorporar_referencia_comercial_actual(datos_semanales, referencia_actual)
ultima_semana = datos_semanales["semana_fin"].max()
ultima_referencia = max(
    bases_actuales.fecha_precio_fnc,
    bases_actuales.fecha_tasa_cambio,
    bases_actuales.fecha_precio_ny,
)
semanas_disponibles_total = datos_semanales["semana_fin"].nunique()

IDIOMA = IDIOMAS[
    st.sidebar.selectbox("Idioma / Language", list(IDIOMAS), index=0)
]

st.title(_t("titulo"))
st.caption(
    _t("subtitulo").format(
        semanas=semanas_disponibles_total,
        ultima=f"{ultima_semana:%d/%m/%Y}",
        referencia=f"{ultima_referencia:%d/%m/%Y}",
    )
)
st.markdown(_t("introduccion"))

st.sidebar.header(_t("filtros"))
tipo_periodo = st.sidebar.radio(
    _t("rango_analisis"),
    options=["Periodo predefinido", "Fechas personalizadas"],
    format_func=lambda opcion: _t(
        "periodo_predefinido"
        if opcion == "Periodo predefinido"
        else "fechas_personalizadas"
    ),
)
if tipo_periodo == "Periodo predefinido":
    periodo = st.sidebar.segmented_control(
        _t("periodo"),
        options=list(PERIODOS_VISUALIZACION),
        default="1 año",
        format_func=_periodo_label,
        width="stretch",
    )
    semanas = PERIODOS_VISUALIZACION[periodo or "1 año"]
    filtrados = _filtrar_periodo(datos, semanas)
else:
    fecha_minima = datos["semana_fin"].min().date()
    fecha_maxima = datos["semana_fin"].max().date()
    rango = st.sidebar.date_input(
        _t("fechas_cierre"),
        value=(max(fecha_minima, fecha_maxima - pd.Timedelta(days=365)), fecha_maxima),
        min_value=fecha_minima,
        max_value=fecha_maxima,
        format="DD/MM/YYYY",
    )
    if isinstance(rango, (tuple, list)) and len(rango) == 2:
        filtrados = _filtrar_fechas(
            datos,
            pd.Timestamp(rango[0]),
            pd.Timestamp(rango[1]),
        )
    else:
        filtrados = _filtrar_periodo(datos, PERIODOS_VISUALIZACION["1 año"])
st.sidebar.divider()
st.sidebar.caption(_t("autor"))

tab_panorama, tab_proyeccion = st.tabs(
    [_t("tab_panorama"), _t("tab_simulador")],
    default=_t("tab_panorama"),
    key="vistas_principales",
)

with tab_panorama:
    st.subheader(_t("sub_lectura"))
    st.caption(_t("cap_lectura"))
    _metricas_mercado(filtrados)
    st.plotly_chart(
        _grafico_mercado(filtrados),
        width="stretch",
        theme=None,
        config=CONFIG_GRAFICO,
    )
    st.caption(_t("cap_base100"))
    st.markdown(_t("md_variaciones"))
    st.dataframe(
        _variaciones_para_pantalla(_variaciones_mercado(datos_semanales)),
        hide_index=True,
        width="stretch",
    )
    st.subheader(_t("sub_prodexp"))
    _bloque_produccion_exportaciones(filtrados, datos)

    st.subheader(_t("sub_exportar"))
    descarga = preparar_descarga_comercial(filtrados)
    nombre_archivo = (
        f"monitor_agro_comercial_{filtrados['semana_fin'].min():%Y%m%d}_"
        f"{filtrados['semana_fin'].max():%Y%m%d}.xlsx"
    )
    inicio_brief = pd.Timestamp(filtrados["semana_fin"].min())
    fin_brief = pd.Timestamp(filtrados["semana_fin"].max())
    clave_pdf = f"{inicio_brief:%Y%m%d}_{fin_brief:%Y%m%d}"
    col_csv, col_brief = st.columns(2)
    col_csv.download_button(
        _t("btn_excel"),
        data=_a_excel(descarga),
        file_name=nombre_archivo,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        width="stretch",
        help=_t("help_excel"),
    )
    col_brief.download_button(
        _t("btn_pdf"),
        data=_brief_pdf(inicio_brief, fin_brief, Path(RUTA_SERIES).stat().st_mtime),
        file_name=f"brief_monitor_agro_{clave_pdf}.pdf",
        mime="application/pdf",
        width="stretch",
        help=_t("help_pdf"),
    )
    with st.expander(_t("exp_cobertura")):
        st.markdown(_t("md_cobertura"))
        st.dataframe(
            _cobertura_para_pantalla(_resumen_fuentes_comerciales(filtrados)),
            hide_index=True,
            width="stretch",
        )
        st.dataframe(
            _metodologia_comercial(),
            hide_index=True,
            width="stretch",
        )

with tab_proyeccion:
    _simulador_proyeccion(historico_diario, calibracion_fnc)

st.divider()
st.caption(_t("foot_fuentes"))
st.caption(_t("foot_copyright"))
