"""Kit de consulta, reporte y simulación del Monitor Agro Colombia."""

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


# Las fuentes usan unidades "de máquina" en el contrato de datos; aquí se
# traducen a etiquetas legibles solo al mostrarlas, sin tocar el esquema.
UNIDADES_LEGIBLES = {
    "COP/carga_125kg": "COP/carga",
    "USc/lb": "US¢/lb",
}


def _unidad_legible(unidad: str) -> str:
    """Traduce la unidad técnica del contrato a una etiqueta legible en la UI."""
    return UNIDADES_LEGIBLES.get(unidad, unidad)


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


def _numero_es(valor: float, decimales: int) -> str:
    texto = f"{valor:,.{decimales}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def _valor_metrica(fila: pd.Series) -> str:
    valor = _numero_es(float(fila["valor"]), int(fila["decimales"]))
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
        etiqueta = "vs semana anterior"
    else:
        fechas = pd.to_datetime(serie["semana_fin"])
        objetivo = fechas.iloc[-1] - pd.Timedelta(days=28)
        previos = serie[fechas <= objetivo]
        if previos.empty:
            return None
        base = float(previos["valor"].astype(float).iloc[-1])
        etiqueta = "vs mes anterior"
    if base == 0:
        return None
    cambio = (actual / base - 1) * 100
    return f"{_numero_es(cambio, 1)}% {etiqueta}"


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
                    "%{x|%d %b %Y}<br>Índice: %{y:.1f}<br>"
                    "Valor: %{customdata[0]:,.1f} %{customdata[1]}<extra></extra>"
                ),
            )
        )
    figura.add_hline(y=100, line_dash="dot", line_color="#9CA39D", line_width=1)
    figura.update_layout(title="Evolución comercial comparable · base 100")
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
            name="Producción mensual",
            hovertemplate=(
                "%{x|%b %Y}<br>%{y:,.1f} miles de sacos de 60 kg<extra></extra>"
            ),
        )
    )
    figura.update_layout(
        title="Producción nacional registrada · una barra por mes",
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
            name="Exportaciones mensuales",
            hovertemplate=(
                "%{x|%b %Y}<br>%{y:,.1f} miles de sacos de 60 kg<extra></extra>"
            ),
        )
    )
    figura.update_layout(
        title="Exportaciones colombianas de café · una barra por mes",
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
                "Producción: %{customdata[0]:,.1f}<br>"
                "Exportaciones: %{customdata[1]:,.1f}<br>"
                "Diferencia: %{y:,.1f} mil sacos<extra></extra>"
            ),
        )
    )
    figura.add_hline(y=0, line_color=COLORES_INTERFAZ["comparacion"], line_width=1)
    figura.update_layout(
        title="Diferencia mensual · producción menos exportaciones",
        xaxis=dict(showgrid=False, title=None, dtick="M1", tickformat="%b<br>%Y"),
        yaxis_title="Miles de sacos de 60 kg",
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
    etiquetas = ["Costo medio", "Último FNC observado", "Precio estimado"]
    colores = ["#B45309", COLORES_INTERFAZ["comparacion"], COLORES_INTERFAZ["acento"]]
    figura = go.Figure(
        go.Bar(
            x=valores,
            y=etiquetas,
            orientation="h",
            marker_color=colores,
            text=[f"${valor:,.0f}" for valor in valores],
            textposition="outside",
            cliponaxis=False,
            hovertemplate="%{y}<br>$%{x:,.0f} COP/carga<extra></extra>",
        )
    )
    figura.update_layout(
        title="Precio y costo por carga de 125 kg",
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
    coeficiente: float,
    factor_rendimiento: float,
    factor_referencia: float,
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
            colorbar=dict(title="COP/carga", tickformat=",.0f"),
            # Solo color: el hover y el clic los maneja la rejilla de puntos.
            hoverinfo="skip",
        )
    )
    # Rejilla fina e invisible para capturar el clic con precisión: el Heatmap no
    # emite eventos de clic, pero un Scatter sí. Cada punto lleva su precio
    # estimado para mostrar el hover y permitir la selección. CLAVE: el hoverinfo
    # no puede ser "skip" porque en Plotly "skip" también anula el clic; por eso
    # se usa un hovertemplate. Los marcadores son grandes para cubrir el área sin
    # huecos y que cualquier clic caiga sobre un punto.
    ajuste = factor_referencia / factor_rendimiento
    resolucion = 50
    tasa_min, tasa_max = float(matriz["tasa_cambio"].min()), float(matriz["tasa_cambio"].max())
    ny_min, ny_max = float(matriz["precio_ny"].min()), float(matriz["precio_ny"].max())
    rejilla_x, rejilla_y, rejilla_precio = [], [], []
    for indice_ny in range(resolucion):
        ny = ny_min + indice_ny * (ny_max - ny_min) / (resolucion - 1)
        for indice_tasa in range(resolucion):
            tasa = tasa_min + indice_tasa * (tasa_max - tasa_min) / (resolucion - 1)
            rejilla_x.append(tasa)
            rejilla_y.append(ny)
            rejilla_precio.append(tasa * ny * coeficiente * ajuste)
    figura.add_trace(
        go.Scatter(
            x=rejilla_x,
            y=rejilla_y,
            mode="markers",
            marker=dict(size=16, color="rgba(0,0,0,0)"),
            customdata=rejilla_precio,
            hovertemplate=(
                "USD/COP: %{x:,.0f}<br>"
                "Coffee C: %{y:.1f} US¢/lb<br>"
                "Precio FNC estimado: $%{customdata:,.0f}<extra></extra>"
            ),
            showlegend=False,
            name="celdas",
        )
    )
    figura.add_trace(
        go.Scatter(
            x=[tasa_escenario],
            y=[precio_ny_escenario],
            mode="markers",
            marker=dict(size=14, color="#FFFFFF", line=dict(color="#17211B", width=3)),
            name="Escenario elegido",
            hoverinfo="skip",
        )
    )
    figura.update_layout(
        title="Mapa de sensibilidad del precio FNC estimado",
        xaxis_title="Tasa de cambio (COP/USD)",
        yaxis_title="Coffee C (US¢/lb)",
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
    plural = "s" if cargas != 1 else ""

    def fila(etiqueta: str, valor: float, color: str, signo: str = "") -> str:
        return (
            "<div style='display:flex;justify-content:space-between;"
            "align-items:baseline;gap:1rem;'>"
            f"<span style='color:{colores['texto_secundario']};'>{etiqueta}</span>"
            f"<span style='color:{color};font-weight:600;"
            "font-variant-numeric:tabular-nums;white-space:nowrap;'>"
            f"{signo}&#36;{_numero_es(valor, 0)}</span></div>"
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
                f"Ingreso por {cargas} carga{plural}",
                resultado.ingreso_total,
                colores["texto"],
            ),
            costo=fila("− Costo total supuesto", resultado.costo_total, naranja),
            margen=fila(
                "= Margen bruto del escenario",
                resultado.margen_total,
                color_margen,
            ),
        ),
        unsafe_allow_html=True,
    )
    st.caption(
        "Resultado **bruto**: ingreso proyectado menos costo de producción "
        "supuesto. Antes de impuestos, logística, financiación, prima por "
        "calidad y otros costos no incluidos."
    )


