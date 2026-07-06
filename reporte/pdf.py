"""Maqueta el brief del periodo como un PDF ejecutivo con gráficas y tablas.

Las gráficas se dibujan con matplotlib (sin navegador) para que el PDF se genere
igual en local y en Streamlit Cloud. Esta capa recibe los datos ya filtrados y
las tablas ya calculadas; no consulta fuentes ni calcula indicadores.
"""

from datetime import date
from io import BytesIO
from math import ceil

import matplotlib

matplotlib.use("Agg")

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from config import CATALOGO_VARIABLES, COLORES_INTERFAZ
from reporte.formato import numero as _numero

_ACENTO_HEX = COLORES_INTERFAZ["acento"]
_TEXTO_HEX = COLORES_INTERFAZ["texto"]
_SECUNDARIO_HEX = COLORES_INTERFAZ["texto_secundario"]
_REJILLA_HEX = COLORES_INTERFAZ["rejilla"]

_ACENTO = colors.HexColor(_ACENTO_HEX)
_TEXTO = colors.HexColor(_TEXTO_HEX)
_SECUNDARIO = colors.HexColor(_SECUNDARIO_HEX)
_BORDE = colors.HexColor(COLORES_INTERFAZ["borde"])
_CABECERA_TABLA = colors.HexColor(COLORES_INTERFAZ["sidebar"])


# Textos del brief en ambos idiomas. Las traducciones coinciden con las de la
# interfaz (TEXTOS y mapas de presentación en app.py) para que pantalla y PDF
# cuenten lo mismo; esta capa no importa app.py para no depender de Streamlit.
_TEXTOS = {
    "titulo": {
        "es": "Pulso Cafetero",
        "en": "Coffee Pulse",
    },
    "titulo_documento": {
        "es": "Brief del periodo — Pulso Cafetero",
        "en": "Period brief — Coffee Pulse",
    },
    "subtitulo": {
        "es": "Brief del periodo · {inicio} a {fin} · generado el {generado}",
        "en": "Period brief · {inicio} to {fin} · generated on {generado}",
    },
    "introduccion": {
        "es": (
            "Lectura descriptiva del precio interno de la Federación Nacional "
            "de Cafeteros (FNC), el café internacional (ICE Coffee C) y la "
            "tasa de cambio USD/COP. Los movimientos no implican causalidad "
            "ni califican el resultado como favorable o desfavorable."
        ),
        "en": (
            "Descriptive reading of the National Federation of Coffee Growers "
            "(FNC) internal price, international coffee (ICE Coffee C) and "
            "the USD/COP exchange rate. Movements do not imply causality nor "
            "qualify the outcome as favorable or unfavorable."
        ),
    },
    "sec_panorama": {"es": "Panorama comercial", "en": "Commercial overview"},
    "nota_base100": {
        "es": (
            "Índice base 100 desde enero de 2023: compara dirección y magnitud "
            "relativa entre series con unidades distintas."
        ),
        "en": (
            "Index based at 100 since January 2023: compares direction and "
            "relative magnitude across series with different units."
        ),
    },
    "sec_variaciones": {
        "es": "Variaciones por indicador",
        "en": "Changes by indicator",
    },
    "sec_flujos": {
        "es": "Producción y exportaciones mensuales",
        "en": "Monthly production and exports",
    },
    "nota_flujos": {
        "es": (
            "Ambas series se conservan en los meses publicados. La diferencia "
            "compara flujos del mismo mes y no equivale a inventarios, reservas "
            "ni consumo interno."
        ),
        "en": (
            "Both series keep their published months. The difference compares "
            "flows of the same month and does not equal inventories, reserves "
            "or domestic consumption."
        ),
    },
    "sin_flujos": {
        "es": (
            "No hay producción o exportaciones mensuales publicadas dentro del "
            "periodo elegido."
        ),
        "en": (
            "No monthly production or exports were published within the "
            "selected period."
        ),
    },
    "sec_cobertura": {"es": "Cobertura y fuentes", "en": "Coverage and sources"},
    "sec_limitaciones": {
        "es": "Alcance y limitaciones",
        "en": "Scope and limitations",
    },
    "fuentes_final": {
        "es": (
            "Fuentes: Federación Nacional de Cafeteros (FNC) y Yahoo Finance "
            "vía yfinance. "
            "Documento exploratorio; no contiene score de oportunidad o riesgo."
        ),
        "en": (
            "Sources: National Federation of Coffee Growers (FNC) and Yahoo "
            "Finance via yfinance. "
            "Exploratory document; it contains no opportunity or risk score."
        ),
    },
    "pagina": {"es": "Página", "en": "Page"},
    "sin_dato": {"es": "Sin dato", "en": "No data"},
    "titulo_mercado": {
        "es": "Evolución comercial comparable · base 100",
        "en": "Comparable commercial evolution · base 100",
    },
    "titulo_flujos": {
        "es": "Producción y exportaciones mensuales · miles de sacos de 60 kg",
        "en": "Monthly production and exports · thousand 60-kg bags",
    },
    "titulo_diferencia": {
        "es": "Diferencia descriptiva · producción menos exportaciones",
        "en": "Descriptive difference · production minus exports",
    },
    "leyenda_produccion": {"es": "Producción", "en": "Production"},
    "leyenda_exportaciones": {"es": "Exportaciones", "en": "Exports"},
    "col_mes": {"es": "Mes comparable", "en": "Comparable month"},
    "col_produccion": {"es": "Producción", "en": "Production"},
    "col_exportaciones": {"es": "Exportaciones", "en": "Exports"},
    "col_diferencia": {"es": "Diferencia", "en": "Difference"},
    "lectura_sin_dato": {
        "es": "{indicador}: sin variación semanal comparable.",
        "en": "{indicador}: no comparable weekly change.",
    },
    "lectura_cambio": {
        "es": "{indicador}: {direccion} {magnitud}% en la última semana.",
        "en": "{indicador}: {direccion} {magnitud}% over the last week.",
    },
    "subio": {"es": "subió", "en": "rose"},
    "bajo": {"es": "bajó", "en": "fell"},
    "sin_cambio": {"es": "no cambió", "en": "did not change"},
}

