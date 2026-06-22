"""
Fuente: clima en zonas cafeteras (Open-Meteo, sin key, solo uso no comercial).

Contrato de salida (ver CLAUDE.md, sección 4):
    fecha    : date
    geografia: str  — nombre del departamento cafetero (ej. "Huila")
    variable : str  — "temp_min" | "temp_max" | "precipitacion"
    valor    : float
    unidad   : str  — "°C" | "mm"
    fuente   : str  — "open-meteo"

Las coordenadas de cada departamento cafetero se leen de config.REGIONES_CAFE.
"""

import pandas as pd
import requests

from config import CLIMA_DIAS_ATRAS, CLIMA_VARIABLES, REGIONES_CAFE


COLUMNAS = ["fecha", "geografia", "variable", "valor", "unidad", "fuente"]

URL_OPEN_METEO = "https://api.open-meteo.com/v1/forecast"
MAPEO_VARIABLES = {
    "temperature_2m_min": ("temp_min", "°C"),
    "temperature_2m_max": ("temp_max", "°C"),
    "precipitation_sum": ("precipitacion", "mm"),
}


def obtener() -> pd.DataFrame:
    """Devuelve variables climáticas diarias para cada zona cafetera."""
    filas: list[dict] = []

    for region in REGIONES_CAFE:
        departamento = region["departamento"]
        parametros = {
            "latitude": region["lat"],
            "longitude": region["lon"],
            "daily": ",".join(CLIMA_VARIABLES),
            "past_days": CLIMA_DIAS_ATRAS,
            "forecast_days": 1,
            "timezone": "auto",
        }

        try:
            respuesta = requests.get(URL_OPEN_METEO, params=parametros, timeout=20)
            respuesta.raise_for_status()
            datos = respuesta.json()
            diarios = datos.get("daily", {})
            fechas = diarios.get("time", [])

            if not fechas:
                print(f"  AVISO: {departamento} - Open-Meteo no devolvio fechas.")
                continue

            for variable_api in CLIMA_VARIABLES:
                if variable_api not in MAPEO_VARIABLES:
                    print(f"  AVISO: {variable_api} - variable climatica sin mapeo.")
                    continue

                nombre_variable, unidad = MAPEO_VARIABLES[variable_api]
                valores = diarios.get(variable_api, [])

                if not valores:
                    print(f"  AVISO: {departamento} - sin datos para {variable_api}.")
                    continue

                for fecha, valor in zip(fechas, valores):
                    if valor is None:
                        continue

                    filas.append({
                        "fecha": pd.to_datetime(fecha).date(),
                        "geografia": departamento,
                        "variable": nombre_variable,
                        "valor": float(valor),
                        "unidad": unidad,
                        "fuente": "open-meteo",
                    })

        except Exception as e:
            print(f"  AVISO: {departamento} - error al consultar Open-Meteo: {e}")

    return pd.DataFrame(filas, columns=COLUMNAS)


if __name__ == "__main__":
    df = obtener()
    print("fuentes.clima - resultado")
    print(f"  shape : {df.shape}")
    print(f"  tipos :\n{df.dtypes}")
    print(f"\n{df.head(15)}")
