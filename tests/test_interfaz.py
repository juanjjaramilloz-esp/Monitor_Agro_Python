import unittest

import pandas as pd

from interfaz.analisis import (
    comparar_produccion_exportaciones,
    resumen_fuentes_comerciales,
    variaciones_mercado,
)
from interfaz.formato import numero, unidad_legible


class FormatoInterfazTests(unittest.TestCase):
    def test_formatea_numeros_por_idioma(self) -> None:
        self.assertEqual(numero(1234.5, 1, "es"), "1.234,5")
        self.assertEqual(numero(1234.5, 1, "en"), "1,234.5")

    def test_traduce_unidades_tecnicas_sin_alterar_desconocidas(self) -> None:
        self.assertEqual(unidad_legible("COP/carga_125kg"), "COP/carga")
        self.assertEqual(unidad_legible("kg"), "kg")


class AnalisisInterfazTests(unittest.TestCase):
    def test_compara_solo_meses_con_ambos_flujos(self) -> None:
        tabla = pd.DataFrame(
            [
                {"fecha_dato": "2026-05-01", "variable": "produccion_nacional", "valor": 1000},
                {"fecha_dato": "2026-05-01", "variable": "exportaciones_cafe", "valor": 900},
                {"fecha_dato": "2026-06-01", "variable": "produccion_nacional", "valor": 1100},
            ]
        )

        resultado = comparar_produccion_exportaciones(tabla)

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado.iloc[0]["diferencia"], 100)

    def test_calcula_variaciones_sin_depender_de_streamlit(self) -> None:
        fechas = pd.date_range("2025-06-29", periods=53, freq="W-SUN")
        filas = []
        for variable, etiqueta in (
            ("precio_interno_referencia", "Precio FNC"),
            ("precio_cafe_arabica", "Coffee C"),
            ("fx_usd_local", "USD/COP"),
        ):
            filas.extend(
                {
                    "semana_fin": fecha,
                    "variable": variable,
                    "valor": 100 + indice,
                    "etiqueta_variable": etiqueta,
                }
                for indice, fecha in enumerate(fechas)
            )

        resultado = variaciones_mercado(pd.DataFrame(filas))

        self.assertEqual(len(resultado), 3)
        self.assertTrue(resultado["Anual (52 sem.)"].notna().all())

    def test_resumen_normaliza_nombre_de_fuente_fnc(self) -> None:
        tabla = pd.DataFrame(
            [
                {
                    "categoria": "Mercado",
                    "variable": "precio_interno_referencia",
                    "semana_fin": "2026-07-05",
                    "fecha_dato": "2026-07-03",
                    "etiqueta_variable": "Precio interno de referencia FNC",
                    "unidad": "COP/carga_125kg",
                    "fuente": "FNC",
                    "cadencia": "Semanal",
                }
            ]
        )

        resultado = resumen_fuentes_comerciales(tabla)

        self.assertEqual(
            resultado.iloc[0]["Fuente"],
            "Federación Nacional de Cafeteros (FNC)",
        )
        self.assertEqual(resultado.iloc[0]["Unidad"], "COP/carga")


if __name__ == "__main__":
    unittest.main()