_LIMITACIONES = {
    "es": [
        "Producción y exportaciones se publican mensualmente y no se rellenan "
        "como datos semanales.",
        "La diferencia mensual entre ambos flujos no mide inventarios, reservas "
        "ni consumo interno.",
        "Algunas series dependen de scraping o archivos descargables que pueden "
        "cambiar de estructura.",
        "El brief describe movimientos estadísticos; no asigna oportunidad, "
        "riesgo ni causalidad.",
    ],
    "en": [
        "Production and exports are published monthly and are not filled in as "
        "weekly data.",
        "The monthly difference between both flows does not measure "
        "inventories, reserves or domestic consumption.",
        "Some series depend on scraping or downloadable files whose structure "
        "may change.",
        "The brief describes statistical movements; it assigns no opportunity, "
        "risk or causality.",
    ],
}

# Traducciones de las etiquetas de datos (mismos textos que la interfaz).
_ETIQUETAS_VAR_EN = {
    "fx_usd_local": "USD/COP exchange rate",
    "precio_cafe_arabica": "International arabica coffee price",
    "precio_interno_referencia": "FNC reference internal price",
    "produccion_nacional": "National coffee production",
    "exportaciones_cafe": "Colombian coffee exports",
}
_ETIQUETA_ES_A_EN = {
    CATALOGO_VARIABLES[variable]["etiqueta"]: etiqueta_en
    for variable, etiqueta_en in _ETIQUETAS_VAR_EN.items()
    if variable in CATALOGO_VARIABLES
}
_COLUMNAS_VARIACIONES_EN = {
    "Indicador": "Indicator",
    "Semanal": "Weekly",
    "Mensual (4 sem.)": "Monthly (4 wks)",
    "Anual (52 sem.)": "Yearly (52 wks)",
}
_COLUMNAS_COBERTURA_EN = {
    "Indicador": "Indicator",
    "Último dato": "Latest data",
    "Unidad": "Unit",
    "Fuente": "Source",
    "Alcance": "Scope",
    "Cadencia": "Cadence",
}
_FUENTES_EN = {
    "Federación Nacional de Cafeteros (FNC)": (
        "National Federation of Coffee Growers (FNC)"
    ),
    "Yahoo Finance / futuro ICE Coffee C": "Yahoo Finance / ICE Coffee C future",
    "Yahoo Finance / USD-COP": "Yahoo Finance / USD-COP",
}
_CADENCIA_EN = {
    "Mensual": "Monthly",
    "Semanal": "Weekly",
    "Semanal (último cierre disponible)": "Weekly (last available close)",
    "Semanal (último dato disponible)": "Weekly (last available datum)",
}
_UNIDADES_EN = {
    "COP/carga": "COP/load",
    "miles de sacos de 60 kg": "thousand 60-kg bags",
}


