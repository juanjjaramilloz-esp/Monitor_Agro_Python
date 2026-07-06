"""Comentario ejecutivo del periodo redactado con Claude, anclado a datos reales.

Corre solo en la automatización de datos (GitHub Actions), nunca en runtime de
la app: el resultado queda versionado en ``datos/comentario/`` con fecha y
modelo, y el tablero solo lee ese archivo. El prompt entrega cifras exactas ya
calculadas desde el histórico y obliga a describir sin predecir ni recomendar,
el mismo estándar de honestidad del resto del kit.

Uso: ``python -m reporte.comentario_ia`` (requiere ANTHROPIC_API_KEY en el
entorno; sin la key informa y termina sin error para no romper corridas
locales).
"""

import json
import os
from datetime import date

import pandas as pd

from config import (
    ARCHIVO_COMENTARIO_IA,
    CATALOGO_VARIABLES,
    COMENTARIO_IA_MAX_TOKENS,
    COMENTARIO_IA_MODELO,
    COMENTARIO_IA_SEMANAS,
    CORRELACION_VENTANA_SEMANAS,
    DIR_COMENTARIO,
    DIR_HISTORICO,
)

RUTA_HISTORICO = DIR_HISTORICO / "historico_semanal.csv"

VARIABLES_MERCADO = [
    "precio_interno_referencia",
    "precio_cafe_arabica",
    "fx_usd_local",
]
VARIABLES_MENSUALES_COMENTARIO = ["produccion_nacional", "exportaciones_cafe"]

INSTRUCCIONES_SISTEMA = """Eres el analista de datos de "Pulso Cafetero", un \
kit de consulta sobre la agroexportación de café de Colombia. Redactas un \
comentario ejecutivo del periodo para caficultores, cooperativas y analistas \
que YA VIERON las cifras sueltas en el tablero (cierres, variaciones, \
máximos/mínimos por serie). Tu valor no es repetir esas cifras una por una: \
es CRUZARLAS para explicar cómo se combinaron los movimientos.

Reglas no negociables:
- Usa ÚNICAMENTE las cifras y fechas entregadas en el mensaje; no agregues \
datos de tu memoria ni contexto externo (noticias, clima, política).
- Describe lo observado; NUNCA predigas, recomiendes comprar/vender ni \
califiques nada como oportunidad o riesgo.
- Cita cifras con su fecha (formato dd/mm/aaaa) tal como vienen en los datos.
- Si un dato viene marcado como no disponible, no lo menciones ni lo estimes.
- La correlación no implica causalidad; si la mencionas, dilo.

Cómo cruzar las cifras (esto es lo que hace útil el comentario, no una lista \
de series aisladas):
- Si el precio interno FNC y el USD/COP se movieron en direcciones distintas \
(o una compensó a la otra), dilo explícitamente citando ambos porcentajes: \
p. ej. "aunque el dólar cayó X%, el precio interno subió Y% porque el alza \
de Z% en Coffee C compensó esa caída".
- Usa las dos correlaciones para decir cuál de las dos variables (Coffee C o \
USD/COP) acompañó más de cerca al precio interno en el periodo, comparando \
los dos coeficientes entre sí.
- Si el mes de producción o de exportaciones coincide con el periodo de \
mercado descrito, señala si esa variación mensual fue en la misma dirección \
que el mercado o no; si no coincide el mes, no fuerces la comparación.
- Cada oración del párrafo 1 y 2 debe conectar al menos dos cifras entre sí, \
no describir una sola serie de forma aislada.

Tono profesional y claro, sin jerga innecesaria; 3 párrafos cortos: (1) cómo \
se combinaron los movimientos del precio interno, Coffee C y USD/COP en el \
periodo (la relación entre ellos, no cada uno por separado), (2) qué dicen \
las dos correlaciones sobre cuál variable pesó más, y cómo se compara la \
variación mensual de producción/exportaciones con la dirección del mercado \
cuando el mes coincide, (3) qué relación entre series conviene seguir \
observando y por qué, en términos descriptivos (sin pronóstico).

Entrega el comentario en español y su traducción fiel al inglés."""

