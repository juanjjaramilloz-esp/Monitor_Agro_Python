"""
Configuración central del Monitor Agro LatAm.

REGLA DE ORO (ver CLAUDE.md, sección 2): todo lo que pueda cambiar vive AQUÍ.
La lógica de los módulos nunca debe tener valores "quemados". Para agregar un
país, mover una coordenada o ajustar un peso del score, se edita solo este
archivo.
"""

from datetime import date
from pathlib import Path

# ---------------------------------------------------------------------------
# Rutas del proyecto
# ---------------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parent
DIR_DATOS = RAIZ / "datos"
DIR_SNAPSHOTS = DIR_DATOS / "snapshots"
DIR_HISTORICO = DIR_DATOS / "historico"
DIR_INDICADORES = DIR_DATOS / "indicadores"
DIR_VISUALIZACION = DIR_DATOS / "visualizacion"

# Ventana inicial del backfill. Se puede cambiar sin tocar la lógica.
HISTORICO_FECHA_INICIO = date(2023, 1, 1)
HISTORICO_RETRASO_CLIMA_DIAS = 5

# Ventanas descriptivas del Bloque 3. No expresan todavía criterio cafetero.
INDICADORES_VENTANA_CORTA = 4
INDICADORES_VENTANA_LARGA = 12
INDICADORES_VENTANA_ANOMALIA = 52
INDICADORES_MIN_OBS_ANOMALIA = 26
GEOGRAFIA_PRIORITARIA = "Caldas"
VARIABLES_CAMBIO_PORCENTUAL = {
    "fx_usd_local",
    "precio_cafe_arabica",
    "precio_interno_referencia",
    "precipitacion_semanal",
}
VARIABLES_INDICE_BASE_100 = {
    "fx_usd_local",
    "precio_cafe_arabica",
    "precio_interno_referencia",
}
UMBRAL_ANOMALIA_MODERADA = 1.0
UMBRAL_ANOMALIA_ALTA = 2.0
PERIODOS_VISUALIZACION = {
    "6 meses": 26,
    "1 año": 52,
    "Todo": None,
}
COLORES_INTERFAZ = {
    "texto": "#17211B",
    "texto_secundario": "#5F6B63",
    "fondo": "#F7F8F5",
    "sidebar": "#EFF3EE",
    "superficie": "#FFFFFF",
    "borde": "#DDE3DD",
    "acento": "#176B4D",
    "comparacion": "#8A8178",
    "rejilla": "#E7EBE7",
}

# Metadatos de presentación. Las etiquetas no alteran los datos ni el score.
CATALOGO_VARIABLES = {
    "fx_usd_local": {
        "etiqueta": "Tasa de cambio USD/COP",
        "descripcion": "Pesos colombianos por un dólar estadounidense",
        "categoria": "Mercado",
        "orden": 1,
        "decimales": 0,
        "color": "#2563EB",
    },
    "precio_cafe_arabica": {
        "etiqueta": "Precio internacional del café arábica",
        "descripcion": "Futuro ICE Coffee C expresado en centavos de dólar por libra",
        "categoria": "Mercado",
        "orden": 2,
        "decimales": 1,
        "color": "#0F766E",
    },
    "precio_interno_referencia": {
        "etiqueta": "Precio interno de referencia FNC",
        "descripcion": "Precio base por carga de 125 kg de café pergamino seco",
        "categoria": "Mercado",
        "orden": 3,
        "decimales": 0,
        "color": "#B7791F",
    },
    "precipitacion_semanal": {
        "etiqueta": "Precipitación semanal",
        "descripcion": "Lluvia acumulada en la coordenada municipal de referencia",
        "categoria": "Clima",
        "orden": 4,
        "decimales": 1,
        "color": "#0284C7",
    },
    "temp_min_semanal": {
        "etiqueta": "Temperatura mínima semanal",
        "descripcion": "Menor temperatura mínima diaria de la semana",
        "categoria": "Clima",
        "orden": 5,
        "decimales": 1,
        "color": "#4F46E5",
    },
    "temp_max_semanal": {
        "etiqueta": "Temperatura máxima semanal",
        "descripcion": "Mayor temperatura máxima diaria de la semana",
        "categoria": "Clima",
        "orden": 6,
        "decimales": 1,
        "color": "#DC2626",
    },
    "temp_promedio_semanal": {
        "etiqueta": "Temperatura promedio semanal",
        "descripcion": "Promedio de los puntos medios diarios de temperatura",
        "categoria": "Clima",
        "orden": 7,
        "decimales": 1,
        "color": "#D97706",
    },
}

# ---------------------------------------------------------------------------
# Geografía nacional (Colombia)
#
# PIVOTE A COLOMBIA: el monitor dejó de comparar países de LatAm y ahora se
# enfoca en Colombia, comparando sus departamentos cafeteros. Las variables
# de alcance nacional (FX, precio interno, noticias) usan estos códigos.
# Los países LatAm retirados quedan recuperables en el historial de git.
# ---------------------------------------------------------------------------
GEOGRAFIA_PAIS = "COLOMBIA"   # etiqueta de geografía para datos nacionales
GEOGRAFIA_GLOBAL = "GLOBAL"    # etiqueta para indicadores internacionales
PAIS_FIPS = "CO"              # código FIPS de Colombia (lo usa GDELT)

