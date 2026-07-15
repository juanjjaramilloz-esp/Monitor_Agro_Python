import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pandas as pd

from reporte import comentario_ia


def _historico_sintetico() -> pd.DataFrame:
    """Histórico semanal con 30 semanas de mercado y 14 meses mensuales."""
    filas = []
    inicio = date(2025, 6, 1)
    for variable, base in [
        ("precio_interno_referencia", 2_000_000.0),
        ("precio_cafe_arabica", 250.0),
        ("fx_usd_local", 4_000.0),
    ]:
        for indice in range(30):
            semana = inicio + timedelta(weeks=indice)
            filas.append(
                {
                    "semana_fin": semana.isoformat(),
                    "fecha_dato": semana.isoformat(),
                    "geografia": "COLOMBIA",
                    "variable": variable,
                    "valor": base * (1 + 0.01 * indice),
                    "unidad": "unidad",
                    "fuente": "prueba",
                }
            )
    for variable in ("produccion_nacional", "exportaciones_cafe"):
        for indice in range(14):
            fecha = pd.Timestamp("2025-01-01") + pd.DateOffset(months=indice)
            filas.append(
                {
                    "semana_fin": fecha.date().isoformat(),
                    "fecha_dato": fecha.date().isoformat(),
                    "geografia": "COLOMBIA",
                    "variable": variable,
                    "valor": 1_000.0 + indice,
                    "unidad": "miles_sacos_60kg",
                    "fuente": "prueba",
                }
            )
    return pd.DataFrame(filas)


def _calibracion_sintetica() -> pd.DataFrame:
    """Trío diario FNC más fresco que el último cierre semanal sintético."""
    return pd.DataFrame(
        [
            {
                "fecha": "2025-12-24",
                "precio_fnc": 2_500_000.0,
                "tasa_cambio": 3_400.0,
                "precio_ny": 300.0,
                "coeficiente_implicito": 2.45,
                "fuente": "FNC",
            },
            {
                "fecha": "2025-12-26",
                "precio_fnc": 2_600_000.0,
                "tasa_cambio": 3_300.0,
                "precio_ny": 310.0,
                "coeficiente_implicito": 2.54,
                "fuente": "FNC",
            },
        ]
    )


def _noticias_sinteticas() -> pd.DataFrame:
    """Titulares con el mismo cable repetido en dos medios y un dominio duplicado."""
    return pd.DataFrame(
        [
            {
                "fecha": date(2025, 12, 26),
                "geografia": "COLOMBIA",
                "titulo": "Helada en Brasil presiona el precio del arábica",
                "url": "https://www.reuters.com/nota-1",
                "fuente": "gdelt",
                "idioma": "spanish",
                "tono": float("nan"),
                "categoria": pd.NA,
            },
            {
                # Mismo titular replicado por otro medio: debe deduplicarse.
                "fecha": date(2025, 12, 25),
                "geografia": "COLOMBIA",
                "titulo": "Helada en Brasil presiona el precio del arábica",
                "url": "https://eltiempo.com/replica",
                "fuente": "gdelt",
                "idioma": "spanish",
                "tono": float("nan"),
                "categoria": pd.NA,
            },
            {
                # Mismo dominio que la primera: debe conservarse solo una.
                "fecha": date(2025, 12, 24),
                "geografia": "COLOMBIA",
                "titulo": "Exportaciones de café crecen en noviembre",
                "url": "https://reuters.com/nota-2",
                "fuente": "gdelt",
                "idioma": "spanish",
                "tono": float("nan"),
                "categoria": pd.NA,
            },
            {
                "fecha": date(2025, 12, 23),
                "geografia": "COLOMBIA",
                "titulo": "Paro camionero afecta salida por el puerto de Buenaventura",
                "url": "https://portafolio.co/nota",
                "fuente": "gdelt",
                "idioma": "spanish",
                "tono": float("nan"),
                "categoria": pd.NA,
            },
        ]
    )


