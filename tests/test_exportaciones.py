from datetime import date
from io import BytesIO
import unittest
from unittest.mock import Mock, patch

import pandas as pd

from fuentes.exportaciones import COLUMNAS, _normalizar, obtener


class ExportacionesFncTests(unittest.TestCase):
    def test_normaliza_volumen_mensual(self) -> None:
        tabla = pd.DataFrame(
            {
                "MES": ["2026-01-01", "2026-02-01"],
                "Total Exportaciones": [1010.0, 980.0],
            }
        )

        resultado = _normalizar(tabla, date(2026, 1, 1), date(2026, 2, 28))

        self.assertEqual(list(resultado.columns), COLUMNAS)
        self.assertEqual(resultado["valor"].tolist(), [1010.0, 980.0])
        self.assertEqual(set(resultado["variable"]), {"exportaciones_cafe"})
        self.assertEqual(set(resultado["unidad"]), {"miles_sacos_60kg"})

    @patch("fuentes.exportaciones.requests.get")
    def test_obtener_descubre_excel_y_devuelve_ultimo_mes(self, descargar: Mock) -> None:
        archivo = BytesIO()
        tabla = pd.DataFrame(
            {
                "MES": [date(2026, 1, 1), date(2026, 2, 1)],
                "Total Exportaciones": [1010.0, 980.0],
            }
        )
        with pd.ExcelWriter(archivo, engine="openpyxl") as escritor:
            tabla.to_excel(
                escritor,
                sheet_name="1. Total_Volumen",
                startrow=6,
                index=False,
            )

        pagina = Mock()
        pagina.text = '<a href="/Exportaciones-Mayo-2026.xlsx">Descargar</a>'
        pagina.raise_for_status.return_value = None
        excel = Mock()
        excel.content = archivo.getvalue()
        excel.raise_for_status.return_value = None
        descargar.side_effect = [pagina, excel]

        resultado = obtener()

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado.iloc[0]["fecha"], date(2026, 2, 1))
        self.assertEqual(resultado.iloc[0]["valor"], 980.0)


if __name__ == "__main__":
    unittest.main()
