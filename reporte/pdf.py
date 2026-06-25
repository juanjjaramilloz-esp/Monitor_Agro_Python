"""Maqueta el brief del periodo como un PDF ejecutivo con gráficas y tablas.

Las gráficas se dibujan con matplotlib (sin navegador) para que el PDF se genere
igual en local y en Streamlit Cloud. Esta capa recibe los datos ya filtrados y
las tablas ya calculadas; no consulta fuentes ni calcula indicadores.
"""

from datetime import date
from io import BytesIO

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
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from config import CATALOGO_VARIABLES, COLORES_INTERFAZ


_ACENTO_HEX = COLORES_INTERFAZ["acento"]
_TEXTO_HEX = COLORES_INTERFAZ["texto"]
_SECUNDARIO_HEX = COLORES_INTERFAZ["texto_secundario"]
_REJILLA_HEX = COLORES_INTERFAZ["rejilla"]

_ACENTO = colors.HexColor(_ACENTO_HEX)
_TEXTO = colors.HexColor(_TEXTO_HEX)
_SECUNDARIO = colors.HexColor(_SECUNDARIO_HEX)
_BORDE = colors.HexColor(COLORES_INTERFAZ["borde"])
_CABECERA_TABLA = colors.HexColor(COLORES_INTERFAZ["sidebar"])


def _numero(valor: float, decimales: int = 1) -> str:
    texto = f"{valor:,.{decimales}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


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


def _png_mercado(periodo: pd.DataFrame) -> bytes:
    """Dibuja las tres series comerciales en índice base 100."""
    mercado = periodo[periodo["categoria"].eq("Mercado")]
    figura, ax = plt.subplots(figsize=(9.2, 3.5))
    for variable, grupo in mercado.groupby("variable", sort=False):
        serie = grupo.sort_values("semana_fin")
        metadatos = CATALOGO_VARIABLES[variable]
        ax.plot(
            serie["semana_fin"],
            serie["indice_base_100"],
            label=metadatos["etiqueta"],
            color=metadatos["color"],
            linewidth=2.0,
        )
    ax.axhline(100, color="#9CA39D", linestyle=":", linewidth=1)
    ax.set_title(
        "Evolución comercial comparable · base 100",
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
    }


def _tabla(df: pd.DataFrame, estilos: dict[str, ParagraphStyle]) -> Table:
    """Convierte un DataFrame en una tabla con la identidad visual del tablero."""
    encabezado = [Paragraph(f"<b>{col}</b>", estilos["cuerpo"]) for col in df.columns]
    filas = [encabezado]
    for _, fila in df.iterrows():
        filas.append([Paragraph(str(valor), estilos["cuerpo"]) for valor in fila])
    tabla = Table(filas, repeatRows=1, hAlign="LEFT")
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


def _imagen(png: bytes, ancho_cm: float = 16.5) -> Image:
    """Inserta un PNG conservando su proporción dentro del ancho disponible."""
    imagen = Image(BytesIO(png))
    proporcion = imagen.drawHeight / imagen.drawWidth
    imagen.drawWidth = ancho_cm * cm
    imagen.drawHeight = ancho_cm * cm * proporcion
    imagen.hAlign = "LEFT"
    return imagen


def _variaciones_formateadas(variaciones: pd.DataFrame) -> pd.DataFrame:
    """Formatea los porcentajes de la tabla de variaciones para el PDF."""
    salida = variaciones.copy()
    for columna in ["Semanal", "Mensual (4 sem.)", "Anual (52 sem.)"]:
        if columna in salida.columns:
            salida[columna] = salida[columna].map(
                lambda valor: f"{_numero(float(valor), 1)}%"
                if pd.notna(valor)
                else "Sin dato"
            )
    return salida


