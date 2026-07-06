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