def _aplicar_clic_sensibilidad(
    minimo_fx: float,
    maximo_fx: float,
    minimo_cafe: float,
    maximo_cafe: float,
) -> None:
    """Lleva un clic en el mapa de sensibilidad a los sliders del escenario."""
    estado = st.session_state.get("sens_sel")
    puntos = []
    if estado is not None and hasattr(estado, "get"):
        seleccion = estado.get("selection") or {}
        puntos = seleccion.get("points", []) if hasattr(seleccion, "get") else []
    # Excluye el marcador del escenario (curva 2) para que no capture el clic.
    candidatos = [p for p in puntos if p.get("curve_number") != 2] or puntos
    if candidatos and candidatos[0].get("x") is not None:
        punto = candidatos[0]
        firma = (punto["x"], punto["y"])
        if st.session_state.get("sens_firma") != firma:
            st.session_state["sim_tasa"] = _ajustar_a_paso(
                float(punto["x"]), minimo_fx, maximo_fx, 0.01
            )
            st.session_state["sim_ny"] = _ajustar_a_paso(
                float(punto["y"]), minimo_cafe, maximo_cafe, 0.01
            )
            st.session_state["sens_firma"] = firma
    # Mantiene los valores guardados dentro del rango vigente si cambió la base.
    st.session_state["sim_tasa"] = _ajustar_a_paso(
        st.session_state["sim_tasa"], minimo_fx, maximo_fx, 0.01
    )
    st.session_state["sim_ny"] = _ajustar_a_paso(
        st.session_state["sim_ny"], minimo_cafe, maximo_cafe, 0.01
    )


