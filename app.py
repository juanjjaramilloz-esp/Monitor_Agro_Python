"""Dashboard descriptivo para explorar mercado, Caldas y departamentos."""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config import (
    CATALOGO_VARIABLES,
    COLORES_INTERFAZ,
    DEPARTAMENTOS,
    FUENTES_COMERCIALES,
    GEOGRAFIA_PRIORITARIA,
    PERIODOS_VISUALIZACION,
)
from procesar.visualizacion import (
    RUTA_SERIES,
    ejecutar as preparar_visualizacion,
    preparar_descarga_comercial,
)


CONFIG_GRAFICO = {
    "displaylogo": False,
    "responsive": True,
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
}


st.set_page_config(
    page_title="Monitor Agro Colombia",
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
        h3 {{ font-size: 1rem; }}
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
            border-radius: 6px;
            padding: 0.8rem 0.9rem;
            min-height: 128px;
        }}
        [data-testid="stMetricLabel"] {{ color: var(--monitor-secundario) !important; }}
        [data-testid="stMetricValue"] {{
            color: var(--monitor-texto) !important;
            font-size: 1.55rem;
        }}
        [data-testid="stMetricDelta"] {{ color: var(--monitor-secundario) !important; }}
        [data-testid="stPlotlyChart"] {{
            background: var(--monitor-superficie);
            border: 1px solid var(--monitor-borde);
            border-radius: 6px;
        }}
        .stTabs [data-baseweb="tab-list"] {{ gap: 1.25rem; }}
        .stTabs [data-baseweb="tab"] {{
            color: var(--monitor-secundario) !important;
            padding-left: 0;
            padding-right: 0;
        }}
        .stTabs [data-baseweb="tab"] p {{ color: inherit !important; }}
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
    if not ruta.exists():
        preparar_visualizacion()
    return _leer_series(str(ruta), ruta.stat().st_mtime)


def _numero_es(valor: float, decimales: int) -> str:
    texto = f"{valor:,.{decimales}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def _valor_metrica(fila: pd.Series) -> str:
    valor = _numero_es(float(fila["valor"]), int(fila["decimales"]))
    return f"{valor} {fila['unidad']}"


def _delta_pct(fila: pd.Series) -> str | None:
    if pd.isna(fila["cambio_1s_pct"]):
        return None
    return f"{_numero_es(float(fila['cambio_1s_pct']), 1)}% semanal"


def _delta_absoluto(fila: pd.Series) -> str | None:
    if pd.isna(fila["cambio_1s_absoluto"]):
        return None
    decimales = int(fila["decimales"])
    cambio = _numero_es(float(fila["cambio_1s_absoluto"]), decimales)
    return f"{cambio} {fila['unidad']} semanal"


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
        margin=dict(l=24, r=20, t=52, b=28),
        paper_bgcolor=colores["superficie"],
        plot_bgcolor=colores["superficie"],
        font=dict(color=colores["texto"], size=12),
        title_font=dict(size=16),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        xaxis=dict(showgrid=False, title=None),
        yaxis=dict(gridcolor=colores["rejilla"], zeroline=False, title=None),
    )
    return figura


def _grafico_mercado(tabla: pd.DataFrame) -> go.Figure:
    figura = go.Figure()
    mercado = tabla[tabla["categoria"] == "Mercado"]
    for variable, grupo in mercado.groupby("variable", sort=False):
        metadatos = CATALOGO_VARIABLES[variable]
        figura.add_trace(
            go.Scatter(
                x=grupo["semana_fin"],
                y=grupo["indice_base_100"],
                mode="lines",
                name=metadatos["etiqueta"],
                line=dict(color=metadatos["color"], width=2.5),
                customdata=grupo[["valor", "unidad"]],
                hovertemplate=(
                    "%{x|%d %b %Y}<br>Índice: %{y:.1f}<br>"
                    "Valor: %{customdata[0]:,.1f} %{customdata[1]}<extra></extra>"
                ),
            )
        )
    figura.add_hline(y=100, line_dash="dot", line_color="#9CA39D", line_width=1)
    figura.update_layout(title="Evolución comercial comparable · base 100")
    return _layout(figura, 430)