def _tr(clave: str, idioma: str) -> str:
    """Texto del brief en el idioma pedido, con respaldo en español."""
    textos = _TEXTOS[clave]
    return textos.get(idioma, textos["es"])


def _etiqueta_indicador(etiqueta_es: str, idioma: str) -> str:
    if idioma == "en":
        return _ETIQUETA_ES_A_EN.get(etiqueta_es, etiqueta_es)
    return etiqueta_es


def _fig_a_png(figura) -> bytes:
    """Cierra la figura de matplotlib y devuelve sus bytes PNG."""
    lector = BytesIO()
    figura.savefig(lector, format="png", dpi=150, bbox_inches="tight")
    plt.close(figura)
    return lector.getvalue()


def _ejes_limpios(ax) -> None:
    """Aplica la estética del tablero a un eje de matplotlib."""
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color(_REJILLA_HEX)
    ax.tick_params(colors=_SECUNDARIO_HEX, labelsize=8)
    ax.grid(axis="y", color=_REJILLA_HEX, linewidth=0.6)
    ax.set_axisbelow(True)


def _png_mercado(periodo: pd.DataFrame, idioma: str = "es") -> bytes:
    """Dibuja las tres series comerciales en índice base 100."""
    mercado = periodo[periodo["categoria"].eq("Mercado")]
    figura, ax = plt.subplots(figsize=(9.2, 3.5))
    for variable, grupo in mercado.groupby("variable", sort=False):
        serie = grupo.sort_values("semana_fin")
        metadatos = CATALOGO_VARIABLES[variable]
        ax.plot(
            serie["semana_fin"],
            serie["indice_base_100"],
            label=_etiqueta_indicador(metadatos["etiqueta"], idioma),
            color=metadatos["color"],
            linewidth=2.0,
        )
    ax.axhline(100, color="#9CA39D", linestyle=":", linewidth=1)
    ax.set_title(
        _tr("titulo_mercado", idioma),
        color=_TEXTO_HEX,
        fontsize=11,
        loc="left",
        pad=8,
    )
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.legend(
        loc="upper center",
        fontsize=8,
        frameon=False,
        ncol=3,
        bbox_to_anchor=(0.5, -0.16),
    )
    _ejes_limpios(ax)
    return _fig_a_png(figura)


def _png_produccion(periodo: pd.DataFrame) -> bytes:
    """Dibuja la producción nacional mensual como barras de ancho fijo."""
    serie = periodo[periodo["variable"].eq("produccion_nacional")].sort_values(
        "fecha_dato"
    )
    figura, ax = plt.subplots(figsize=(9.2, 3.2))
    ax.bar(
        serie["fecha_dato"],
        serie["valor"],
        width=14,
        color=_ACENTO_HEX,
    )
    ax.set_title(
        "Producción nacional mensual · miles de sacos de 60 kg",
        color=_TEXTO_HEX,
        fontsize=11,
        loc="left",
        pad=10,
    )
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    _ejes_limpios(ax)
    return _fig_a_png(figura)


def _flujos_mensuales(periodo: pd.DataFrame) -> pd.DataFrame:
    """Empareja producción y exportaciones sin interpretar la diferencia."""
    datos = periodo[
        periodo["variable"].isin(["produccion_nacional", "exportaciones_cafe"])
    ][["fecha_dato", "variable", "valor"]].copy()
    if datos.empty:
        return pd.DataFrame()
    datos["mes"] = pd.to_datetime(datos["fecha_dato"]).dt.to_period("M")
    flujos = datos.pivot_table(
        index="mes", columns="variable", values="valor", aggfunc="last"
    ).reset_index()
    flujos["fecha"] = flujos["mes"].dt.to_timestamp()
    if {"produccion_nacional", "exportaciones_cafe"}.issubset(flujos.columns):
        flujos["diferencia"] = (
            flujos["produccion_nacional"] - flujos["exportaciones_cafe"]
        )
    return flujos.sort_values("fecha").reset_index(drop=True)


