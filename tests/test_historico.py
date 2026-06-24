from datetime import date, timedelta
import unittest

import pandas as pd

from procesar.historico import _combinar_historico, agregar_semanal


COLUMNAS_DIARIAS = ["fecha", "geografia", "variable", "valor", "unidad", "fuente"]


class AgregacionHistoricaTests(unittest.TestCase):
    def _datos_semana(self) -> pd.DataFrame:
        inicio = date(2026, 1, 5)
        filas = [
            [inicio, "COLOMBIA", "fx_usd_local", 4000.0, "COP/USD", "yfinance"],
            [
                inicio + timedelta(days=4),
                "COLOMBIA",
                "fx_usd_local",
                4100.0,
                "COP/USD",
                "yfinance",
            ],
        ]
        for desplazamiento in range(7):
            fecha = inicio + timedelta(days=desplazamiento)
            filas.extend(
                [
                    [fecha, "Caldas", "precipitacion", 1.0, "mm", "open-meteo"],
                    [fecha, "Caldas", "temp_min", 10.0, "°C", "open-meteo"],
                    [fecha, "Caldas", "temp_max", 20.0, "°C", "open-meteo"],
                ]
            )
        return pd.DataFrame(filas, columns=COLUMNAS_DIARIAS)

    def test_usa_ultimo_cierre_y_agrega_siete_dias_clima(self) -> None:
        resultado = agregar_semanal(self._datos_semana(), date(2026, 1, 11))

        fx = resultado[resultado["variable"] == "fx_usd_local"].iloc[0]
        lluvia = resultado[
            resultado["variable"] == "precipitacion_semanal"
        ].iloc[0]
        promedio = resultado[
            resultado["variable"] == "temp_promedio_semanal"
        ].iloc[0]

        self.assertEqual(fx["valor"], 4100.0)
        self.assertEqual(lluvia["valor"], 7.0)
        self.assertEqual(lluvia["dias_observados"], 7)
        self.assertEqual(promedio["valor"], 15.0)

    def test_excluye_semana_final_aun_abierta(self) -> None:
        datos = self._datos_semana()
        extra = pd.DataFrame(
            [
                [
                    date(2026, 1, 12),
                    "COLOMBIA",
                    "fx_usd_local",
                    4200,
                    "COP/USD",
                    "yfinance",
                ]
            ],
            columns=COLUMNAS_DIARIAS,
        )
        resultado = agregar_semanal(
            pd.concat([datos, extra], ignore_index=True),
            date(2026, 1, 13),
        )

        self.assertEqual(set(resultado["semana_fin"]), {date(2026, 1, 11)})

    def test_produccion_mensual_no_se_rellena_semanalmente(self) -> None:
        tabla = pd.DataFrame(
            [
                [
                    date(2026, 1, 1),
                    "COLOMBIA",
                    "produccion_nacional",
                    900.0,
                    "miles_sacos_60kg",
                    "FNC",
                ],
                [
                    date(2026, 2, 1),
                    "COLOMBIA",
                    "produccion_nacional",
                    1000.0,
                    "miles_sacos_60kg",
                    "FNC",
                ],
            ],
            columns=COLUMNAS_DIARIAS,
        )

        resultado = agregar_semanal(tabla, date(2026, 2, 28))

        self.assertEqual(len(resultado), 2)
        self.assertEqual(resultado["fecha_dato"].nunique(), 2)


class PersistenciaHistoricaTests(unittest.TestCase):
    def test_combinar_es_idempotente_y_prefiere_dato_nuevo(self) -> None:
        columnas = ["fecha", "geografia", "variable", "valor", "unidad", "fuente"]
        existente = pd.DataFrame(
            [["2026-01-01", "GLOBAL", "cafe", 100.0, "u", "test"]],
            columns=columnas,
        )
        nuevos = pd.DataFrame(
            [[date(2026, 1, 1), "GLOBAL", "cafe", 110.0, "u", "test"]],
            columns=columnas,
        )

        resultado = _combinar_historico(
            existente,
            nuevos,
            ["fecha", "geografia", "variable", "fuente"],
        )

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado.iloc[0]["valor"], 110.0)
        self.assertEqual(resultado.iloc[0]["fecha"], "2026-01-01")


if __name__ == "__main__":
    unittest.main()