ESQUEMA_SALIDA = {
    "type": "object",
    "properties": {
        "comentario_es": {
            "type": "string",
            "description": "Comentario de 3 párrafos en español, separados por líneas en blanco.",
        },
        "comentario_en": {
            "type": "string",
            "description": "Traducción fiel al inglés del mismo comentario.",
        },
    },
    "required": ["comentario_es", "comentario_en"],
    "additionalProperties": False,
}


def _fecha(valor: object) -> str:
    return f"{pd.Timestamp(valor):%d/%m/%Y}"


def _resumen_semanal(serie: pd.DataFrame, semanas: int) -> dict | None:
    """Cierre, variación y extremos de una serie semanal en las últimas semanas."""
    ordenada = serie.sort_values("fecha_dato").reset_index(drop=True)
    if ordenada.empty:
        return None
    ultima = ordenada.iloc[-1]
    corte = pd.Timestamp(ultima["fecha_dato"]) - pd.Timedelta(weeks=semanas)
    periodo = ordenada[pd.to_datetime(ordenada["fecha_dato"]) > corte]
    if len(periodo) < 2:
        return None
    primera = periodo.iloc[0]
    maxima = periodo.loc[periodo["valor"].idxmax()]
    minima = periodo.loc[periodo["valor"].idxmin()]
    variacion = (float(ultima["valor"]) / float(primera["valor"]) - 1) * 100
    return {
        "cierre": float(ultima["valor"]),
        "fecha_cierre": _fecha(ultima["fecha_dato"]),
        "variacion_pct": round(variacion, 2),
        "desde_fecha": _fecha(primera["fecha_dato"]),
        "maximo": float(maxima["valor"]),
        "fecha_maximo": _fecha(maxima["fecha_dato"]),
        "minimo": float(minima["valor"]),
        "fecha_minimo": _fecha(minima["fecha_dato"]),
        "unidad": str(ultima["unidad"]),
    }


def _resumen_mensual(serie: pd.DataFrame) -> dict | None:
    """Último mes publicado y sus variaciones mensual e interanual."""
    ordenada = serie.sort_values("fecha_dato").reset_index(drop=True)
    if ordenada.empty:
        return None
    ultima = ordenada.iloc[-1]
    resumen = {
        "valor": float(ultima["valor"]),
        "mes": f"{pd.Timestamp(ultima['fecha_dato']):%m/%Y}",
        "unidad": str(ultima["unidad"]),
    }
    if len(ordenada) >= 2:
        previo = float(ordenada.iloc[-2]["valor"])
        if previo:
            resumen["variacion_mensual_pct"] = round(
                (float(ultima["valor"]) / previo - 1) * 100, 2
            )
    if len(ordenada) >= 13:
        anterior = float(ordenada.iloc[-13]["valor"])
        if anterior:
            resumen["variacion_interanual_pct"] = round(
                (float(ultima["valor"]) / anterior - 1) * 100, 2
            )
    return resumen


def _correlacion_reciente(
    historico: pd.DataFrame,
    variable_a: str,
    variable_b: str,
    ventana: int,
) -> float | None:
    """Pearson sobre variaciones semanales en la ventana más reciente."""
    pivote = (
        historico[historico["variable"].isin([variable_a, variable_b])]
        .pivot_table(index="semana_fin", columns="variable", values="valor")
        .sort_index()
        .pct_change()
        .dropna()
        .tail(ventana)
    )
    if len(pivote) < ventana or variable_a not in pivote or variable_b not in pivote:
        return None
    valor = pivote[variable_a].corr(pivote[variable_b])
    return None if pd.isna(valor) else round(float(valor), 2)