def _png_flujos_mensuales(periodo: pd.DataFrame, idioma: str = "es") -> bytes:
    """Compara producción, exportaciones y su diferencia en una sola pieza."""
    flujos = _flujos_mensuales(periodo)
    figura, (ax_superior, ax_inferior) = plt.subplots(
        2,
        1,
        figsize=(9.2, 5.5),
        sharex=True,
        gridspec_kw={"height_ratios": [2, 1], "hspace": 0.18},
    )
    if "produccion_nacional" in flujos:
        ax_superior.plot(
            flujos["fecha"],
            flujos["produccion_nacional"],
            label=_tr("leyenda_produccion", idioma),
            color=CATALOGO_VARIABLES["produccion_nacional"]["color"],
            linewidth=2,
            marker="o",
            markersize=3,
        )
    if "exportaciones_cafe" in flujos:
        ax_superior.plot(
            flujos["fecha"],
            flujos["exportaciones_cafe"],
            label=_tr("leyenda_exportaciones", idioma),
            color=CATALOGO_VARIABLES["exportaciones_cafe"]["color"],
            linewidth=2,
            marker="o",
            markersize=3,
        )
    ax_superior.set_title(
        _tr("titulo_flujos", idioma),
        color=_TEXTO_HEX,
        fontsize=11,
        loc="left",
        pad=8,
    )
    ax_superior.legend(loc="upper left", fontsize=8, frameon=False, ncol=2)
    _ejes_limpios(ax_superior)

    if "diferencia" in flujos:
        colores_barras = [
            _ACENTO_HEX if valor >= 0 else "#B45309"
            for valor in flujos["diferencia"].fillna(0)
        ]
        ax_inferior.bar(
            flujos["fecha"],
            flujos["diferencia"],
            width=18,
            color=colores_barras,
        )
    ax_inferior.axhline(0, color=_SECUNDARIO_HEX, linewidth=0.8)
    ax_inferior.set_title(
        _tr("titulo_diferencia", idioma),
        color=_TEXTO_HEX,
        fontsize=9,
        loc="left",
        pad=5,
    )
    intervalo = max(1, ceil(max(len(flujos), 1) / 10))
    ax_inferior.xaxis.set_major_locator(mdates.MonthLocator(interval=intervalo))
    ax_inferior.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    _ejes_limpios(ax_inferior)
    return _fig_a_png(figura)


def _estilos() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "titulo": ParagraphStyle(
            "MonitorTitulo",
            parent=base["Title"],
            textColor=_ACENTO,
            fontSize=20,
            leading=24,
            spaceAfter=2,
            alignment=TA_LEFT,
        ),
        "subtitulo": ParagraphStyle(
            "MonitorSubtitulo",
            parent=base["Normal"],
            textColor=_SECUNDARIO,
            fontSize=10,
            leading=14,
            spaceAfter=14,
        ),
        "seccion": ParagraphStyle(
            "MonitorSeccion",
            parent=base["Heading2"],
            textColor=_ACENTO,
            fontSize=13,
            leading=16,
            spaceBefore=14,
            spaceAfter=6,
        ),
        "cuerpo": ParagraphStyle(
            "MonitorCuerpo",
            parent=base["Normal"],
            textColor=_TEXTO,
            fontSize=10,
            leading=15,
            spaceAfter=4,
        ),
        "nota": ParagraphStyle(
            "MonitorNota",
            parent=base["Normal"],
            textColor=_SECUNDARIO,
            fontSize=8.5,
            leading=12,
        ),
        "tabla": ParagraphStyle(
            "MonitorTabla",
            parent=base["Normal"],
            textColor=_TEXTO,
            fontSize=8.2,
            leading=10.5,
        ),
    }


def _tabla(
    df: pd.DataFrame,
    estilos: dict[str, ParagraphStyle],
    anchos: list[float] | None = None,
) -> Table:
    """Convierte un DataFrame en una tabla con la identidad visual del tablero."""
    encabezado = [Paragraph(f"<b>{col}</b>", estilos["tabla"]) for col in df.columns]
    filas = [encabezado]
    for _, fila in df.iterrows():
        filas.append([Paragraph(str(valor), estilos["tabla"]) for valor in fila])
    col_widths = [ancho * cm for ancho in anchos] if anchos else None
    tabla = Table(filas, repeatRows=1, hAlign="LEFT", colWidths=col_widths)
    tabla.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), _CABECERA_TABLA),
                ("TEXTCOLOR", (0, 0), (-1, 0), _ACENTO),
                ("GRID", (0, 0), (-1, -1), 0.5, _BORDE),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _CABECERA_TABLA]),
            ]
        )
    )
    return tabla