# ---------------------------------------------------------------------------
# Departamentos cafeteros de Colombia (clima)
#
# Cada región incluye:
#   departamento : nombre del departamento (es la 'geografia' de cada fila)
#   municipio    : municipio cafetero representativo (referencia humana)
#   lat / lon    : coordenada del municipio para consultar Open-Meteo
# ---------------------------------------------------------------------------
REGIONES_CAFE = [
    {"departamento": "Huila",      "municipio": "Pitalito",   "lat": 1.85,  "lon": -76.05},
    {"departamento": "Antioquia",  "municipio": "Andes",      "lat": 5.66,  "lon": -75.88},
    {"departamento": "Tolima",     "municipio": "Líbano",     "lat": 4.92,  "lon": -75.06},
    {"departamento": "Cauca",      "municipio": "Popayán",    "lat": 2.44,  "lon": -76.61},
    {"departamento": "Nariño",     "municipio": "La Unión",   "lat": 1.60,  "lon": -77.13},
    {"departamento": "Caldas",     "municipio": "Manizales",  "lat": 5.07,  "lon": -75.52},
    {"departamento": "Risaralda",  "municipio": "Pereira",    "lat": 4.81,  "lon": -75.69},
    {"departamento": "Quindío",    "municipio": "Armenia",    "lat": 4.53,  "lon": -75.68},
]

# ---------------------------------------------------------------------------
# FX (Fase 1a) — solo USD/COP
#
# Tras el pivote a Colombia el FX relevante es uno solo: USD/COP. Se usa
# yfinance (Frankfurter/BCE no cubre COP). geografia = COLOMBIA.
# ---------------------------------------------------------------------------
TICKER_FX = "USDCOP=X"
MONEDA = "COP"

# ---------------------------------------------------------------------------
# Café (Fase 1b)
# ---------------------------------------------------------------------------
# Futuro ICE Coffee C (arábica) en Yahoo Finance; precio global, diario.
TICKER_CAFE_ARABICA = "KC=F"
# Robusta (opcional, segundo commodity): "RM=F" en algunos feeds. Validar.
TICKER_CAFE_ROBUSTA = None
# Alpha Vantage = contexto MENSUAL (requiere API key gratuita).
# La key NO va aquí: se lee de la variable de entorno ALPHAVANTAGE_API_KEY.

# ---------------------------------------------------------------------------
# Precio interno de referencia FNC (Colombia)
# ---------------------------------------------------------------------------
# Página de estadísticas cafeteras de la Federación Nacional de Cafeteros.
# Se raspa el HTML del servidor (no requiere JS). Es scraping: frágil.
URL_PRECIO_INTERNO_FNC = "https://federaciondecafeteros.org/wp/estadisticas-cafeteras/"
FNC_PATRON_ARCHIVO_HISTORICO = "Precios-area-y-produccion-de-cafe"
FNC_PREFIJO_HOJA_PRECIO_DIARIO = "1. Precio Interno Diario"
FNC_FILA_ENCABEZADO_HISTORICO = 5
FNC_COLUMNA_FECHA_HISTORICO = "Fecha"
FNC_COLUMNA_PRECIO_HISTORICO = "Precio Interno ($/125 Kg)"

# ---------------------------------------------------------------------------
# Clima (Fase 1c) — Open-Meteo
# ---------------------------------------------------------------------------
# Variables diarias a pedir por zona cafetera.
CLIMA_VARIABLES = ["temperature_2m_min", "temperature_2m_max", "precipitation_sum"]
# Cuántos días hacia atrás traer en cada corrida.
CLIMA_DIAS_ATRAS = 7
URL_OPEN_METEO_PRONOSTICO = "https://api.open-meteo.com/v1/forecast"
URL_OPEN_METEO_HISTORICO = "https://archive-api.open-meteo.com/v1/archive"

# ---------------------------------------------------------------------------
# Noticias (Fase 1d) — GDELT
# ---------------------------------------------------------------------------
IDIOMA_NOTICIAS = "spanish"
NOTICIAS_DIAS_ATRAS = 7
NOTICIAS_MAX_REGISTROS = 25
# Términos que disparan señales relevantes para agroexportación.
TERMINOS_NOTICIAS = [
    "café",
    "exportación",
    "paro",
    "bloqueo",
    "puerto",
    "EUDR",
    "helada",
    "sequía",
    "arancel",
]

# ---------------------------------------------------------------------------
# Score (Fase 3) — PROVISIONAL
# ---------------------------------------------------------------------------
# Los pesos reales se definen en la Fase 3, con datos en mano. No usar aún.
PESOS_OPORTUNIDAD: dict[str, float] = {}
PESOS_RIESGO: dict[str, float] = {}


# Atajo útil para recorrer solo los nombres de departamento.
DEPARTAMENTOS = [r["departamento"] for r in REGIONES_CAFE]
ORDEN_GEOGRAFIAS = [
    GEOGRAFIA_GLOBAL,
    GEOGRAFIA_PAIS,
    GEOGRAFIA_PRIORITARIA,
] + [d for d in DEPARTAMENTOS if d != GEOGRAFIA_PRIORITARIA]