def construir_contexto(historico: pd.DataFrame) -> dict:
    """Arma el paquete de cifras exactas que el modelo puede citar (y nada más)."""
    datos = historico.copy()
    datos["fecha_dato"] = pd.to_datetime(datos["fecha_dato"])
    contexto: dict = {
        "periodo_semanas": COMENTARIO_IA_SEMANAS,
        "series_mercado": {},
        "series_mensuales": {},
        "correlaciones": {},
    }
    for variable in VARIABLES_MERCADO:
        serie = datos[datos["variable"].eq(variable)]
        resumen = _resumen_semanal(serie, COMENTARIO_IA_SEMANAS)
        if resumen is not None:
            resumen["etiqueta"] = CATALOGO_VARIABLES[variable]["etiqueta"]
            contexto["series_mercado"][variable] = resumen
    for variable in VARIABLES_MENSUALES_COMENTARIO:
        serie = datos[datos["variable"].eq(variable)]
        resumen = _resumen_mensual(serie)
        if resumen is not None:
            resumen["etiqueta"] = CATALOGO_VARIABLES[variable]["etiqueta"]
            contexto["series_mensuales"][variable] = resumen
    correlacion_cafe = _correlacion_reciente(
        datos, "precio_interno_referencia", "precio_cafe_arabica",
        CORRELACION_VENTANA_SEMANAS,
    )
    correlacion_fx = _correlacion_reciente(
        datos, "precio_interno_referencia", "fx_usd_local",
        CORRELACION_VENTANA_SEMANAS,
    )
    if correlacion_cafe is not None:
        contexto["correlaciones"]["fnc_vs_coffee_c"] = {
            "valor": correlacion_cafe,
            "ventana_semanas": CORRELACION_VENTANA_SEMANAS,
            "nota": "Pearson sobre variaciones semanales; no implica causalidad.",
        }
    if correlacion_fx is not None:
        contexto["correlaciones"]["fnc_vs_usd_cop"] = {
            "valor": correlacion_fx,
            "ventana_semanas": CORRELACION_VENTANA_SEMANAS,
            "nota": "Pearson sobre variaciones semanales; no implica causalidad.",
        }
    return contexto


def construir_mensaje(contexto: dict) -> str:
    """Mensaje de usuario: solo las cifras que el comentario puede citar."""
    return (
        "Redacta el comentario del periodo con base exclusiva en estas cifras "
        f"(últimas {contexto['periodo_semanas']} semanas del mercado y último "
        "mes publicado de las series mensuales):\n\n"
        + json.dumps(contexto, ensure_ascii=False, indent=2)
    )


def generar_comentario(contexto: dict, cliente=None) -> dict:
    """Llama a Claude y devuelve el comentario bilingüe validado por esquema."""
    if cliente is None:
        import anthropic

        cliente = anthropic.Anthropic()
    respuesta = cliente.messages.create(
        model=COMENTARIO_IA_MODELO,
        max_tokens=COMENTARIO_IA_MAX_TOKENS,
        system=INSTRUCCIONES_SISTEMA,
        output_config={"format": {"type": "json_schema", "schema": ESQUEMA_SALIDA}},
        messages=[{"role": "user", "content": construir_mensaje(contexto)}],
    )
    if respuesta.stop_reason == "refusal":
        raise RuntimeError("comentario_ia: el modelo declinó la solicitud")
    texto = next(
        bloque.text for bloque in respuesta.content if bloque.type == "text"
    )
    comentario = json.loads(texto)
    return {
        "fecha_generacion": date.today().isoformat(),
        "modelo": COMENTARIO_IA_MODELO,
        "periodo_semanas": contexto["periodo_semanas"],
        "comentario_es": comentario["comentario_es"],
        "comentario_en": comentario["comentario_en"],
    }


def guardar(comentario: dict) -> None:
    DIR_COMENTARIO.mkdir(parents=True, exist_ok=True)
    ARCHIVO_COMENTARIO_IA.write_text(
        json.dumps(comentario, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def cargar() -> dict | None:
    """Lee el comentario versionado; None si no existe o está corrupto."""
    try:
        comentario = json.loads(ARCHIVO_COMENTARIO_IA.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not all(
        clave in comentario
        for clave in ("fecha_generacion", "comentario_es", "comentario_en")
    ):
        return None
    return comentario


def main() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("comentario_ia: sin ANTHROPIC_API_KEY en el entorno; no se genera.")
        return
    historico = pd.read_csv(RUTA_HISTORICO)
    contexto = construir_contexto(historico)
    if not contexto["series_mercado"]:
        print("comentario_ia: sin series de mercado suficientes; no se genera.")
        return
    comentario = generar_comentario(contexto)
    guardar(comentario)
    print(
        f"comentario_ia: comentario del {comentario['fecha_generacion']} "
        f"guardado en {ARCHIVO_COMENTARIO_IA}"
    )


if __name__ == "__main__":
    main()
