from datetime import date, timedelta
import unittest

import pandas as pd

from config import DEPARTAMENTOS
from procesar.calidad import COLUMNAS_HISTORICO_SEMANAL
from procesar.indicadores import calcular, crear_resumen


class IndicadoresTemporalesTests(unittest.TestCase):
    def _serie(self, valores: list[float], variable: str = "fx_usd_local") -> pd.DataFrame:
        inicio = date(2026, 1, 4)
        filas = []
        for indice, valor in enumerate(valores):
            semana = inicio + timedelta(weeks=indice)
            filas.append(
                [
                    semana,
                    semana,
                    "COLOMBIA",
                    variable,
                    valor,
                    "COP/USD",
                    "yfinance",
                    5,
                ]
            )
        return pd.DataFrame(filas, columns=COLUMNAS_HISTORICO_SEMANAL)

    def test_calcula_cambios_y_promedio_movil(self) -> None:
        historico = self._serie([100.0, 110.0, 121.0, 133.1, 146.41])

        resultado = calcular(historico)
        ultima = resultado[resultado["semana_fin"] == date(2026, 2, 1)]

        cambio_1s = ultima[ultima["indicador"] == "cambio_1s_pct"].iloc[0]
        cambio_4s = ultima[ultima["indicador"] == "cambio_4s_pct"].iloc[0]
        promedio = ultima[ultima["indicador"] == "promedio_movil_4s"].iloc[0]
        self.assertAlmostEqual(cambio_1s["valor"], 10.0)
        self.assertAlmostEqual(cambio_4s["valor"], 46.41)
        self.assertAlmostEqual(promedio["valor"], 127.6275)

    def test_anomalia_usa_solo_semanas_anteriores(self) -> None:
        valores = [9.0, 11.0] * 13 + [20.0]
        resultado = calcular(self._serie(valores))
        anomalia = resultado[resultado["indicador"] == "anomalia_z_52s"].iloc[-1]

        self.assertAlmostEqual(anomalia["valor"], 10.0)
        self.assertEqual(anomalia["observaciones"], 26)

    def test_produccion_calcula_cambios_mensual_e_interanual(self) -> None:
        inicio = pd.Timestamp("2025-01-01")
        filas = []
        for indice in range(13):
            fecha = (inicio + pd.DateOffset(months=indice)).date()
            semana = fecha + timedelta(days=6 - fecha.weekday())
            filas.append(
                [
                    semana,
                    fecha,
                    "COLOMBIA",
                    "produccion_nacional",
                    100.0 + indice * 10,
                    "miles_sacos_60kg",
                    "FNC",
                    1,
                ]
            )
        historico = pd.DataFrame(filas, columns=COLUMNAS_HISTORICO_SEMANAL)

        resultado = calcular(historico)
        indicadores = set(resultado["indicador"])

        self.assertIn("cambio_1m_pct", indicadores)
        self.assertIn("cambio_12m_pct", indicadores)
        self.assertNotIn("cambio_1s_pct", indicadores)


class ComparacionesDepartamentalesTests(unittest.TestCase):
    def setUp(self) -> None:
        semana = date(2026, 1, 4)
        filas = []
        for posicion, departamento in enumerate(DEPARTAMENTOS, start=1):
            filas.append(
                [
                    semana,
                    semana,
                    departamento,
                    "precipitacion_semanal",
                    float(posicion),
                    "mm",
                    "open-meteo",
                    7,
                ]
            )
        self.historico = pd.DataFrame(filas, columns=COLUMNAS_HISTORICO_SEMANAL)

    def test_ranking_uno_es_valor_mas_alto(self) -> None:
        resultado = calcular(self.historico)
        ultimo_departamento = DEPARTAMENTOS[-1]
        fila = resultado[
            (resultado["geografia"] == ultimo_departamento)
            & (resultado["indicador"] == "ranking_departamental")
        ].iloc[0]
        percentil = resultado[
            (resultado["geografia"] == ultimo_departamento)
            & (resultado["indicador"] == "percentil_departamental")
        ].iloc[0]

        self.assertEqual(fila["valor"], 1.0)
        self.assertEqual(percentil["valor"], 100.0)

    def test_resumen_acepta_fechas_csv(self) -> None:
        historico = self.historico.copy()
        historico["semana_fin"] = historico["semana_fin"].astype(str)
        indicadores = calcular(historico)

        resumen = crear_resumen(historico, indicadores)

        self.assertEqual(len(resumen), len(DEPARTAMENTOS))
        self.assertIn("ranking_departamental", resumen.columns)
        self.assertTrue(resumen["ranking_departamental"].notna().all())


if __name__ == "__main__":
    unittest.main()
