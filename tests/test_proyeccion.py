from datetime import date
import unittest

import pandas as pd

from procesar.proyeccion import (
    calcular_escenario,
    crear_matriz_sensibilidad,
    obtener_bases,
    proyectar_precio_fnc,
)


class ProyeccionTests(unittest.TestCase):
    def test_precio_base_se_conserva_si_no_cambian_supuestos(self) -> None:
        resultado = proyectar_precio_fnc(2_000_000, 4_000, 250, 4_000, 250)
        self.assertEqual(resultado, 2_000_000)

    def test_precio_responde_proporcionalmente_a_dolar_y_bolsa(self) -> None:
        resultado = proyectar_precio_fnc(2_000_000, 4_000, 250, 4_400, 275)
        self.assertAlmostEqual(resultado, 2_420_000)

    def test_precio_fnc_base_es_piso_ante_mercado_a_la_baja(self) -> None:
        # Coffee C y USD/COP por debajo de la base no proyectan bajo el precio FNC.
        resultado = proyectar_precio_fnc(2_000_000, 4_000, 250, 3_600, 240)
        self.assertEqual(resultado, 2_000_000)

    def test_factor_peor_que_referencia_si_puede_bajar_del_piso(self) -> None:
        # Un peor rendimiento sí reduce lo que recibe el productor.
        resultado = proyectar_precio_fnc(
            2_000_000, 4_000, 250, 4_000, 250, 100, 94
        )
        self.assertAlmostEqual(resultado, 2_000_000 * 94 / 100)

    def test_calcula_margen_por_carga_y_total(self) -> None:
        resultado = calcular_escenario(
            2_000_000,
            4_000,
            250,
            4_000,
            250,
            1_600_000,
            10,
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

    def test_matriz_contiene_todas_las_combinaciones(self) -> None:
        matriz = crear_matriz_sensibilidad(
            2_000_000,
            4_000,
            250,
            [3_800, 4_000],
            [240, 250, 260],
        )
        self.assertEqual(len(matriz), 6)
        self.assertEqual(matriz["precio_fnc_proyectado"].max(), 2_080_000)


if __name__ == "__main__":
    unittest.main()