def _lectura_neutral(variaciones: pd.DataFrame) -> list[str]:
    """Resume la dirección semanal de cada indicador sin afirmar causalidad."""
    lecturas = []
    for _, fila in variaciones.iterrows():
        cambio = fila.get("Semanal")
        if pd.isna(cambio):
            lecturas.append(f"{fila['Indicador']}: sin variación semanal comparable.")
            continue
        direccion = "subió" if cambio > 0 else "bajó" if cambio < 0 else "no cambió"
        lecturas.append(
            f"{fila['Indicador']}: {direccion} {_numero(abs(float(cambio)), 1)}% "
            "en la última semana."
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
) -> bytes:
    """Construye el PDF del brief y devuelve sus bytes listos para descargar."""
    if fecha_generacion is None:
        fecha_generacion = date.today()
    inicio_ts = pd.Timestamp(inicio)
    fin_ts = pd.Timestamp(fin)
    estilos = _estilos()

    produccion = periodo[periodo["variable"].eq("produccion_nacional")]

    historia = BytesIO()
    documento = SimpleDocTemplate(
        historia,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
        title="Brief del periodo — Herramienta Consultas y Reportes",
        author="Herramienta Consultas y Reportes",
    )

    elementos = [
        Paragraph("Herramienta Consultas y Reportes", estilos["titulo"]),
        Paragraph(
            f"Brief del periodo · {inicio_ts:%d/%m/%Y} a {fin_ts:%d/%m/%Y} · "
            f"generado el {fecha_generacion:%d/%m/%Y}",
            estilos["subtitulo"],
        ),
        Paragraph(
            "Lectura descriptiva del precio interno FNC, el café internacional "
            "(ICE Coffee C) y la tasa de cambio USD/COP. Los movimientos no "
            "implican causalidad ni califican el resultado como favorable o "
            "desfavorable.",
            estilos["cuerpo"],
        ),
        Paragraph("Panorama comercial", estilos["seccion"]),
        _imagen(_png_mercado(periodo)),
        Paragraph(
            "Índice base 100 desde enero de 2023: compara dirección y magnitud "
            "relativa entre series con unidades distintas.",
            estilos["nota"],
        ),
        Spacer(1, 0.3 * cm),
        Paragraph("Variaciones por indicador", estilos["seccion"]),
        _tabla(_variaciones_formateadas(variaciones), estilos),
        Spacer(1, 0.3 * cm),
    ]

    for lectura in _lectura_neutral(variaciones):
        elementos.append(Paragraph(f"• {lectura}", estilos["cuerpo"]))

    elementos.append(Paragraph("Producción nacional mensual", estilos["seccion"]))
    if not produccion.empty:
        elementos.append(_imagen(_png_produccion(periodo)))
        elementos.append(
            Paragraph(
                "La producción se publica por mes y no se rellena como dato "
                "semanal.",
                estilos["nota"],
            )
        )
    else:
        elementos.append(
            Paragraph(
                "No hay un dato mensual de producción publicado dentro del "
                "periodo elegido.",
                estilos["cuerpo"],
            )
        )

    elementos.extend(
        [
            Paragraph("Cobertura y fuentes", estilos["seccion"]),
            _tabla(cobertura, estilos),
            Paragraph("Alcance y limitaciones", estilos["seccion"]),
        ]
    )
    limitaciones = [
        "La producción nacional se publica mensualmente y no se rellena como "
        "dato semanal.",
        "El clima usa una coordenada municipal de referencia y no representa "
        "toda la variación departamental.",
        "Algunas series dependen de scraping o archivos descargables que pueden "
        "cambiar de estructura.",
        "El brief describe movimientos estadísticos; no asigna oportunidad, "
        "riesgo ni causalidad.",
    ]
    for limitacion in limitaciones:
        elementos.append(Paragraph(f"• {limitacion}", estilos["cuerpo"]))

    elementos.extend(
        [
            Spacer(1, 0.4 * cm),
            Paragraph(
                "Fuentes: FNC, Open-Meteo y Yahoo Finance vía yfinance. "
                "Documento exploratorio; no contiene score de oportunidad o riesgo.",
                estilos["nota"],
            ),
        ]
    )

    documento.build(elementos)
    return historia.getvalue()
