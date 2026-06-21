"""
Configuración central del Monitor Agro LatAm.

REGLA DE ORO (ver CLAUDE.md, sección 2): todo lo que pueda cambiar vive AQUÍ.
La lógica de los módulos nunca debe tener valores "quemados". Para agregar un
país, mover una coordenada o ajustar un peso del score, se edita solo este
archivo.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Rutas del proyecto
# ---------------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parent
DIR_DATOS = RAIZ / "datos"
DIR_SNAPSHOTS = DIR_DATOS / "snapshots"

# ---------------------------------------------------------------------------
# Países a monitorear
#
# Cada país incluye:
#   nombre        : nombre legible
#   iso3          : código ISO 3166-1 alfa-3 (Banco Mundial, etc.)
#   moneda        : código ISO 4217 de la moneda local
#   fips          : código país FIPS de 2 letras (lo usa GDELT para filtrar)
#   ticker_fx     : par USD/moneda local en Yahoo Finance (fuente de respaldo)
#   zona_cafetera : punto representativo de la principal región cafetera
#                   (lat/lon) para consultar el clima
#
# Nota FX: las tasas del BCE (Frankfurter) NO cubren COP, PEN ni HNL; solo
# BRL y MXN. Por eso guardamos un ticker de Yahoo para todas, y la decisión
# final de fuente se valida en vivo en la Fase 1a.
# ---------------------------------------------------------------------------
PAISES = [
    {
        "nombre": "Colombia",
        "iso3": "COL",
        "moneda": "COP",
        "fips": "CO",
        "ticker_fx": "USDCOP=X",
        "zona_cafetera": {"nombre": "Eje Cafetero (Manizales)", "lat": 5.07, "lon": -75.52},
    },
    {
        "nombre": "Brasil",
        "iso3": "BRA",
        "moneda": "BRL",
        "fips": "BR",
        "ticker_fx": "USDBRL=X",
        "zona_cafetera": {"nombre": "Sul de Minas (Varginha)", "lat": -21.55, "lon": -45.43},
    },
    {
        "nombre": "Perú",
        "iso3": "PER",
        "moneda": "PEN",
        "fips": "PE",
        "ticker_fx": "USDPEN=X",
        "zona_cafetera": {"nombre": "Chanchamayo (Junín)", "lat": -11.05, "lon": -75.34},
    },
    {
        "nombre": "Honduras",
        "iso3": "HND",
        "moneda": "HNL",
        "fips": "HO",
        "ticker_fx": "USDHNL=X",
        "zona_cafetera": {"nombre": "Marcala (La Paz)", "lat": 14.16, "lon": -88.01},
    },
    {
        "nombre": "México",
        "iso3": "MEX",
        "moneda": "MXN",
        "fips": "MX",
        "ticker_fx": "USDMXN=X",
        "zona_cafetera": {"nombre": "Soconusco, Chiapas (Tapachula)", "lat": 14.90, "lon": -92.26},
    },
]

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
# Clima (Fase 1c) — Open-Meteo
# ---------------------------------------------------------------------------
# Variables diarias a pedir por zona cafetera.
CLIMA_VARIABLES = ["temperature_2m_min", "temperature_2m_max", "precipitation_sum"]
# Cuántos días hacia atrás traer en cada corrida.
CLIMA_DIAS_ATRAS = 7

# ---------------------------------------------------------------------------
# Noticias (Fase 1d) — GDELT
# ---------------------------------------------------------------------------
IDIOMA_NOTICIAS = "spanish"
NOTICIAS_DIAS_ATRAS = 7
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


# Atajo útil para recorrer solo los códigos ISO3.
ISO3 = [p["iso3"] for p in PAISES]