def _restablecer_simulador() -> None:
    """Borra el estado del escenario para que vuelva a sus valores iniciales."""
    for clave in (
        "sim_tasa",
        "sim_ny",
        "sim_costo",
        "sim_cargas",
        "sim_factor",
        "sens_sel",
        "sens_firma",
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
    st.subheader("Estimador de precio interno y margen")
    st.caption(
        "Ingrese supuestos de Coffee C y USD/COP para estimar el precio interno "
        "FNC. El precio FNC observado ya no es una entrada ni funciona como piso."
    )

    with st.expander("Calibración y metodología", expanded=False):
        if modelo.calibracion_oficial:
            st.caption(
                f"Calibración oficial FNC del {modelo.fecha_fin_calibracion:%d/%m/%Y}: "
                "precio interno, Coffee C y TRM publicados juntos para evitar mezclar "
                "fuentes u horas de cierre. Si esa referencia falla, el respaldo "
                f"estadístico tiene un error histórico medio de "
                f"${_numero_es(modelo.error_absoluto_medio, 0)} por carga "
                f"({modelo.error_porcentual_medio:.2f}%)."
            )
        else:
            st.caption(
                f"Calibración de respaldo: {modelo.observaciones_calibracion} fechas "
                f"comparables, de {modelo.fecha_inicio_calibracion:%d/%m/%Y} a "
                f"{modelo.fecha_fin_calibracion:%d/%m/%Y}. Validación caminando sobre "
                f"{modelo.observaciones_validacion} observaciones: error absoluto medio "
                f"${_numero_es(modelo.error_absoluto_medio, 0)} por carga "
                f"({modelo.error_porcentual_medio:.2f}%)."
            )
        st.markdown(
            "**Fórmula:** USD/COP escenario × Coffee C escenario × coeficiente "
            "calibrado × (factor referencia ÷ factor de rendimiento). El coeficiente "
            "se recalcula con los últimos datos diarios comparables y pondera más "
            "los recientes. Resume prima, conversiones y otros componentes que no "
            "se modelan por separado; no reproduce la fórmula oficial de la FNC."
        )

    minimo_fx = float(floor(bases.tasa_cambio * PROYECCION_RANGO_FACTOR_FX[0] / 50) * 50)
    maximo_fx = float(ceil(bases.tasa_cambio * PROYECCION_RANGO_FACTOR_FX[1] / 50) * 50)
    minimo_cafe = float(floor(bases.precio_ny * PROYECCION_RANGO_FACTOR_CAFE[0]))
    maximo_cafe = float(ceil(bases.precio_ny * PROYECCION_RANGO_FACTOR_CAFE[1]))

    st.session_state.setdefault(
        "sim_tasa", _ajustar_a_paso(bases.tasa_cambio, minimo_fx, maximo_fx, 0.01)
    )
    st.session_state.setdefault(
        "sim_ny", _ajustar_a_paso(bases.precio_ny, minimo_cafe, maximo_cafe, 0.01)
    )
    _aplicar_clic_sensibilidad(minimo_fx, maximo_fx, minimo_cafe, maximo_cafe)

    control_1, control_2 = st.columns(2)
    tasa_escenario = control_1.number_input(
        "Tasa de cambio del escenario · COP/USD",
        min_value=minimo_fx,
        max_value=maximo_fx,
        step=0.01,
        format="%.2f",
        key="sim_tasa",
    )
    precio_ny_escenario = control_2.number_input(
        "Coffee C del escenario · US¢/lb",
        min_value=minimo_cafe,
        max_value=maximo_cafe,
        step=0.01,
        format="%.2f",
        key="sim_ny",
    )
    st.caption(
        "Escriba los valores del día o haga clic en el mapa de sensibilidad para "
        "fijar un escenario."
    )

    st.session_state.setdefault("sim_costo", float(COSTO_PRODUCCION_REFERENCIA))
    st.session_state.setdefault("sim_cargas", int(PROYECCION_CARGAS_PREDETERMINADAS))
    st.session_state.setdefault("sim_factor", float(FACTOR_RENDIMIENTO_REFERENCIA))

    control_3, control_4, control_5 = st.columns(3)
    costo_produccion = control_3.number_input(
        "Costo de producción · COP por carga de 125 kg",
        min_value=0.0,
        step=10_000.0,
        format="%.0f",
        help="Referencia nacional FEPCafé; edítela para representar otro supuesto.",
        key="sim_costo",
    )
    cargas = control_4.slider(
        "Volumen del escenario · cargas de 125 kg",
        min_value=1,
        max_value=PROYECCION_CARGAS_MAXIMAS,
        step=1,
        key="sim_cargas",
    )
    factor_rendimiento = control_5.number_input(
        "Factor de rendimiento",
        min_value=FACTOR_RENDIMIENTO_RANGO[0],
        max_value=FACTOR_RENDIMIENTO_RANGO[1],
        step=1.0,
        format="%.0f",
        help=(
            "Kg de café pergamino seco por carga de excelso; 94 es la referencia "
            "FNC. Un factor menor (mejor rendimiento) sube el precio recibido; uno "
            "mayor lo baja. Ajuste aproximado, no la fórmula oficial."
        ),
        key="sim_factor",
    )

    st.button(
        "↺ Restablecer valores predeterminados",
        on_click=_restablecer_simulador,
        help="Vuelve los controles del escenario a los últimos valores disponibles.",
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
        "Precio FNC estimado",
        f"${_numero_es(resultado.precio_fnc_estimado, 0)}",
        (
            f"{_numero_es(resultado.diferencia_fnc_observado_pct, 1)}% frente al último observado"
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
            "Margen bruto por carga",
            f"${_numero_es(resultado.margen_por_carga, 0)}",
            f"{_numero_es(resultado.margen_sobre_ingreso_pct, 1)}% del ingreso",
            delta_color="off",
        )
    metricas[2].metric(
        f"Ingreso por {cargas} carga{'s' if cargas != 1 else ''}",
        f"${_numero_es(resultado.ingreso_total, 0)}",
        delta=None,
    )
    with metricas[3].container(key="metrica_margen_total"):
        st.metric(
            "Margen bruto total",
            f"${_numero_es(resultado.margen_total, 0)}",
            (
                f"{_numero_es(resultado.retorno_sobre_costo_pct, 1)}% sobre el costo"
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
                modelo.coeficiente,
                factor_rendimiento,
                FACTOR_RENDIMIENTO_REFERENCIA,
            ),
            width="stretch",
            theme=None,
            config=CONFIG_GRAFICO,
            on_select="rerun",
            selection_mode="points",
            key="sens_sel",
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
        "Descargar informe del escenario (Markdown)",
        data=informe.encode("utf-8"),
        file_name=f"informe_simulador_monitor_agro_{pd.Timestamp.today():%Y%m%d}.md",
        mime="text/markdown",
        width="stretch",
        help="Guarda los supuestos actuales, los resultados, la metodología y las limitaciones.",
    )

    st.info(
        f"Costo medio inicial: ${COSTO_PRODUCCION_REFERENCIA:,.0f} COP por carga, "
        f"referencia nacional con dato de {COSTO_PRODUCCION_FECHA:%m/%Y}. "
        "No representa necesariamente el costo de una finca particular."
    )
    st.markdown(f"**Fuente del costo:** [{COSTO_PRODUCCION_FUENTE}]({COSTO_PRODUCCION_URL})")
    st.caption(
        "El margen es una simulación bruta: precio estimado menos costo de "
        "producción supuesto. No incluye prima modelada, impuestos, logística, "
        "financiación, descuentos por calidad ni diferencias regionales."
    )


def _metricas_mercado(tabla: pd.DataFrame) -> None:
    modo = (
        st.segmented_control(
            "Comparar variación",
            options=["Mensual", "Semanal"],
            default="Mensual",
            key="modo_comparacion_mercado",
            help=(
                "Mensual compara el último valor con el de hace ~4 semanas; "
                "Semanal lo compara con el cierre de la semana anterior."
            ),
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
            label=fila["etiqueta_variable"],
            value=_valor_metrica(fila),
            delta=_variacion_comparacion(serie, modo),
            delta_color="off",
            chart_data=serie["valor"].tail(12).tolist(),
            chart_type="line",
            help=fila["descripcion_variable"],
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
        st.info("No hay un dato mensual de producción publicado dentro del periodo elegido.")
        return

    serie = tabla_completa[
        tabla_completa["variable"].eq("produccion_nacional")
    ].sort_values("fecha_dato")
    ultima_periodo = periodo.sort_values("fecha_dato").iloc[-1]
    ultima_completa = serie[serie["fecha_dato"].eq(ultima_periodo["fecha_dato"])].iloc[-1]
    columnas = st.columns([1, 1, 2])
    columnas[0].metric(
        "Producción nacional · mensual",
        f"{_numero_es(float(ultima_periodo['valor']), 1)} mil sacos de 60 kg",
        help="Producción registrada de café verde equivalente publicada por la FNC.",
    )
    cambio_mensual = ultima_completa["cambio_1m_pct"]
    cambio_anual = ultima_completa["cambio_12m_pct"]
    columnas[1].metric(
        "Mes del dato",
        pd.Timestamp(ultima_periodo["fecha_dato"]).strftime("%m/%Y"),
        delta=(
            f"{_numero_es(float(cambio_mensual), 1)}% frente al mes anterior"
            if pd.notna(cambio_mensual)
            else None
        ),
        delta_color="off",
    )
    columnas[2].markdown(
        f"**Cambio interanual:** "
        f"{_numero_es(float(cambio_anual), 1) + '%' if pd.notna(cambio_anual) else 'Sin dato'}  \n"
        f"**Fuente:** FNC"
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
        st.info("No hay exportaciones mensuales publicadas dentro del periodo elegido.")
        return
    st.plotly_chart(
        _grafico_exportaciones(exportaciones_periodo),
        width="stretch",
        theme=None,
        config=CONFIG_GRAFICO,
    )

    comparacion = _comparar_produccion_exportaciones(tabla_filtrada)
    if comparacion.empty:
        st.info("No hay meses comunes para comparar producción y exportaciones.")
        return
    ultima = comparacion.iloc[-1]
    diferencia = float(ultima["diferencia"])
    etiqueta = (
        "Producción no exportada en el mismo mes"
        if diferencia >= 0
        else "Exportaciones por encima de la producción del mes"
    )
    st.metric(
        etiqueta,
        f"{_numero_es(abs(diferencia), 1)} mil sacos de 60 kg",
        help=(
            "Diferencia descriptiva entre dos flujos mensuales. No equivale a "
            "inventario: puede incluir café producido en otros meses, rezagos "
            "logísticos y diferencias de registro."
        ),
    )
    st.plotly_chart(
        _grafico_diferencia_mensual(tabla_filtrada),
        width="stretch",
        theme=None,
        config=CONFIG_GRAFICO,
    )
    st.caption(
        "Un valor positivo indica producción superior a las exportaciones del "
        "mismo mes; uno negativo indica exportaciones superiores. La diferencia "
        "no mide directamente reservas ni consumo interno."
    )


def _metodologia_comercial() -> pd.DataFrame:
    """Devuelve la metodología comercial en el orden visible del catálogo."""
    filas = []
    variables = sorted(
        FUENTES_COMERCIALES,
        key=lambda variable: CATALOGO_VARIABLES[variable]["orden"],
    )
    for variable in variables:
        metadatos = FUENTES_COMERCIALES[variable]
        filas.append(
            {
                "Indicador": CATALOGO_VARIABLES[variable]["etiqueta"],
                "Tratamiento semanal": metadatos["metodo"],
            }
        )
    return pd.DataFrame(filas)


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

st.title("Herramienta Consultas y Reportes")
st.caption(
    "Kit de consulta y reporte para integrar, comparar y exportar "
    "evidencia comercial del café colombiano · "
    f"{semanas_disponibles_total} semanas cerradas hasta {ultima_semana:%d/%m/%Y} · "
    f"referencia comercial al {ultima_referencia:%d/%m/%Y}"
)
st.markdown(
    "Explore series para análisis, informes y reuniones. El panorama nacional "
    "permite leer conjuntamente precio interno FNC, Coffee C y USD/COP, y el "
    "simulador estima precio interno y margen bajo distintos supuestos."
)

st.sidebar.header("Filtros")
tipo_periodo = st.sidebar.radio(
    "Rango de análisis",
    options=["Periodo predefinido", "Fechas personalizadas"],
)
if tipo_periodo == "Periodo predefinido":
    periodo = st.sidebar.segmented_control(
        "Periodo",
        options=list(PERIODOS_VISUALIZACION),
        default="1 año",
        width="stretch",
    )
    semanas = PERIODOS_VISUALIZACION[periodo or "1 año"]
    filtrados = _filtrar_periodo(datos, semanas)
else:
    fecha_minima = datos["semana_fin"].min().date()
    fecha_maxima = datos["semana_fin"].max().date()
    rango = st.sidebar.date_input(
        "Fechas de cierre",
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
st.sidebar.caption("Autor: Juan José Jaramillo")

tab_panorama, tab_proyeccion = st.tabs(
    [
        "Panorama nacional",
        "Simulador",
    ],
    default="Panorama nacional",
    key="vistas_principales",
)

with tab_panorama:
    st.subheader("Lectura conjunta comercial")
    st.caption(
        "Movimiento descriptivo de las tres series. Las variaciones no implican "
        "causalidad ni califican el resultado como favorable o desfavorable."
    )
    _metricas_mercado(filtrados)
    st.plotly_chart(
        _grafico_mercado(filtrados),
        width="stretch",
        theme=None,
        config=CONFIG_GRAFICO,
    )
    st.caption(
        "Índice base 100 desde enero de 2023: permite comparar dirección y magnitud "
        "relativa entre series con unidades distintas."
    )
    st.markdown("**Variaciones por indicador**")
    st.dataframe(
        _variaciones_mercado(datos_semanales).style.format(
            {
                "Semanal": "{:+.1f}%",
                "Mensual (4 sem.)": "{:+.1f}%",
                "Anual (52 sem.)": "{:+.1f}%",
            },
            na_rep="Sin dato",
        ),
        hide_index=True,
        width="stretch",
    )
    st.subheader("Producción y exportaciones mensuales")
    _bloque_produccion_exportaciones(filtrados, datos)

    st.subheader("Exportar para informes y reuniones")
    descarga = preparar_descarga_comercial(filtrados)
    nombre_archivo = (
        f"monitor_agro_comercial_{filtrados['semana_fin'].min():%Y%m%d}_"
        f"{filtrados['semana_fin'].max():%Y%m%d}.csv"
    )
    inicio_brief = pd.Timestamp(filtrados["semana_fin"].min())
    fin_brief = pd.Timestamp(filtrados["semana_fin"].max())
    clave_pdf = f"{inicio_brief:%Y%m%d}_{fin_brief:%Y%m%d}"
    col_csv, col_brief = st.columns(2)
    col_csv.download_button(
        "Descargar series comerciales (CSV)",
        data=descarga.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
        file_name=nombre_archivo,
        mime="text/csv",
        width="stretch",
        help="Incluye valores, variaciones, unidad, fuente, alcance y fecha real del dato.",
    )
    col_brief.download_button(
        "Descargar brief del periodo (PDF)",
        data=_brief_pdf(inicio_brief, fin_brief, Path(RUTA_SERIES).stat().st_mtime),
        file_name=f"brief_monitor_agro_{clave_pdf}.pdf",
        mime="application/pdf",
        width="stretch",
        help="Documento con las gráficas, las variaciones y las fuentes del periodo.",
    )
    with st.expander("Cobertura y metodología comercial"):
        st.markdown(
            "Las tres series se comparan semanalmente, pero conservan su unidad y "
            "la fecha real del dato. El índice base 100 facilita comparar tendencias; "
            "no convierte las variables a una misma unidad ni demuestra causalidad."
        )
        st.dataframe(
            _resumen_fuentes_comerciales(filtrados),
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
st.caption(
    "Fuentes: FNC, Open-Meteo y Yahoo Finance vía yfinance. "
    "Visualización exploratoria; no contiene score de oportunidad o riesgo."
)
st.caption(
    "© 2026 Juan José Jaramillo · Todos los derechos reservados."
)
