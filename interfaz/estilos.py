"""Tema CSS de la interfaz Streamlit."""

import streamlit as st

from config import COLORES_INTERFAZ


def aplicar_estilos() -> None:
    """Aplica el lenguaje visual compartido de la aplicación."""
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
        h1 {{
            font-size: 2rem;
            font-weight: 700;
            letter-spacing: -0.01em;
            margin-bottom: 0.15rem;
        }}
        h1 + div[data-testid="stCaptionContainer"] {{ margin-bottom: 0.6rem; }}
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
        [data-testid="stExpander"] summary {{ transition: color 120ms ease; }}
        [data-testid="stExpander"] summary:hover {{ color: var(--monitor-acento) !important; }}
        [data-testid="stAlert"] {{
            background: var(--monitor-superficie);
            border: 1px solid var(--monitor-borde);
            border-left: 4px solid var(--monitor-acento);
            border-radius: 10px;
        }}
        [data-testid="stDataFrame"] {{
            border: 1px solid var(--monitor-borde);
            border-radius: 10px;
            overflow: hidden;
        }}
        [data-testid="stDataFrame"] [data-testid="stDataFrameResizable"] {{
            border-radius: 10px;
        }}
        [data-testid="stDataFrame"] thead tr th {{
            background: var(--monitor-sidebar) !important;
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
            padding-bottom: 0.5rem;
            font-size: 1.02rem;
            border-bottom: 3px solid transparent;
            transition: color 120ms ease, border-color 120ms ease;
        }}
        .stTabs [data-baseweb="tab"] p {{ color: inherit !important; font-weight: 500; }}
        .stTabs [data-baseweb="tab"]:hover {{ color: var(--monitor-acento) !important; }}
        .stTabs [aria-selected="true"] {{
            color: var(--monitor-acento) !important;
            border-bottom-color: var(--monitor-acento);
        }}
        @media (max-width: 1024px) {{
            .block-container {{ padding: 1.2rem 1rem 2.5rem; }}
            [data-testid="stMetric"] {{ min-height: 120px; }}
        }}
        @media (max-width: 768px) {{
            .block-container {{ padding: 1rem 0.8rem 2rem; }}
            h1 {{ font-size: 1.65rem; }}
            [data-testid="stMetric"] {{ min-height: 112px; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
