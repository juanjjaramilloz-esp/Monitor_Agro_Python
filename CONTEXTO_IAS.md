# Continuidad técnica entre IAs - Monitor Agro Colombia

Bitácora operativa para asistentes con acceso al repositorio. Registra el punto
exacto de avance y lo que no se puede inferir leyendo el código rápidamente.
Las reglas, contratos y comandos permanentes viven únicamente en `CLAUDE.md`.

## Cómo retomar

1. Leer `CLAUDE.md` completo.
2. Leer este archivo.
3. Ejecutar `git status --short` y `git log --oneline -8`.
4. No asumir que una tarea pendiente sigue pendiente si Git o las pruebas
   demuestran lo contrario.

`BRIEFING_CHAT.md` no es requisito para programar: está diseñado para chats
estratégicos sin acceso al repositorio.

---

## Punto de control actual

Actualizado: **2026-06-22**.

- El MVP descriptivo ya tiene fuentes, controles de calidad, histórico desde
  2023, indicadores neutrales, preparación visual y dashboard básico.
- La etapa actual es **feedback de visualizaciones**. El conocimiento cafetero
  experto y el score continúan pausados por decisión del usuario.
- Próximo trabajo: recoger y aplicar feedback de comprensión/utilidad del
  dashboard. No diseñar todavía el score definitivo.
- `BRIEFING_CHAT.md` entra ahora al control de versiones y debe mantenerse como
  resumen estratégico, no como registro de cada cambio técnico.

Commits más recientes:

- `d85359d` - Corregir tema e interacción del dashboard.
- `f9c4a89` - Crear dashboard básico para feedback.
- `f586b3b` - Preparar datos y metadatos para visualizaciones.
- `cde861d` - Agregar indicadores de tendencia y comparación.
- `4a24e51` - Construir backfill histórico semanal desde 2023.
- `3ef2d23` - Agregar modo histórico a fuentes numéricas.
- `9536939` - Agregar controles de calidad para snapshots.
- `f46198b` - Actualizar contexto tras pivote a Colombia.

---

## Estado verificable por bloque

### Fuentes, unión y calidad

- Fuentes activas: café ICE y USD/COP por yfinance, precio interno y Excel
  histórico FNC, clima por Open-Meteo y noticias nacionales por GDELT.
- El pivote de comparación LatAm a ocho departamentos cafeteros colombianos
  está completo de extremo a extremo.
- Un snapshot completo contiene exactamente 35 filas: 3 comerciales y 32
  climáticas (8 departamentos por 4 variables).
- La unión conserva `fecha_snapshot` y `fecha_dato`; no se oculta que las
  fuentes pueden tener fechas de disponibilidad diferentes.
- La calidad clasifica componentes como `OK`, `VACIO`, `INCOMPLETO` o
  `FECHA_FUTURA`. Un snapshot existente solo se reemplaza con autorización
  explícita.
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

### Indicadores y preparación visual

- `procesar/indicadores.py` produce cambios semanales, cambios de 4 semanas,
  medias móviles de 4 y 12 semanas, anomalía histórica y comparación
  departamental.
- La anomalía compara contra hasta 52 semanas previas, exige 26 observaciones
  y no usa datos futuros.
- Ranking 1 significa valor numérico más alto; no significa mejor, oportunidad
  ni menor riesgo.
- Validación: 44.946 filas derivadas, 180 semanas, rankings de 1 a 8 y cero
  duplicados.
- `procesar/visualizacion.py` genera 6.300 filas listas para gráficos, 35 filas
  de resumen y un catálogo de 7 variables. Incluye etiquetas, colores,
  municipio de referencia e índice base 100 para las tres series comerciales.

### Dashboard para feedback

- Aplicación: `app.py`, Streamlit 1.58.0 y Plotly 6.8.0.
- `Panorama nacional` muestra café ICE, USD/COP y precio interno FNC. No cambia
  al elegir departamento porque esas series tienen alcance global/nacional.
- La vista departamental muestra cuatro métricas climáticas, lluvia con media
  móvil y temperaturas mínima, promedio y máxima.
- `Comparación` muestra los ocho departamentos y la historia del seleccionado
  frente a la mediana.
- Al cambiar departamento se activa su pestaña y aparece el municipio de
  referencia. No existe selector municipal: por ahora hay una coordenada
  representativa por departamento.
- El tema claro está fijado en `.streamlit/config.toml`; los colores editables
  se centralizan en `config.py`.
- Validación tras el último ajuste: 27 pruebas unitarias, prueba funcional
  Caldas/Manizales -> Huila/Pitalito sin excepciones y endpoint de salud `ok`.
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

## Límites del siguiente cambio

- No iniciar score ni interpretación agronómica hasta que el usuario entregue
  feedback e información experta. Las preguntas de producto están en
  `BRIEFING_CHAT.md`.
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

## Cómo mantener esta bitácora

Actualizarla solo cuando cambie el estado técnico, una decisión vigente, una
limitación, una validación relevante o el próximo paso. Reemplazar información
obsoleta en vez de acumular versiones contradictorias. No copiar secciones de
`CLAUDE.md` ni convertirla en un changelog completo; Git ya conserva ese
historial.
