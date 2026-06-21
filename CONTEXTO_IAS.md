# Contexto entre IAs - Monitor Agro LatAm

Este archivo sirve como bitacora de continuidad para trabajar alternando entre
asistentes, IDEs y sesiones. Antes de retomar el proyecto, leer en este orden:

1. `CLAUDE.md` - reglas, fases y contratos del proyecto.
2. `CONTEXTO_IAS.md` - novedades, decisiones recientes y punto exacto de avance.
3. `git log --oneline -5` y `git status --short` - confirmar historial y arbol limpio.

Regla practica: cuando una IA o el usuario cierre una unidad de trabajo
validada, registrar aqui lo importante y hacer commit.

---

## Estado actual

Proyecto: monitor semanal de condiciones para agroexportacion latinoamericana,
con foco inicial en cafe.

Fase actual: **Fase 1 completa**.

Siguiente paso natural: **Fase 2 - unir fuentes y guardar el primer snapshot en
`datos/snapshots/`**.

Commits relevantes:

- `4791a62` - Fase 1d: implementar `fuentes/noticias.py` con GDELT.
- `e14bfad` - Fase 1c: implementar `fuentes/clima.py` con Open-Meteo.
- `cc08a46` - Fase 1b: implementar `fuentes/cafe.py` con yfinance.
- `6410d74` - Fase 1a: implementar `fuentes/fx.py` con yfinance.
- `d0767f0` - Fase 0: esqueleto y contratos base.

---

## Convenciones que no se deben romper

- Cada modulo en `fuentes/` expone una unica funcion publica `obtener()`.
- Las fuentes numericas devuelven exactamente:
  `fecha`, `pais`, `variable`, `valor`, `unidad`, `fuente`.
- Noticias devuelve exactamente:
  `fecha`, `pais`, `titulo`, `url`, `fuente`, `idioma`, `tono`, `categoria`.
- Si una fuente falla, debe devolver un `DataFrame` vacio con columnas correctas.
- Todo parametro editable debe vivir en `config.py`.
- No mezclar fases en un mismo cambio.
- Hacer commits entre cambios validados para poder alternar entre asistentes.

---

## Hallazgos y decisiones tecnicas

### FX - Fase 1a

- Se usa `yfinance` para las cinco monedas, no una mezcla Frankfurter +
  yfinance.
- Motivo: `yfinance` cubre COP, BRL, PEN, HNL y MXN; Frankfurter/BCE no cubre
  COP, PEN ni HNL.
- `yfinance` puede devolver columnas `MultiIndex`; para extraer cierre se usa
  `datos["Close"]` y, si es `DataFrame`, `iloc[:, 0]`.
- Las fechas pueden diferir por pais. Se toma el ultimo cierre disponible de los
  ultimos 5 dias, adecuado para frecuencia semanal.

### Cafe - Fase 1b

- Se usa `config.TICKER_CAFE_ARABICA = "KC=F"`.
- El precio del cafe es global, por eso `pais = "GLOBAL"`.
- Variable: `precio_cafe_arabica`.
- Unidad: `USc/lb`.
- Fuente fragil: `yfinance` raspa Yahoo Finance y puede romperse.
- Ultima validacion real: `2026-06-18`, valor aproximado `256.10 USc/lb`.

### Clima - Fase 1c

- Se usa Open-Meteo con coordenadas de `config.PAISES[*]["zona_cafetera"]`.
- Variables configuradas:
  `temperature_2m_min`, `temperature_2m_max`, `precipitation_sum`.
- Mapeo de salida:
  `temp_min` (`grados C`), `temp_max` (`grados C`), `precipitacion` (`mm`).
- Ultima validacion real: `120` filas, equivalente a 5 paises x 3 variables x
  8 fechas (`past_days=7` mas dia actual).

### Noticias - Fase 1d

- Se usa `gdeltdoc` con `GdeltDoc` y `Filters`.
- `gdeltdoc` ya esta en `requirements.txt`, pero hubo que instalarlo en el
  entorno `.venv`.
- Se agrego `NOTICIAS_MAX_REGISTROS = 25` en `config.py`.
- GDELT se consulta por pais usando `fips` de `config.PAISES`.
- Ultima validacion real devolvio `RateLimitError` para todos los paises; el
  fallback funciono y devolvio `DataFrame` vacio con columnas correctas.
- La normalizacion fue probada con un DataFrame artificial estilo GDELT:
  `seendate`, `title`, `url`, `language` -> contrato de noticias.
- `tono` queda como `NaN` float; `categoria` queda pendiente para fase posterior.

---

## Limitaciones del entorno encontradas

- El sandbox a veces bloquea red usando proxy local `127.0.0.1:9`.
- Para validar fuentes reales puede ser necesario ejecutar con permisos de red.
- `py_compile` sobre `fuentes/noticias.py` fallo por permisos escribiendo en
  `__pycache__`; se valido importando con `PYTHONDONTWRITEBYTECODE=1`.
- `git add` y `git commit` pueden requerir permisos escalados porque escriben en
  `.git`.

---

## Decisiones del usuario

- El proyecto se mantiene como MVP primero; luego se mejora para LinkedIn.
- El resultado final deseado debe impresionar como herramienta analitica, no
  solo como scripts: ranking/score semanal, narrativa ejecutiva y dashboard.
- El usuario quiere mantener el habito de commits entre cambios, sin importar
  que asistente hizo el trabajo.
- El usuario quiere que este archivo registre novedades, decisiones del chat,
  hallazgos y cualquier instruccion relevante para que otras IAs retomen bien.

---

## Como actualizar este archivo

Actualizarlo cuando ocurra cualquiera de estas cosas:

- Se complete una fase o subfase.
- Se haga un commit relevante.
- Una fuente revele una limitacion nueva.
- El usuario tome una decision de producto, metodologia o estilo.
- Se agregue una dependencia, variable de configuracion o restriccion operativa.
- Se descubra algo necesario para que otra IA no repita trabajo.

Formato recomendado para nuevas entradas:

```text
### YYYY-MM-DD - Titulo breve

- Que cambio.
- Que se valido.
- Que limitacion o decision queda.
- Commit relacionado, si existe.
```

---

## Proxima tarea sugerida

Implementar **Fase 2 - `procesar/unir.py`**:

- Llamar las fuentes ya implementadas.
- Unir datos numericos en una tabla semanal.
- Decidir como representar fechas distintas entre fuentes:
  mantener fecha real del dato y/o agregar una fecha de snapshot semanal.
- Guardar el primer snapshot en `datos/snapshots/`.
- Verificar con `python main.py` o un comando aislado equivalente.
- Registrar aqui la decision tomada y hacer commit.
