from datetime import date
import unittest

import pandas as pd

from procesar.proyeccion import (
    ModeloPrecioFNC,
    calibrar_modelo,
    calcular_escenario,
    crear_matriz_sensibilidad,
    estimar_precio_fnc,
    obtener_bases,
    obtener_bases_calibracion,
)


class ProyeccionTests(unittest.TestCase):
    def _modelo(self, coeficiente: float = 2.0) -> ModeloPrecioFNC:
        return ModeloPrecioFNC(
            coeficiente=coeficiente,
            observaciones_calibracion=5,
            fecha_inicio_calibracion=pd.Timestamp("2026-01-01"),
            fecha_fin_calibracion=pd.Timestamp("2026-01-05"),
            error_absoluto_medio=25_000,
            error_porcentual_medio=1.2,
            observaciones_validacion=100,
        )

    def test_estima_precio_desde_trm_y_coffee_c(self) -> None:
        resultado = estimar_precio_fnc(self._modelo(), 4_000, 250)
        self.assertEqual(resultado, 2_000_000)

    def test_precio_responde_proporcionalmente_a_dolar_y_bolsa(self) -> None:
        resultado = estimar_precio_fnc(self._modelo(), 4_400, 275)
        self.assertAlmostEqual(resultado, 2_420_000)

    def test_no_aplica_piso_del_precio_fnc_observado(self) -> None:
        resultado = calcular_escenario(
            self._modelo(),
            3_600,
            240,
            1_600_000,
            1,
            precio_fnc_observado=2_000_000,
        )
        self.assertEqual(resultado.precio_fnc_estimado, 1_728_000)
        self.assertLess(resultado.diferencia_fnc_observado_pct, 0)

    def test_factor_peor_que_referencia_reduce_el_estimado(self) -> None:
        # Un peor rendimiento sí reduce lo que recibe el productor.
        resultado = estimar_precio_fnc(self._modelo(), 4_000, 250, 100, 94)
        self.assertAlmostEqual(resultado, 2_000_000 * 94 / 100)

    def test_calcula_margen_por_carga_y_total(self) -> None:
        resultado = calcular_escenario(
            self._modelo(),
            4_000,
            250,
            1_600_000,
            10,
            precio_fnc_observado=2_000_000,
        )
        self.assertEqual(resultado.margen_por_carga, 400_000)
        self.assertEqual(resultado.margen_total, 4_000_000)
        self.assertEqual(resultado.margen_sobre_ingreso_pct, 20)
        self.assertEqual(resultado.retorno_sobre_costo_pct, 25)

    def test_obtiene_ultimas_bases_por_fecha_real(self) -> None:
        tabla = pd.DataFrame(
            [
                [date(2026, 1, 1), "precio_interno_referencia", 2_000_000],
                [date(2026, 2, 1), "precio_interno_referencia", 2_100_000],
                [date(2026, 2, 2), "fx_usd_local", 4_000],
                [date(2026, 2, 3), "precio_cafe_arabica", 250],
            ],
            columns=["fecha_dato", "variable", "valor"],
        )
        bases = obtener_bases(tabla)
        self.assertEqual(bases.precio_fnc, 2_100_000)
        self.assertEqual(bases.fecha_precio_fnc.date(), date(2026, 2, 1))

    def test_obtiene_bases_de_la_referencia_oficial(self) -> None:
        tabla = pd.DataFrame(
            [
                {
                    "fecha": "2026-06-25",
                    "precio_fnc": 2_160_000,
                    "tasa_cambio": 3_435.99,
                    "precio_ny": 276.40,
                }
            ]
        )

        bases = obtener_bases_calibracion(tabla)

        self.assertIsNotNone(bases)
        self.assertEqual(bases.precio_fnc, 2_160_000)
        self.assertEqual(bases.tasa_cambio, 3_435.99)
        self.assertEqual(bases.precio_ny, 276.40)

    def test_calibra_con_fechas_diarias_comparables(self) -> None:
        filas = []
        for indice, fecha in enumerate(pd.date_range("2026-01-01", periods=8)):
            tasa = 4_000 + indice * 10
            cafe = 250 + indice
            coeficiente = 1.9 + indice * 0.01
            filas.extend(
                [
                    [fecha, "fx_usd_local", tasa],
                    [fecha, "precio_cafe_arabica", cafe],
                    [fecha, "precio_interno_referencia", tasa * cafe * coeficiente],
                ]
            )
        modelo = calibrar_modelo(
            pd.DataFrame(filas, columns=["fecha", "variable", "valor"])
        )
        self.assertEqual(modelo.observaciones_calibracion, 5)
        self.assertGreater(modelo.coeficiente, 1.94)
        self.assertLess(modelo.coeficiente, 1.97)
        self.assertEqual(modelo.observaciones_validacion, 3)

    def test_calibracion_oficial_reemplaza_coeficiente_de_respaldo(self) -> None:
        filas = []
        for indice, fecha in enumerate(pd.date_range("2026-01-01", periods=8)):
            tasa = 4_000 + indice * 10
            cafe = 250 + indice
            filas.extend(
                [
                    [fecha, "fx_usd_local", tasa],
                    [fecha, "precio_cafe_arabica", cafe],
                    [fecha, "precio_interno_referencia", tasa * cafe * 2.0],
                ]
            )
        historico = pd.DataFrame(filas, columns=["fecha", "variable", "valor"])
        oficial = pd.DataFrame(
            [
                {
                    "fecha": "2026-02-01",
                    "coeficiente_implicito": 2.25,
                }
            ]
        )

        modelo = calibrar_modelo(historico, oficial)

        self.assertEqual(modelo.coeficiente, 2.25)
        self.assertTrue(modelo.calibracion_oficial)
        self.assertEqual(modelo.fecha_fin_calibracion.date(), date(2026, 2, 1))

    def test_matriz_contiene_todas_las_combinaciones(self) -> None:
        matriz = crear_matriz_sensibilidad(
            self._modelo(),
            [3_800, 4_000],
            [240, 250, 260],
        )
        self.assertEqual(len(matriz), 6)
        self.assertEqual(matriz["precio_fnc_estimado"].max(), 2_080_000)


if __name__ == "__main__":
    unittest.main()
