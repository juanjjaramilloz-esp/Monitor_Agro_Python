from datetime import date
import unittest
from unittest.mock import Mock, patch

import pandas as pd

from fuentes import cafe, clima, fx, precio_interno, referencia_mercado_fnc
from procesar.calibracion_fnc import preparar


class FuentesYahooHistoricasTests(unittest.TestCase):
    def setUp(self) -> None:
        self.desde = date(2026, 1, 1)
        self.hasta = date(2026, 1, 2)
        self.cierres = pd.DataFrame(
            {"Close": [100.0, 110.0]},
            index=pd.to_datetime(["2026-01-01", "2026-01-02"]),
        )

    @patch("fuentes.fx.yf.download")
    def test_fx_historico_conserva_todos_los_cierres(self, descargar: Mock) -> None:
        descargar.return_value = self.cierres

        resultado = fx.obtener(self.desde, self.hasta)

        self.assertEqual(len(resultado), 2)
        self.assertEqual(resultado["valor"].tolist(), [100.0, 110.0])
        self.assertEqual(descargar.call_args.kwargs["end"], "2026-01-03")

    @patch("fuentes.cafe.yf.download")
    def test_cafe_actual_conserva_solo_ultimo_cierre(self, descargar: Mock) -> None:
        descargar.return_value = self.cierres

        resultado = cafe.obtener()

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado.iloc[0]["valor"], 110.0)
        self.assertEqual(descargar.call_args.kwargs["period"], "5d")

    def test_rango_incompleto_es_error_de_uso(self) -> None:
        with self.assertRaises(ValueError):
            fx.obtener(desde=self.desde)
        with self.assertRaises(ValueError):
            cafe.obtener(hasta=self.hasta)


class ClimaHistoricoTests(unittest.TestCase):
    @patch("fuentes.clima.requests.get")
    @patch(
        "fuentes.clima.REGIONES_CAFE",
        [{"departamento": "Caldas", "lat": 5.07, "lon": -75.52}],
    )
    def test_clima_historico_usa_api_archive(self, consultar: Mock) -> None:
        respuesta = Mock()
        respuesta.raise_for_status.return_value = None
        respuesta.json.return_value = {
            "daily": {
                "time": ["2026-01-01"],
                "temperature_2m_min": [10.0],
                "temperature_2m_max": [20.0],
                "precipitation_sum": [5.0],
            }
        }
        consultar.return_value = respuesta

        resultado = clima.obtener(date(2026, 1, 1), date(2026, 1, 1))

        self.assertEqual(len(resultado), 3)
        url = consultar.call_args.args[0]
        parametros = consultar.call_args.kwargs["params"]
        self.assertIn("archive-api", url)
        self.assertEqual(parametros["start_date"], "2026-01-01")
        self.assertEqual(parametros["end_date"], "2026-01-01")
        self.assertNotIn("forecast_days", parametros)


class PrecioInternoHistoricoTests(unittest.TestCase):
    def test_normaliza_y_filtra_rango_diario_fnc(self) -> None:
        tabla = pd.DataFrame(
            {
                "Fecha": [
                    "2025-12-31",
                    "2026-01-01",
                    "2026-01-02",
                    "invalida",
                ],
                "Precio Interno ($/125 Kg)": [1900000, 2000000, 2100000, None],
            }
        )

        resultado = precio_interno._normalizar_historico(
            tabla,
            date(2026, 1, 1),
            date(2026, 1, 2),
        )

        self.assertEqual(len(resultado), 2)
        self.assertEqual(resultado["valor"].tolist(), [2000000.0, 2100000.0])

    def test_encuentra_excel_historico_en_pagina_fnc(self) -> None:
        sopa = precio_interno.BeautifulSoup(
            '<a href="/wp-content/uploads/Precios-area-y-produccion-de-cafe.xlsx">Excel</a>',
            "html.parser",
        )

        url = precio_interno._buscar_url_historico(sopa)

        self.assertEqual(
            url,
            "https://federaciondecafeteros.org/wp-content/uploads/"
            "Precios-area-y-produccion-de-cafe.xlsx",
        )


class ReferenciaMercadoFncTests(unittest.TestCase):
    def test_parsea_trio_oficial_con_formato_colombiano(self) -> None:
        texto = """
        Precio interno de referencia: $2.160.000 Fecha: 2026-06-25
        Bolsa de NY: $276,40 Fecha: 2026-06-25
        Tasa de cambio: 3.435,99 Fecha: 2026-06-25
        """
        resultado = referencia_mercado_fnc._parsear(texto)

        self.assertEqual(len(resultado), 3)
        valores = resultado.set_index("variable")["valor"]
        self.assertEqual(valores["precio_interno_referencia"], 2_160_000)
        self.assertEqual(valores["precio_cafe_fnc_calculo"], 276.40)
        self.assertEqual(valores["fx_fnc_calculo"], 3_435.99)

    def test_prepara_coeficiente_implicito(self) -> None:
        tabla = referencia_mercado_fnc._parsear(
            "Precio interno de referencia: $2.160.000 Fecha: 2026-06-25 "
            "Bolsa de NY: $276,40 Tasa de cambio: 3.435,99"
        )
        calibracion = preparar(tabla)

        esperado = 2_160_000 / (3_435.99 * 276.40)
        self.assertAlmostEqual(calibracion.iloc[0]["coeficiente_implicito"], esperado)


if __name__ == "__main__":
    unittest.main()
