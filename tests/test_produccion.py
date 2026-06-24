from datetime import date
from io import BytesIO
import unittest
from unittest.mock import Mock, patch

import pandas as pd

from fuentes.produccion import COLUMNAS, _normalizar, obtener


class ProduccionFncTests(unittest.TestCase):
    def test_normaliza_meses_sin_rellenar_fechas(self) -> None:
        tabla = pd.DataFrame(
            {"Mes": ["2026-01-01", "2026-03-01"], "Producción": [900.0, 1100.0]}
        )

        resultado = _normalizar(tabla, date(2026, 1, 1), date(2026, 3, 31))

        self.assertEqual(list(resultado.columns), COLUMNAS)
        self.assertEqual(len(resultado), 2)
        self.assertEqual(
            resultado["fecha"].tolist(),
            [date(2026, 1, 1), date(2026, 3, 1)],
        )
        self.assertEqual(set(resultado["unidad"]), {"miles_sacos_60kg"})

    @patch("fuentes.produccion.requests.get")
    def test_obtener_descubre_excel_y_devuelve_ultimo_mes(self, descargar: Mock) -> None:
        archivo = BytesIO()
        tabla = pd.DataFrame(
            {
                "Mes": [date(2026, 1, 1), date(2026, 2, 1)],
                "Producción": [900.0, 950.0],
            }
        )
        with pd.ExcelWriter(archivo, engine="openpyxl") as escritor:
            tabla.to_excel(
                escritor,
                sheet_name="8. Producción mensual",
                startrow=5,
                index=False,
            )

        pagina = Mock()
        pagina.text = (
            '<a href="https://fnc.test/Precios-area-y-produccion-de-cafe.xlsx">'
            "Descargar</a>"
        )
        pagina.raise_for_status.return_value = None
        excel = Mock()
        excel.content = archivo.getvalue()
        excel.raise_for_status.return_value = None
        descargar.side_effect = [pagina, excel]

        resultado = obtener()

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado.iloc[0]["fecha"], date(2026, 2, 1))
        self.assertEqual(resultado.iloc[0]["valor"], 950.0)


if __name__ == "__main__":
    unittest.main()
