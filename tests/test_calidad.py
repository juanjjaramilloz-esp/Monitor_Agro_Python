from datetime import date, timedelta
import unittest

import pandas as pd

from config import DEPARTAMENTOS
from procesar.calidad import (
    COLUMNAS_SNAPSHOT,
    VARIABLES_CLIMA,
    generar_reporte_calidad,
    validar_snapshot,
)


class CalidadSnapshotTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fecha = date(2026, 6, 22)
        filas = [
            self._fila("COLOMBIA", "fx_usd_local", "yfinance"),
            self._fila("GLOBAL", "precio_cafe_arabica", "yfinance"),
            self._fila("COLOMBIA", "precio_interno_referencia", "FNC"),
        ]
        for departamento in DEPARTAMENTOS:
            for variable in VARIABLES_CLIMA:
                filas.append(self._fila(departamento, variable, "open-meteo"))
        self.tabla = pd.DataFrame(filas, columns=COLUMNAS_SNAPSHOT)

    def _fila(self, geografia: str, variable: str, fuente: str) -> dict:
        return {
            "fecha_snapshot": self.fecha,
            "fecha_dato": self.fecha - timedelta(days=1),
            "geografia": geografia,
            "variable": variable,
            "valor": 1.0,
            "unidad": "unidad",
            "fuente": fuente,
        }

    def test_snapshot_completo_es_valido(self) -> None:
        validar_snapshot(self.tabla, self.fecha)
        reporte = generar_reporte_calidad(self.tabla, self.fecha)
        self.assertEqual(set(reporte["estado"]), {"OK"})

    def test_rechaza_dato_posterior_al_snapshot(self) -> None:
        tabla = self.tabla.copy()
        tabla.loc[0, "fecha_dato"] = self.fecha + timedelta(days=1)
        with self.assertRaisesRegex(ValueError, "posteriores"):
            validar_snapshot(tabla, self.fecha)
        reporte = generar_reporte_calidad(tabla, self.fecha).set_index("componente")
        self.assertEqual(reporte.loc["fx", "estado"], "FECHA_FUTURA")

    def test_rechaza_duplicados(self) -> None:
        tabla = pd.concat([self.tabla, self.tabla.iloc[[0]]], ignore_index=True)
        with self.assertRaisesRegex(ValueError, "duplicadas"):
            validar_snapshot(tabla, self.fecha)

    def test_reporte_marca_componente_vacio(self) -> None:
        tabla = self.tabla[self.tabla["variable"] != "fx_usd_local"]
        reporte = generar_reporte_calidad(tabla, self.fecha).set_index("componente")
        self.assertEqual(reporte.loc["fx", "estado"], "VACIO")


if __name__ == "__main__":
    unittest.main()