def _grafico_lluvia(tabla: pd.DataFrame, departamento: str) -> go.Figure:
    datos = tabla[
        (tabla["geografia"] == departamento)
        & (tabla["variable"] == "precipitacion_semanal")
    ]
    color = CATALOGO_VARIABLES["precipitacion_semanal"]["color"]
    figura = go.Figure()
    figura.add_trace(
        go.Bar(
            x=datos["semana_fin"],
            y=datos["valor"],
            name="Precipitación",
            marker_color=color,
            opacity=0.68,
            hovertemplate="%{x|%d %b %Y}<br>%{y:.1f} mm<extra></extra>",
        )
    )
    figura.add_trace(
        go.Scatter(
            x=datos["semana_fin"],
            y=datos["promedio_movil_4s"],
            name="Promedio 4 semanas",
            line=dict(color="#174E73", width=2.5),
            hovertemplate="%{x|%d %b %Y}<br>%{y:.1f} mm<extra></extra>",
        )
    )
    figura.update_layout(title=f"Precipitación · {departamento}", bargap=0.1)
    return _layout(figura, 390)


def _grafico_temperaturas(tabla: pd.DataFrame, departamento: str) -> go.Figure:
    variables = ["temp_min_semanal", "temp_promedio_semanal", "temp_max_semanal"]
    datos = tabla[(tabla["geografia"] == departamento) & tabla["variable"].isin(variables)]
    figura = go.Figure()
    for variable in variables:
        grupo = datos[datos["variable"] == variable]
        metadatos = CATALOGO_VARIABLES[variable]
        figura.add_trace(
            go.Scatter(
                x=grupo["semana_fin"],
                y=grupo["valor"],
                mode="lines",
                name=metadatos["etiqueta"].replace(" semanal", ""),
                line=dict(
                    color=metadatos["color"],
                    width=3 if variable == "temp_promedio_semanal" else 1.8,
                ),
                hovertemplate="%{x|%d %b %Y}<br>%{y:.1f} °C<extra></extra>",
            )
        )
    figura.update_layout(title=f"Temperaturas · {departamento}")
    return _layout(figura, 390)


def _grafico_ranking(
    tabla: pd.DataFrame,
    variable: str,
    semana: pd.Timestamp,
    departamento: str,
) -> go.Figure:
    datos = tabla[
        (tabla["semana_fin"] == semana) & (tabla["variable"] == variable)
    ].sort_values("valor", ascending=True)
    metadatos = CATALOGO_VARIABLES[variable]
    colores = [
        COLORES_INTERFAZ["acento"]
        if geografia == departamento
        else COLORES_INTERFAZ["comparacion"]
        for geografia in datos["geografia"]
    ]
    figura = go.Figure(
        go.Bar(
            x=datos["valor"],
            y=datos["geografia"],
            orientation="h",
            marker_color=colores,
            customdata=datos[["municipio_referencia", "unidad"]],
            hovertemplate=(
                "%{y} · %{customdata[0]}<br>%{x:.1f} %{customdata[1]}<extra></extra>"
            ),
        )
    )
    figura.update_layout(
        title=f"Comparación departamental · {metadatos['etiqueta']}",
        hovermode="closest",
        showlegend=False,
    )
    return _layout(figura, 440)


