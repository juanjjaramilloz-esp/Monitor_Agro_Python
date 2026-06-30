from datetime import date, timedelta
import unittest

import pandas as pd

from reporte.generar import generar
from reporte.pdf import _flujos_mensuales, generar_pdf_brief


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

    def test_pdf_separa_tres_paginas_utiles_e_incluye_ambos_flujos(self) -> None:
        datos = self._datos().copy()
        datos["categoria"] = datos["variable"].map(
            lambda variable: "Mercado" if variable.startswith(("precio_", "fx_")) else "Producción"
        )
        datos["indice_base_100"] = datos["valor"]
        exportaciones = datos[datos["variable"].eq("produccion_nacional")].copy()
        exportaciones["variable"] = "exportaciones_cafe"
        exportaciones["valor"] = exportaciones["valor"] - 50
        datos = pd.concat([datos, exportaciones], ignore_index=True)
        variaciones = pd.DataFrame(
            [
                {"Indicador": "Precio interno FNC", "Semanal": 1.0, "Mensual (4 sem.)": 2.0, "Anual (52 sem.)": 3.0},
                {"Indicador": "Coffee C", "Semanal": 1.0, "Mensual (4 sem.)": 2.0, "Anual (52 sem.)": 3.0},
                {"Indicador": "USD/COP", "Semanal": 1.0, "Mensual (4 sem.)": 2.0, "Anual (52 sem.)": 3.0},
            ]
        )
        cobertura = pd.DataFrame(
            [
                {
                    "Indicador": "Producción nacional",
                    "Último dato": "01/01/2026",
                    "Unidad": "miles de sacos de 60 kg",
                    "Fuente": "FNC",
                    "Alcance": "Colombia",
                    "Cadencia": "Mensual",
                }
            ]
        )

        contenido = generar_pdf_brief(
            inicio=date(2025, 1, 1),
            fin=date(2026, 1, 31),
            periodo=datos,
            variaciones=variaciones,
            cobertura=cobertura,
            fecha_generacion=date(2026, 6, 30),
        )

        self.assertTrue(contenido.startswith(b"%PDF"))
        self.assertEqual(
            contenido.count(b"/Type /Page") - contenido.count(b"/Type /Pages"),
            3,
        )
        flujos = _flujos_mensuales(datos)
        self.assertIn("diferencia", flujos.columns)
        self.assertEqual(
            flujos.iloc[-1]["diferencia"],
            flujos.iloc[-1]["produccion_nacional"]
            - flujos.iloc[-1]["exportaciones_cafe"],
        )


if __name__ == "__main__":
    unittest.main()