class ConstruirContextoTests(unittest.TestCase):
    def test_contexto_incluye_mercado_mensuales_y_correlaciones(self):
        contexto = comentario_ia.construir_contexto(_historico_sintetico())
        self.assertEqual(
            set(contexto["series_mercado"]),
            {"precio_interno_referencia", "precio_cafe_arabica", "fx_usd_local"},
        )
        fnc = contexto["series_mercado"]["precio_interno_referencia"]
        for clave in (
            "cierre", "fecha_cierre", "variacion_pct",
            "maximo", "minimo", "etiqueta",
        ):
            self.assertIn(clave, fnc)
        self.assertEqual(
            set(contexto["series_mensuales"]),
            {"produccion_nacional", "exportaciones_cafe"},
        )
        produccion = contexto["series_mensuales"]["produccion_nacional"]
        self.assertIn("variacion_mensual_pct", produccion)
        self.assertIn("variacion_interanual_pct", produccion)
        # Las tres series suben en paralelo: correlación 1.0 en la ventana.
        self.assertEqual(
            contexto["correlaciones"]["fnc_vs_coffee_c"]["valor"], 1.0
        )
        self.assertEqual(
            contexto["correlaciones"]["fnc_vs_usd_cop"]["valor"], 1.0
        )

    def test_referencia_diaria_usa_la_ultima_fila_y_mide_la_brecha(self):
        historico = _historico_sintetico()
        contexto = comentario_ia.construir_contexto(
            historico, _calibracion_sintetica()
        )
        referencia = contexto["referencia_diaria"]
        self.assertEqual(referencia["fecha"], "26/12/2025")
        fx = referencia["valores"]["fx_usd_local"]
        self.assertEqual(fx["valor"], 3_300.0)
        self.assertEqual(fx["unidad"], "COP/USD")
        # Brecha frente al cierre semanal sintético de la misma serie.
        cierre = contexto["series_mercado"]["fx_usd_local"]["cierre"]
        esperado = round((3_300.0 / cierre - 1) * 100, 2)
        self.assertEqual(fx["variacion_desde_cierre_semanal_pct"], esperado)
        self.assertEqual(
            set(referencia["valores"]),
            {"precio_interno_referencia", "precio_cafe_arabica", "fx_usd_local"},
        )

    def test_sin_calibracion_no_hay_referencia_diaria(self):
        contexto = comentario_ia.construir_contexto(_historico_sintetico())
        self.assertNotIn("referencia_diaria", contexto)
        contexto_vacia = comentario_ia.construir_contexto(
            _historico_sintetico(), pd.DataFrame()
        )
        self.assertNotIn("referencia_diaria", contexto_vacia)

    def test_contexto_sin_datos_no_lanza(self):
        vacio = pd.DataFrame(
            columns=[
                "semana_fin", "fecha_dato", "geografia",
                "variable", "valor", "unidad", "fuente",
            ]
        )
        contexto = comentario_ia.construir_contexto(vacio)
        self.assertEqual(contexto["series_mercado"], {})
        self.assertEqual(contexto["series_mensuales"], {})
        self.assertEqual(contexto["correlaciones"], {})

    def test_senales_noticias_deduplica_por_titulo_y_dominio(self):
        contexto = comentario_ia.construir_contexto(
            _historico_sintetico(), noticias=_noticias_sinteticas()
        )
        senales = contexto["senales_noticias"]
        titulares = senales["titulares"]
        # 4 filas de entrada: cae la réplica del cable y la segunda nota del
        # mismo dominio; quedan 2, dentro del tope configurado.
        self.assertEqual(len(titulares), 2)
        self.assertEqual(
            [t["dominio"] for t in titulares],
            ["reuters.com", "portafolio.co"],
        )
        primera = titulares[0]
        self.assertEqual(
            primera["titulo"], "Helada en Brasil presiona el precio del arábica"
        )
        self.assertEqual(primera["fecha"], "26/12/2025")
        self.assertIn("sin verificar", senales["descripcion"])

    def test_sin_noticias_no_hay_senales(self):
        contexto = comentario_ia.construir_contexto(_historico_sintetico())
        self.assertNotIn("senales_noticias", contexto)
        contexto_vacio = comentario_ia.construir_contexto(
            _historico_sintetico(), noticias=pd.DataFrame()
        )
        self.assertNotIn("senales_noticias", contexto_vacio)

    def test_senales_respetan_el_tope_configurado(self):
        noticias = pd.concat(
            [
                pd.DataFrame(
                    [
                        {
                            "fecha": date(2025, 12, 20 + i),
                            "geografia": "COLOMBIA",
                            "titulo": f"Titular distinto número {i}",
                            "url": f"https://subdominio-{i}.reuters.com/nota",
                            "fuente": "gdelt",
                            "idioma": "spanish",
                            "tono": float("nan"),
                            "categoria": pd.NA,
                        }
                    ]
                )
                for i in range(6)
            ],
            ignore_index=True,
        )
        contexto = comentario_ia.construir_contexto(
            _historico_sintetico(), noticias=noticias
        )
        titulares = contexto["senales_noticias"]["titulares"]
        self.assertEqual(len(titulares), comentario_ia.NOTICIAS_COMENTARIO_MAX)
        # Se priorizan los más recientes.
        self.assertEqual(titulares[0]["fecha"], "25/12/2025")

    def test_descarta_dominios_no_reconocidos(self):
        noticias = _noticias_sinteticas().copy()
        noticias.loc[:, "url"] = [
            f"https://sitio-opaco-{indice}.example/nota"
            for indice in range(len(noticias))
        ]

        contexto = comentario_ia.construir_contexto(
            _historico_sintetico(), noticias=noticias
        )

        self.assertNotIn("senales_noticias", contexto)

    def test_pocas_semanas_no_generan_resumen_de_mercado(self):
        historico = _historico_sintetico()
        recorte = historico[
            historico["variable"].isin(
                ["produccion_nacional", "exportaciones_cafe"]
            )
            | (
                historico["fecha_dato"]
                >= historico["fecha_dato"].max()
            )
        ]
        contexto = comentario_ia.construir_contexto(recorte)
        self.assertEqual(contexto["series_mercado"], {})