def _resumen_ultimo_mes(periodo: pd.DataFrame, idioma: str = "es") -> pd.DataFrame:
    flujos = _flujos_mensuales(periodo).dropna(
        subset=["produccion_nacional", "exportaciones_cafe"], how="any"
    )
    if flujos.empty:
        return pd.DataFrame()
    ultimo = flujos.iloc[-1]
    return pd.DataFrame(
        [
            {
                _tr("col_mes", idioma): pd.Timestamp(ultimo["fecha"]).strftime(
                    "%m/%Y"
                ),
                _tr("col_produccion", idioma): _numero(
                    float(ultimo["produccion_nacional"]), 1, idioma
                ),
                _tr("col_exportaciones", idioma): _numero(
                    float(ultimo["exportaciones_cafe"]), 1, idioma
                ),
                _tr("col_diferencia", idioma): _numero(
                    float(ultimo["diferencia"]), 1, idioma
                ),
            }
        ]
    )


def _pie_pagina(canvas, documento, idioma: str = "es") -> None:
    """Añade autor, página y una línea discreta en todas las páginas."""
    canvas.saveState()
    ancho, _ = A4
    canvas.setStrokeColor(_BORDE)
    canvas.line(2 * cm, 1.25 * cm, ancho - 2 * cm, 1.25 * cm)
    canvas.setFillColor(_SECUNDARIO)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(2 * cm, 0.85 * cm, "Juan José Jaramillo · Pulso Cafetero")
    canvas.drawRightString(
        ancho - 2 * cm, 0.85 * cm, f"{_tr('pagina', idioma)} {documento.page}"
    )
    canvas.restoreState()


def _imagen(png: bytes, ancho_cm: float = 16.5) -> Image:
    """Inserta un PNG conservando su proporción dentro del ancho disponible."""
    imagen = Image(BytesIO(png))
    proporcion = imagen.drawHeight / imagen.drawWidth
    imagen.drawWidth = ancho_cm * cm
    imagen.drawHeight = ancho_cm * cm * proporcion
    imagen.hAlign = "LEFT"
    return imagen


def _variaciones_formateadas(
    variaciones: pd.DataFrame, idioma: str = "es"
) -> pd.DataFrame:
    """Formatea porcentajes y traduce encabezados e indicadores para el PDF."""
    salida = variaciones.copy()
    for columna in ["Semanal", "Mensual (4 sem.)", "Anual (52 sem.)"]:
        if columna in salida.columns:
            salida[columna] = salida[columna].map(
                lambda valor: f"{_numero(float(valor), 1, idioma)}%"
                if pd.notna(valor)
                else _tr("sin_dato", idioma)
            )
    if idioma == "en":
        if "Indicador" in salida.columns:
            salida["Indicador"] = salida["Indicador"].map(
                lambda etiqueta: _etiqueta_indicador(etiqueta, idioma)
            )
        salida = salida.rename(columns=_COLUMNAS_VARIACIONES_EN)
    return salida


def _cobertura_traducida(cobertura: pd.DataFrame, idioma: str) -> pd.DataFrame:
    """Traduce valores y encabezados de la tabla de cobertura para el PDF."""
    if idioma != "en":
        return cobertura
    vista = cobertura.copy()
    traducciones = {
        "Indicador": lambda v: _etiqueta_indicador(v, idioma),
        "Fuente": lambda v: _FUENTES_EN.get(v, v),
        "Cadencia": lambda v: _CADENCIA_EN.get(v, v),
        "Unidad": lambda v: _UNIDADES_EN.get(v, v),
    }
    for columna, traducir in traducciones.items():
        if columna in vista.columns:
            vista[columna] = vista[columna].map(traducir)
    return vista.rename(columns=_COLUMNAS_COBERTURA_EN)


def _lectura_neutral(variaciones: pd.DataFrame, idioma: str = "es") -> list[str]:
    """Resume la dirección semanal de cada indicador sin afirmar causalidad."""
    lecturas = []
    for _, fila in variaciones.iterrows():
        indicador = _etiqueta_indicador(str(fila["Indicador"]), idioma)
        cambio = fila.get("Semanal")
        if pd.isna(cambio):
            lecturas.append(
                _tr("lectura_sin_dato", idioma).format(indicador=indicador)
            )
            continue
        direccion = _tr(
            "subio" if cambio > 0 else "bajo" if cambio < 0 else "sin_cambio",
            idioma,
        )
        lecturas.append(
            _tr("lectura_cambio", idioma).format(
                indicador=indicador,
                direccion=direccion,
                magnitud=_numero(abs(float(cambio)), 1, idioma),
            )
        )
    return lecturas