def _grafico_vs_mediana(
    tabla: pd.DataFrame,
    variable: str,
    departamento: str,
) -> go.Figure:
    datos = tabla[tabla["variable"] == variable]
    seleccionado = datos[datos["geografia"] == departamento]
    mediana = datos.groupby("semana_fin", as_index=False)["valor"].median()
    metadatos = CATALOGO_VARIABLES[variable]
    figura = go.Figure()
    figura.add_trace(
        go.Scatter(
            x=seleccionado["semana_fin"],
            y=seleccionado["valor"],
            mode="lines",
            name=departamento,
            line=dict(color=COLORES_INTERFAZ["acento"], width=3),
        )
    )
    figura.add_trace(
        go.Scatter(
            x=mediana["semana_fin"],
            y=mediana["valor"],
            mode="lines",
            name="Mediana de 8 departamentos",
            line=dict(color=COLORES_INTERFAZ["comparacion"], width=2, dash="dash"),
        )
    )
    figura.update_traces(
        hovertemplate=(
            f"%{{x|%d %b %Y}}<br>%{{y:.1f}} "
            f"{seleccionado.iloc[0]['unidad']}<extra></extra>"
        )
    )
    figura.update_layout(
        title=f"{departamento} frente a la mediana · {metadatos['etiqueta']}"
    )
    return _layout(figura, 390)


