from datetime import date, timedelta
import unittest

import pandas as pd

from procesar.calidad import COLUMNAS_HISTORICO_SEMANAL
from procesar.visualizacion import (
    _estado_anomalia,
    configuracion_eje_mensual,
    crear_resumen_visual,
    faltan_variables_historicas,
    filtrar_periodo_visualizacion,
    incorporar_referencia_comercial_actual,
    preparar,
    preparar_descarga_comercial,
)


class PreparacionVisualTests(unittest.TestCase):
    def _historico(self) -> pd.DataFrame:
        inicio = date(2026, 1, 4)
        filas = []
        for indice, valor in enumerate([4000.0, 4040.0, 4080.0, 4120.0, 4160.0]):
            semana = inicio + timedelta(weeks=indice)
            filas.append(
                [
                    semana,
                    semana,
                    "COLOMBIA",
                    "fx_usd_local",
                    valor,
                    "COP/USD",
                    "yfinance",
                    5,
                ]
            )
        filas.append(
            [
                inicio,
                inicio,
                "Caldas",
                "precipitacion_semanal",
                70.0,
                "mm",
                "open-meteo",
                7,
            ]
        )
        return pd.DataFrame(filas, columns=COLUMNAS_HISTORICO_SEMANAL)

    def test_agrega_metadatos_e_indice_base_100(self) -> None:
        historico = self._historico()

        resultado = preparar(historico)
        mercado = resultado[resultado["variable"] == "fx_usd_local"]
        caldas = resultado[resultado["geografia"] == "Caldas"].iloc[0]

        self.assertEqual(len(resultado), len(historico))
        self.assertEqual(mercado.iloc[0]["indice_base_100"], 100.0)
        self.assertEqual(mercado.iloc[-1]["indice_base_100"], 104.0)
        self.assertEqual(mercado.iloc[0]["etiqueta_variable"], "Tasa de cambio USD/COP")
        self.assertEqual(caldas["municipio_referencia"], "Manizales")
        self.assertEqual(caldas["tipo_geografia"], "Departamental")

    def test_resumen_usa_solo_ultima_semana(self) -> None:
        resultado = preparar(self._historico())

        resumen = crear_resumen_visual(resultado)

        self.assertEqual(len(resumen), 1)
        self.assertEqual(resumen.iloc[0]["semana_fin"], date(2026, 2, 1))

    def test_rechaza_variable_sin_catalogo(self) -> None:
        historico = self._historico()
        historico.loc[0, "variable"] = "variable_desconocida"
        with self.assertRaisesRegex(ValueError, "sin catálogo"):
            preparar(historico)

    def test_estado_anomalia_es_neutral_y_configurable(self) -> None:
        self.assertEqual(_estado_anomalia(2.1), "Muy por encima de su historia")
        self.assertEqual(_estado_anomalia(-1.1), "Por debajo de su historia")
        self.assertEqual(_estado_anomalia(0.2), "Dentro de su rango histórico")
        self.assertEqual(_estado_anomalia(None), "Sin historial suficiente")

    def test_descarga_comercial_conserva_trazabilidad(self) -> None:
        resultado = preparar(self._historico())

        descarga = preparar_descarga_comercial(resultado)

        self.assertEqual(len(descarga), 5)
        self.assertIn("fecha_dato", descarga.columns)
        self.assertIn("fuente", descarga.columns)
        self.assertIn("unidad", descarga.columns)
        self.assertEqual(descarga.iloc[0]["indicador"], "Tasa de cambio USD/COP")

    def test_detecta_variable_historica_ausente_en_series(self) -> None:
        historico = {"produccion_nacional", "exportaciones_cafe"}

        self.assertTrue(
            faltan_variables_historicas(historico, {"produccion_nacional"})
        )
        self.assertFalse(faltan_variables_historicas(historico, historico))

    def test_incorpora_referencia_actual_sin_reemplazar_historico(self) -> None:
        historico = preparar(self._historico())
        actualizado = incorporar_referencia_comercial_actual(
            historico,
            {"fx_usd_local": (4300.0, pd.Timestamp("2026-02-05"))},
        )
        actual = actualizado[
            actualizado["variable"].eq("fx_usd_local")
        ].sort_values("fecha_dato").iloc[-1]

        self.assertEqual(len(actualizado), len(historico) + 1)
        self.assertEqual(actual["valor"], 4300.0)
        self.assertEqual(actual["fecha_dato"], pd.Timestamp("2026-02-05"))
        self.assertEqual(actual["fuente"], "FNC")

    def test_eje_mensual_limita_etiquetas_sin_forzar_cada_mes(self) -> None:
        fechas = pd.Series(pd.date_range("2023-01-01", periods=41, freq="MS"))
        configuracion = configuracion_eje_mensual(fechas)

        self.assertEqual(configuracion["tickmode"], "array")
        self.assertEqual(len(configuracion["tickvals"]), 12)
        self.assertEqual(configuracion["tickvals"][0], fechas.iloc[0])
        self.assertEqual(configuracion["tickvals"][-1], fechas.iloc[-1])
        self.assertEqual(configuracion["tickangle"], 0)
        self.assertNotIn("dtick", configuracion)
        self.assertNotIn("nticks", configuracion)
        self.assertNotIn("ticklabelmode", configuracion)

    def test_eje_mensual_rechaza_un_maximo_inutilizable(self) -> None:
        with self.assertRaisesRegex(ValueError, "al menos 2"):
            configuracion_eje_mensual(pd.Series(dtype="datetime64[ns]"), 1)

    def test_eje_mensual_usa_una_etiqueta_por_barra_en_periodos_cortos(self) -> None:
        fechas = pd.Series(pd.date_range("2025-12-01", periods=6, freq="MS"))

        configuracion = configuracion_eje_mensual(fechas)

        self.assertEqual(list(configuracion["tickvals"]), list(fechas))

    def test_periodo_predefinido_conserva_ultimos_meses_publicados(self) -> None:
        filas = []
        for fecha in pd.date_range("2025-12-01", "2026-05-01", freq="MS"):
            for variable in ["produccion_nacional", "exportaciones_cafe"]:
                filas.append(
                    {
                        "semana_fin": fecha,
                        "fecha_dato": fecha,
                        "variable": variable,
                        "valor": 1.0,
                    }
                )
        filas.extend(
            {
                "semana_fin": fecha,
                "fecha_dato": fecha,
                "variable": "fx_usd_local",
                "valor": 1.0,
            }
            for fecha in pd.date_range("2026-01-04", "2026-06-28", freq="W-SUN")
        )
        tabla = pd.DataFrame(filas)

        tres_meses = filtrar_periodo_visualizacion(tabla, 13)
        seis_meses = filtrar_periodo_visualizacion(tabla, 26)

        for variable in ["produccion_nacional", "exportaciones_cafe"]:
            self.assertEqual(len(tres_meses[tres_meses["variable"].eq(variable)]), 3)
            self.assertEqual(len(seis_meses[seis_meses["variable"].eq(variable)]), 6)

    def test_periodo_predefinido_mantiene_corte_semanal(self) -> None:
        fechas = pd.date_range("2026-01-04", "2026-06-28", freq="W-SUN")
        tabla = pd.DataFrame(
            {
                "semana_fin": fechas,
                "fecha_dato": fechas,
                "variable": "fx_usd_local",
                "valor": 1.0,
            }
        )

        resultado = filtrar_periodo_visualizacion(tabla, 13)

        self.assertEqual(len(resultado), 13)
        self.assertEqual(resultado["semana_fin"].max(), pd.Timestamp("2026-06-28"))


if __name__ == "__main__":
    unittest.main()
