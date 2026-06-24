# Continuidad técnica entre IAs - Monitor Agro Colombia

Bitácora operativa para asistentes con acceso al repositorio. Contiene solo el
estado y los hallazgos que no conviene reconstruir en cada relevo. El contrato
técnico estable está en `CLAUDE.md`; la estrategia de producto está en
`BRIEFING_CHAT.md`.

## Cómo retomar

1. Leer `CLAUDE.md` completo.
2. Leer este archivo.
3. Ejecutar `git status --short` y `git log --oneline -8`.
4. Verificar con código y pruebas cualquier dato operativo que pueda haber
   cambiado desde la fecha de actualización.

No es necesario leer `BRIEFING_CHAT.md` para una tarea puramente técnica. Sí
debe leerse cuando el cambio dependa de audiencia, utilidad, jerarquía visual o
una decisión de producto.

---

## Punto de control

Actualizado: **2026-06-24**.

- El MVP descriptivo ya tiene fuentes, controles de calidad, histórico desde
  2023, indicadores neutrales, preparación visual y dashboard básico.
- Se recibió feedback de la beneficiaria vinculada a CRECE. La prioridad
  inmediata es convertir el panorama comercial en una herramienta reutilizable
  para investigación, informes y reuniones; la capa climática se conserva, pero
  no se amplía a partir de este feedback.
- El conocimiento cafetero experto y el score continúan pausados por decisión
  del usuario.
- Próximo trabajo: fortalecer la lectura comercial y preparar un brief
  ejecutivo exportable. Después se investigará una fuente defendible de
  producción/productividad territorial.
- Git es la fuente de verdad del historial; no mantener aquí una copia de
  `git log`.

---

## Estado verificable

### Cobertura y calidad

- El pivote de comparación LatAm a ocho departamentos cafeteros colombianos
  está completo de extremo a extremo.
- Un snapshot completo contiene exactamente 35 filas: 3 comerciales y 32
  climáticas (8 departamentos por 4 variables).
- La unión conserva `fecha_snapshot` y `fecha_dato`; las fuentes pueden tener
  fechas de disponibilidad diferentes.
- El snapshot inicial `snapshot_2026-06-21.csv` precede esa validación y tiene
  un FX fechado un día después del snapshot. Se conserva como evidencia; las
  corridas nuevas bloquean esa inconsistencia.

### Histórico

- `procesar/historico.py` acepta rangos, excluye semanas parciales y actualiza
  de forma idempotente.
- Rango validado: `2023-01-08` a `2026-06-14`, 180 semanas completas.
- Resultados validados: 33.368 filas diarias y 6.300 filas semanales, sin nulos
  ni duplicados y con 35 indicadores por semana.
- Mercado y FNC usan el último dato disponible de cada semana. Clima suma
  lluvia y calcula mínima, máxima y promedio semanal.

### Indicadores, preparación visual y dashboard

- Ranking 1 significa valor numérico más alto; no significa mejor, oportunidad
  ni menor riesgo.
- Validación: 44.946 filas derivadas, 180 semanas, rankings de 1 a 8 y cero
  duplicados.
- La preparación visual genera 6.300 filas listas para gráficos, 35 filas de
  resumen y un catálogo de 7 variables.
- `Panorama nacional` muestra café ICE, USD/COP y precio interno FNC. No cambia
  al elegir departamento porque esas series tienen alcance global/nacional.
- El panorama comercial permite descargar el periodo filtrado en CSV con fecha
  real del dato, unidad, variaciones, fuente y alcance. También muestra cobertura
  y tratamiento semanal de cada serie.
- Los periodos disponibles incluyen 3 y 6 meses, 1 y 3 años y todo el histórico.
- Al cambiar departamento se activa su pestaña y aparece el municipio de
  referencia. No existe selector municipal: por ahora hay una coordenada
  representativa por departamento.
- El tema claro está fijado en `.streamlit/config.toml`; los colores editables
  se centralizan en `config.py`.
- Validación tras el último ajuste: 28 pruebas unitarias, ejecución funcional
  de Streamlit sin excepciones y endpoint de salud `ok`.
- URL local mientras el servidor esté corriendo: `http://localhost:8501`.

---

## Hallazgos que pueden evitar retrabajo

- yfinance puede devolver columnas `MultiIndex`; la normalización actual ya
  contempla que `datos["Close"]` resulte ser un `DataFrame`.
- El precio FNC colombiano usa puntos como separadores de miles. El parser
  convierte, por ejemplo, `$2.110.000` a `2110000` y aplica una banda de
  plausibilidad para evitar interpretarlo como `2.11`.
- El Excel histórico FNC se descubre desde la página de estadísticas y contiene
  precio diario desde 2003; el backfill activo lo filtra desde 2023.
- GDELT puede responder `RateLimitError`. El fallback vacío funciona, pero
  sigue pendiente decidir otra estrategia si el límite se vuelve recurrente.
- El PDF FNC por ciudad fue descartado por fragilidad y escasa diferencia
  frente al precio nacional. No reabrir esa decisión sin una necesidad de
  producto concreta.
- Las coordenadas climáticas son referencias municipales y no representan toda
  la variación interna de cada departamento.

---

## Límites vigentes

- No iniciar score ni interpretación agronómica hasta recibir feedback e
  información experta. Las razones y preguntas están en `BRIEFING_CHAT.md`.
- Mantener commits entre unidades de trabajo validadas.
- No convertir el selector departamental en selector municipal sin ampliar
  primero la cobertura de datos.

---

## Restricciones operativas observadas

- La red del sandbox puede quedar bloqueada por un proxy local; las validaciones
  reales de fuentes pueden requerir permisos de red.
- En Windows, `py_compile` o pruebas que crean temporales pueden fallar al
  limpiar `__pycache__` o `%TEMP%`; se puede validar sintaxis con `ast.parse`
  sin escribir bytecode.
- Las operaciones de Git pueden requerir permisos para escribir en `.git`.

## Mantenimiento

Actualizarla solo cuando cambie el estado técnico, una decisión vigente, una
limitación, una validación relevante o el próximo paso. Reemplazar información
obsoleta en vez de acumular versiones contradictorias. No copiar secciones de
`CLAUDE.md` ni convertirla en un changelog completo; Git ya conserva ese
historial.