def _metricas_mercado(tabla: pd.DataFrame) -> None:
    ultima = tabla["semana_fin"].max()
    datos = tabla[(tabla["semana_fin"] == ultima) & (tabla["categoria"] == "Mercado")]
    columnas = st.columns(3)
    variables = ["fx_usd_local", "precio_cafe_arabica", "precio_interno_referencia"]
    for columna, variable in zip(columnas, variables):
        fila = datos[datos["variable"] == variable].iloc[0]
        historial = tabla[tabla["variable"] == variable].sort_values("semana_fin").tail(12)
        columna.metric(
            label=fila["etiqueta_variable"],
            value=_valor_metrica(fila),
            delta=_delta_pct(fila),
            delta_color="off",
            chart_data=historial["valor"].tolist(),
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
    mercado = tabla[tabla["categoria"].eq("Mercado")].copy()
    indices = mercado.groupby("variable")["semana_fin"].idxmax()
    ultimos = mercado.loc[indices]
    filas = []
    for _, fila in ultimos.iterrows():
        metadatos = FUENTES_COMERCIALES[fila["variable"]]
        filas.append(
            {
                "Indicador": fila["etiqueta_variable"],
                "Último dato": pd.Timestamp(fila["fecha_dato"]).strftime("%d/%m/%Y"),
                "Unidad": fila["unidad"],
                "Fuente": metadatos["nombre"],
                "Alcance": metadatos["alcance"],
            }
        )
    return pd.DataFrame(filas)


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


def _metricas_clima(tabla: pd.DataFrame, departamento: str) -> None:
    ultima = tabla["semana_fin"].max()
    datos = tabla[(tabla["semana_fin"] == ultima) & (tabla["geografia"] == departamento)]
    variables = [
        "precipitacion_semanal",
        "temp_min_semanal",
        "temp_promedio_semanal",
        "temp_max_semanal",
    ]
    columnas = st.columns(4)
    for columna, variable in zip(columnas, variables):
        fila = datos[datos["variable"] == variable].iloc[0]
        delta = _delta_pct(fila) if variable == "precipitacion_semanal" else _delta_absoluto(fila)
        historial = tabla[
            (tabla["geografia"] == departamento) & (tabla["variable"] == variable)
        ].sort_values("semana_fin").tail(12)
        columna.metric(
            label=fila["etiqueta_variable"],
            value=_valor_metrica(fila),
            delta=delta,
            delta_color="off",
            chart_data=historial["valor"].tolist(),
            chart_type="bar" if variable == "precipitacion_semanal" else "line",
            help=fila["descripcion_variable"],
        )


_estilos()
datos = _cargar_datos()
ultima_semana = datos["semana_fin"].max()
semanas_disponibles_total = datos["semana_fin"].nunique()

st.title("Monitor Agro Colombia")
st.caption(
    "Herramienta de consulta y reporte para integrar, comparar y exportar "
    "evidencia comercial del café colombiano · "
    f"{semanas_disponibles_total} semanas · datos hasta {ultima_semana:%d/%m/%Y}"
)
st.markdown(
    "Explore series para análisis, informes y reuniones. El panorama nacional "
    "permite leer conjuntamente precio interno FNC, Coffee C y USD/COP; las "
    "vistas territoriales conservan el contexto climático ya disponible."
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
departamento = st.sidebar.selectbox(
    "Departamento / zona de referencia",
    options=DEPARTAMENTOS,
    index=DEPARTAMENTOS.index(GEOGRAFIA_PRIORITARIA),
)
municipio = datos.loc[
    datos["geografia"] == departamento, "municipio_referencia"
].iloc[0]
st.sidebar.markdown(f"**Referencia climática:** {municipio}")
st.sidebar.caption("Ranking 1 = valor numérico más alto, no mejor resultado.")

tab_panorama, tab_departamento, tab_comparacion = st.tabs(
    ["Panorama nacional", f"{departamento} · {municipio}", "Comparación"],
    default=f"{departamento} · {municipio}",
    key=f"vistas_{departamento}",
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
    st.dataframe(
        _variaciones_mercado(datos).style.format(
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
    descarga = preparar_descarga_comercial(filtrados)
    nombre_archivo = (
        f"monitor_agro_comercial_{filtrados['semana_fin'].min():%Y%m%d}_"
        f"{filtrados['semana_fin'].max():%Y%m%d}.csv"
    )
    st.download_button(
        "Descargar series comerciales (CSV)",
        data=descarga.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
        file_name=nombre_archivo,
        mime="text/csv",
        width="stretch",
        help="Incluye valores, variaciones, unidad, fuente, alcance y fecha real del dato.",
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

with tab_departamento:
    st.subheader(f"{departamento} · referencia {municipio}")
    _metricas_clima(filtrados, departamento)
    col_lluvia, col_temperatura = st.columns(2)
    with col_lluvia:
        st.plotly_chart(
            _grafico_lluvia(filtrados, departamento),
            width="stretch",
            theme=None,
            config=CONFIG_GRAFICO,
        )
    with col_temperatura:
        st.plotly_chart(
            _grafico_temperaturas(filtrados, departamento),
            width="stretch",
            theme=None,
            config=CONFIG_GRAFICO,
        )
    st.caption(
        "El clima representa una coordenada municipal de referencia y no toda la "
        "variación interna del departamento."
    )

with tab_comparacion:
    opciones_clima = {
        CATALOGO_VARIABLES[variable]["etiqueta"]: variable
        for variable in CATALOGO_VARIABLES
        if CATALOGO_VARIABLES[variable]["categoria"] == "Clima"
    }
    etiqueta = st.selectbox("Variable climática", options=list(opciones_clima))
    variable = opciones_clima[etiqueta]
    semanas_disponibles = sorted(filtrados["semana_fin"].unique())
    semana_comparacion = st.select_slider(
        "Semana de comparación",
        options=semanas_disponibles,
        value=semanas_disponibles[-1],
        format_func=lambda fecha: pd.Timestamp(fecha).strftime("%d/%m/%Y"),
    )
    col_ranking, col_historia = st.columns([0.9, 1.1])
    with col_ranking:
        st.plotly_chart(
            _grafico_ranking(filtrados, variable, semana_comparacion, departamento),
            width="stretch",
            theme=None,
            config=CONFIG_GRAFICO,
        )
    with col_historia:
        st.plotly_chart(
            _grafico_vs_mediana(filtrados, variable, departamento),
            width="stretch",
            theme=None,
            config=CONFIG_GRAFICO,
        )

st.divider()
st.caption(
    "Fuentes: FNC, Open-Meteo y Yahoo Finance vía yfinance. "
    "Visualización exploratoria; no contiene score de oportunidad o riesgo."
)