class GenerarComentarioTests(unittest.TestCase):
    def _cliente_simulado(self, texto: str, stop_reason: str = "end_turn"):
        respuesta = SimpleNamespace(
            stop_reason=stop_reason,
            content=[SimpleNamespace(type="text", text=texto)],
        )
        cliente = mock.Mock()
        cliente.messages.create.return_value = respuesta
        return cliente

    def test_generar_devuelve_comentario_bilingue_con_trazabilidad(self):
        contexto = comentario_ia.construir_contexto(_historico_sintetico())
        cliente = self._cliente_simulado(
            json.dumps(
                {"comentario_es": "Texto ES.", "comentario_en": "Text EN."}
            )
        )
        comentario = comentario_ia.generar_comentario(contexto, cliente=cliente)
        self.assertEqual(comentario["comentario_es"], "Texto ES.")
        self.assertEqual(comentario["comentario_en"], "Text EN.")
        self.assertEqual(comentario["modelo"], comentario_ia.COMENTARIO_IA_MODELO)
        self.assertEqual(
            comentario["fecha_generacion"], date.today().isoformat()
        )
        llamada = cliente.messages.create.call_args.kwargs
        self.assertEqual(llamada["model"], comentario_ia.COMENTARIO_IA_MODELO)
        # El mensaje de usuario contiene solo las cifras del contexto.
        self.assertIn("precio_interno_referencia", llamada["messages"][0]["content"])

    def test_generar_lanza_si_el_modelo_declina(self):
        contexto = comentario_ia.construir_contexto(_historico_sintetico())
        cliente = self._cliente_simulado("", stop_reason="refusal")
        with self.assertRaises(RuntimeError):
            comentario_ia.generar_comentario(contexto, cliente=cliente)

    def test_generar_exige_y_registra_conexion_con_noticia(self):
        contexto = comentario_ia.construir_contexto(
            _historico_sintetico(), noticias=_noticias_sinteticas()
        )
        cliente = self._cliente_simulado(
            json.dumps(
                {
                    "comentario_es": (
                        "Un titular de reuters.com del 26/12/2025 sobre heladas "
                        "coincide con el avance de Coffee C de 1,0%."
                    ),
                    "comentario_en": (
                        "A reuters.com headline from 26/12/2025 about frost "
                        "coincides with Coffee C's 1.0% increase."
                    ),
                    "noticia_conectada": {
                        "dominio": "reuters.com",
                        "fecha": "26/12/2025",
                        "variable_dato": "precio_cafe_arabica",
                    },
                }
            )
        )

        comentario = comentario_ia.generar_comentario(contexto, cliente=cliente)

        self.assertEqual(comentario["noticias_disponibles"], 2)
        self.assertEqual(comentario["noticia_conectada"]["dominio"], "reuters.com")
        esquema = cliente.messages.create.call_args.kwargs["output_config"]["format"]["schema"]
        self.assertIn("noticia_conectada", esquema["required"])

    def test_generar_rechaza_noticia_que_no_aparece_en_el_texto(self):
        contexto = comentario_ia.construir_contexto(
            _historico_sintetico(), noticias=_noticias_sinteticas()
        )
        cliente = self._cliente_simulado(
            json.dumps(
                {
                    "comentario_es": "Comentario sin trazabilidad.",
                    "comentario_en": "Comment without traceability.",
                    "noticia_conectada": {
                        "dominio": "reuters.com",
                        "fecha": "26/12/2025",
                        "variable_dato": "precio_cafe_arabica",
                    },
                }
            )
        )

        with self.assertRaisesRegex(RuntimeError, "no incluye dominio y fecha"):
            comentario_ia.generar_comentario(contexto, cliente=cliente)


class PersistenciaTests(unittest.TestCase):
    def test_guardar_y_cargar_ida_y_vuelta(self):
        comentario = {
            "fecha_generacion": "2026-07-06",
            "modelo": "claude-opus-4-8",
            "periodo_semanas": 4,
            "comentario_es": "ES",
            "comentario_en": "EN",
        }
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "comentario_periodo.json"
            with (
                mock.patch.object(comentario_ia, "ARCHIVO_COMENTARIO_IA", ruta),
                mock.patch.object(
                    comentario_ia, "DIR_COMENTARIO", Path(carpeta)
                ),
            ):
                comentario_ia.guardar(comentario)
                self.assertEqual(comentario_ia.cargar(), comentario)

    def test_cargar_devuelve_none_si_falta_o_esta_corrupto(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "comentario_periodo.json"
            with mock.patch.object(comentario_ia, "ARCHIVO_COMENTARIO_IA", ruta):
                self.assertIsNone(comentario_ia.cargar())
                ruta.write_text("{no es json", encoding="utf-8")
                self.assertIsNone(comentario_ia.cargar())
                ruta.write_text(json.dumps({"otra": "cosa"}), encoding="utf-8")
                self.assertIsNone(comentario_ia.cargar())


if __name__ == "__main__":
    unittest.main()
