from datetime import date, timedelta
import unittest

import pandas as pd

from procesar.calidad import COLUMNAS_HISTORICO_SEMANAL
from procesar.visualizacion import (
    _estado_anomalia,
    crear_resumen_visual,
    faltan_variables_historicas,
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


if __name__ == "__main__":
    unittest.main()