def generar_pdf_brief(
    *,
    inicio: date | pd.Timestamp,
    fin: date | pd.Timestamp,
    periodo: pd.DataFrame,
    variaciones: pd.DataFrame,
    cobertura: pd.DataFrame,
    fecha_generacion: date | None = None,
    idioma: str = "es",
) -> bytes:
    """Construye el PDF del brief (español o inglés) y devuelve sus bytes.

    `variaciones` y `cobertura` llegan en español (como las genera app.py);
    esta capa las traduce cuando `idioma="en"`.
    """
    if fecha_generacion is None:
        fecha_generacion = date.today()
    inicio_ts = pd.Timestamp(inicio)
    fin_ts = pd.Timestamp(fin)
    estilos = _estilos()

    flujos = periodo[
        periodo["variable"].isin(["produccion_nacional", "exportaciones_cafe"])
    ]

    historia = BytesIO()
    documento = SimpleDocTemplate(
        historia,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.7 * cm,
        title=_tr("titulo_documento", idioma),
        author=_tr("titulo", idioma),
    )

    elementos = [
        Paragraph(_tr("titulo", idioma), estilos["titulo"]),
        Paragraph(
            _tr("subtitulo", idioma).format(
                inicio=f"{inicio_ts:%d/%m/%Y}",
                fin=f"{fin_ts:%d/%m/%Y}",
                generado=f"{fecha_generacion:%d/%m/%Y}",
            ),
            estilos["subtitulo"],
        ),
        Paragraph(_tr("introduccion", idioma), estilos["cuerpo"]),
        Paragraph(_tr("sec_panorama", idioma), estilos["seccion"]),
        _imagen(_png_mercado(periodo, idioma)),
        Paragraph(_tr("nota_base100", idioma), estilos["nota"]),
        Spacer(1, 0.3 * cm),
        Paragraph(_tr("sec_variaciones", idioma), estilos["seccion"]),
        _tabla(
            _variaciones_formateadas(variaciones, idioma),
            estilos,
            [5.2, 3.4, 3.4, 3.4],
        ),
        Spacer(1, 0.3 * cm),
    ]

    for lectura in _lectura_neutral(variaciones, idioma):
        elementos.append(Paragraph(f"• {lectura}", estilos["cuerpo"]))

    elementos.append(PageBreak())
    elementos.append(Paragraph(_tr("sec_flujos", idioma), estilos["seccion"]))
    if not flujos.empty:
        elementos.append(_imagen(_png_flujos_mensuales(periodo, idioma)))
        resumen_mes = _resumen_ultimo_mes(periodo, idioma)
        if not resumen_mes.empty:
            elementos.append(
                _tabla(resumen_mes, estilos, [3.6, 4.0, 4.0, 4.0])
            )
        elementos.append(Paragraph(_tr("nota_flujos", idioma), estilos["nota"]))
    else:
        elementos.append(Paragraph(_tr("sin_flujos", idioma), estilos["cuerpo"]))

    elementos.extend(
        [
            PageBreak(),
            Paragraph(_tr("sec_cobertura", idioma), estilos["seccion"]),
            _tabla(
                _cobertura_traducida(cobertura, idioma),
                estilos,
                [3.0, 2.2, 2.5, 3.3, 1.8, 3.7],
            ),
            Paragraph(_tr("sec_limitaciones", idioma), estilos["seccion"]),
        ]
    )
    for limitacion in _LIMITACIONES.get(idioma, _LIMITACIONES["es"]):
        elementos.append(Paragraph(f"• {limitacion}", estilos["cuerpo"]))

    elementos.extend(
        [
            Spacer(1, 0.4 * cm),
            Paragraph(_tr("fuentes_final", idioma), estilos["nota"]),
        ]
    )

    def _pie(canvas, doc) -> None:
        _pie_pagina(canvas, doc, idioma)

    documento.build(elementos, onFirstPage=_pie, onLaterPages=_pie)
    return historia.getvalue()
