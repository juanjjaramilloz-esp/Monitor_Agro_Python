from datetime import date, timedelta
import unittest

import pandas as pd

from reporte.generar import generar


class BriefEjecutivoTests(unittest.TestCase):
    def _datos(self) -> pd.DataFrame:
        filas = []
        inicio = date(2025, 1, 5)
        especificaciones = [
            ("precio_interno_referencia", "COP/carga_125kg", "Semanal", "FNC"),
            ("precio_cafe_arabica", "USc/lb", "Semanal", "yfinance"),
            ("fx_usd_local", "COP/USD", "Semanal", "yfinance"),
        ]
        for variable, unidad, cadencia, fuente in especificaciones:
            for indice in range(53):
                semana = inicio + timedelta(weeks=indice)
                filas.append(
                    {
                        "semana_fin": semana,
                        "fecha_dato": semana,
                        "variable": variable,
                        "valor": 100.0 + indice,
                        "unidad": unidad,
                        "cadencia": cadencia,
                        "fuente": fuente,
                        "cambio_1s_pct": 1.0,
                        "cambio_4s_pct": 4.0,
                        "cambio_1m_pct": pd.NA,
                        "cambio_12m_pct": pd.NA,
                    }
                )
        for indice in range(13):
            fecha = pd.Timestamp("2025-01-01") + pd.DateOffset(months=indice)
            filas.append(
                {
                    "semana_fin": fecha + pd.offsets.Week(weekday=6),
                    "fecha_dato": fecha,
                    "variable": "produccion_nacional",
                    "valor": 800.0 + indice * 10,
                    "unidad": "miles_sacos_60kg",
                    "cadencia": "Mensual",
                    "fuente": "FNC",
                    "cambio_1s_pct": pd.NA,
                    "cambio_4s_pct": pd.NA,
                    "cambio_1m_pct": 1.2,
                    "cambio_12m_pct": 15.0 if indice == 12 else pd.NA,
                }
            )
        return pd.DataFrame(filas)

    def test_brief_incluye_trazabilidad_y_cadencias(self) -> None:
        texto = generar(
            self._datos(),
            date(2025, 1, 1),
            date(2026, 1, 31),
            date(2026, 6, 24),
        )

        self.assertIn("Producción nacional de café", texto)
        self.assertIn("Cadencia: Mensual", texto)
        self.assertIn("Variación interanual", texto)
        self.assertIn("no implican causalidad", texto)
        self.assertIn("Fecha de generación:** 24/06/2026", texto)

    def test_brief_declara_serie_sin_dato_en_periodo(self) -> None:
        texto = generar(
            self._datos(),
            date(2025, 1, 6),
            date(2025, 1, 12),
            date(2026, 6, 24),
        )

        self.assertIn("Sin dato publicado dentro del periodo seleccionado", texto)


if __name__ == "__main__":
    unittest.main()
