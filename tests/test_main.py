import unittest

import pandas as pd

from main import COLS_NOTICIAS, COLS_NUMERICAS, _validar


class ValidacionFuentesTests(unittest.TestCase):
    def test_fuente_vacia_no_se_reporta_como_ok(self) -> None:
        tabla = pd.DataFrame(columns=list(COLS_NUMERICAS))
        self.assertEqual(_validar("prueba", tabla, COLS_NUMERICAS), "VACIO")

    def test_rechaza_valor_no_numerico(self) -> None:
        tabla = pd.DataFrame(
            [["2026-06-22", "COLOMBIA", "fx", "no-numero", "u", "test"]],
            columns=["fecha", "geografia", "variable", "valor", "unidad", "fuente"],
        )
        with self.assertRaisesRegex(ValueError, "numéricos"):
            _validar("prueba", tabla, COLS_NUMERICAS)

    def test_noticias_usa_url_para_detectar_duplicados(self) -> None:
        columnas = [
            "fecha",
            "geografia",
            "titulo",
            "url",
            "fuente",
            "idioma",
            "tono",
            "categoria",
        ]
        fila = [
            "2026-06-22",
            "COLOMBIA",
            "Título",
            "https://ejemplo.co",
            "test",
            "es",
            0.0,
            "clima",
        ]
        tabla = pd.DataFrame([fila, fila], columns=columnas)
        with self.assertRaisesRegex(ValueError, "duplicadas"):
            _validar("noticias", tabla, COLS_NOTICIAS)


if __name__ == "__main__":
    unittest.main()
