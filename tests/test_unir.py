from datetime import date
from pathlib import Path
import unittest
from unittest.mock import patch

import pandas as pd

from procesar.calidad import COLUMNAS_SNAPSHOT
from procesar.unir import _agregar_clima, _guardar_snapshot, unir


class AgregacionClimaTests(unittest.TestCase):
    def test_promedio_empareja_temperaturas_por_fecha(self) -> None:
        filas = [
            [date(2026, 1, 1), "Caldas", "temp_min", 10.0, "°C", "open-meteo"],
            [date(2026, 1, 2), "Caldas", "temp_min", 20.0, "°C", "open-meteo"],
            [date(2026, 1, 2), "Caldas", "temp_max", 30.0, "°C", "open-meteo"],
        ]
        clima = pd.DataFrame(
            filas,
            columns=["fecha", "geografia", "variable", "valor", "unidad", "fuente"],
        )

        resultado = _agregar_clima(clima, date(2026, 1, 3))
        promedio = resultado.loc[
            resultado["variable"] == "temp_promedio_semanal", "valor"
        ].iloc[0]

        self.assertEqual(promedio, 25.0)


class GuardadoSnapshotTests(unittest.TestCase):
    def test_no_sobrescribe_sin_permiso_explicito(self) -> None:
        fecha = date(2026, 1, 3)
        tabla = pd.DataFrame(
            [[fecha, fecha, "GLOBAL", "prueba", 1.0, "u", "test"]],
            columns=COLUMNAS_SNAPSHOT,
        )
        with (
            patch("procesar.unir.DIR_SNAPSHOTS", Path("snapshots-prueba")),
            patch("pathlib.Path.mkdir"),
            patch("pathlib.Path.exists", side_effect=[False, True, True]),
            patch.object(pd.DataFrame, "to_csv") as guardar_csv,
        ):
            _guardar_snapshot(tabla, fecha)
            with self.assertRaises(FileExistsError):
                _guardar_snapshot(tabla, fecha)
            _guardar_snapshot(tabla, fecha, sobrescribir=True)
        self.assertEqual(guardar_csv.call_count, 2)

    def test_union_parcial_reporta_calidad_y_conserva_datos(self) -> None:
        fecha = date(2026, 1, 3)
        columnas = ["fecha", "geografia", "variable", "valor", "unidad", "fuente"]
        fx = pd.DataFrame(
            [[fecha, "COLOMBIA", "fx_usd_local", 4000.0, "COP/USD", "yfinance"]],
            columns=columnas,
        )
        vacio = pd.DataFrame(columns=columnas)

        with (
            patch("procesar.unir.fx.obtener", return_value=fx),
            patch("procesar.unir.cafe.obtener", return_value=vacio),
            patch("procesar.unir.precio_interno.obtener", return_value=vacio),
            patch("procesar.unir.produccion.obtener", return_value=vacio),
            patch("procesar.unir.exportaciones.obtener", return_value=vacio),
            patch("procesar.unir.clima.obtener", return_value=vacio),
            patch("procesar.unir._guardar_snapshot") as guardar,
        ):
            tabla = unir(fecha_snapshot=fecha)

        self.assertEqual(len(tabla), 1)
        guardar.assert_called_once()


if __name__ == "__main__":
    unittest.main()
