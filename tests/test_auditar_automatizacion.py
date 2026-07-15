import unittest
from datetime import date

import pandas as pd

from procesar.auditar_automatizacion import evaluar_frescura


class AuditoriaAutomatizacionTests(unittest.TestCase):
    HOY = date(2026, 7, 15)

    def _diario(self, fecha: str) -> pd.DataFrame:
        variables = [
            "fx_usd_local",
            "precio_cafe_arabica",
            "precio_interno_referencia",
            "precipitacion",
        ]
        return pd.DataFrame({"fecha": [fecha] * len(variables), "variable": variables})

    def _semanal(self, fecha: str) -> pd.DataFrame:
        variables = [
            "fx_usd_local",
            "precio_cafe_arabica",
            "precio_interno_referencia",
            "precipitacion_semanal",
        ]
        return pd.DataFrame(
            {"semana_fin": [fecha] * len(variables), "variable": variables}
        )

    def test_acepta_retrasos_normales_de_publicacion(self) -> None:
        fechas, errores = evaluar_frescura(
            self._diario("2026-07-10"),
            self._semanal("2026-07-05"),
            pd.DataFrame({"fecha": ["2026-07-11"]}),
            date(2026, 7, 13),
            self.HOY,
        )

        self.assertFalse(errores)
        self.assertEqual(fechas["calibracion_fnc"], date(2026, 7, 11))

    def test_detecta_artefactos_congelados(self) -> None:
        _, errores = evaluar_frescura(
            self._diario("2026-06-01"),
            self._semanal("2026-06-01"),
            pd.DataFrame({"fecha": ["2026-06-01"]}),
            date(2026, 6, 1),
            self.HOY,
        )

        self.assertEqual(len(errores), 10)
        self.assertTrue(any("comentario_ia" in error for error in errores))

    def test_detecta_series_criticas_ausentes(self) -> None:
        _, errores = evaluar_frescura(
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame(),
            None,
            self.HOY,
        )

        self.assertEqual(len(errores), 10)
        self.assertTrue(all("fecha válida" in error for error in errores))

    def test_secret_ia_ausente_no_bloquea_datos_frescos(self) -> None:
        fechas, errores = evaluar_frescura(
            self._diario("2026-07-10"),
            self._semanal("2026-07-05"),
            pd.DataFrame({"fecha": ["2026-07-11"]}),
            None,
            self.HOY,
            auditar_comentario=False,
        )

        self.assertFalse(errores)
        self.assertIn("comentario_ia (sin secret configurado)", fechas)


if __name__ == "__main__":
    unittest.main()
