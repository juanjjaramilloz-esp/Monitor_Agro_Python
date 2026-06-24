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
  2023, indicadores neutrales, preparación visual, dashboard y brief Markdown.
- Se recibió feedback de la beneficiaria vinculada a CRECE. La prioridad
  inmediata es convertir el panorama comercial en una herramienta reutilizable
  para investigación, informes y reuniones; la capa climática se conserva, pero
  no se amplía a partir de este feedback.
- El conocimiento cafetero experto y el score continúan pausados por decisión
  del usuario.
- Existe un simulador de escenarios separado del score. Desplaza el último
  precio FNC observado en proporción al producto Coffee C × USD/COP, permite
  editar el costo por carga y calcula margen bruto para un volumen supuesto.
  No modela prima, calidad, pasilla, logística, impuestos ni causalidad.
- La primera ampliación confirmada es producción **nacional mensual** FNC. No
  se incorporó producción departamental o municipal.
- El repositorio tiene remoto `origin` en GitHub y la aplicación está
  desplegada en Streamlit Community Cloud. El despliegue público con simulador
  fue verificado por el usuario y carga correctamente.
- Se hizo una ronda de pulido de interfaz para acercar el tablero a un producto:
  se retiró la pestaña `Comparación`, se renombró la sección a "Producción
  nacional mensual", se quitaron textos de cadencia y del ranking, se reorganizó
  el panorama (descargas lado a lado) y se afinó el CSS (radios, sombras suaves,
  botones de descarga con acento). El simulador gana un informe descargable.
- `ACERCA_DE.md` es la guía de contexto para visitantes de la app pública (no de
  instalación); `README.md` sigue siendo la guía técnica de ejecución local.
- Próximo trabajo: validar el kit, el brief y el simulador con una tarea real de
  CRECE antes de ampliar datos o formatos.
- Git es la fuente de verdad del historial; no mantener aquí una copia de
  `git log`.

---

## Estado verificable

### Cobertura y calidad

- El pivote de comparación LatAm a ocho departamentos cafeteros colombianos
  está completo de extremo a extremo.
- Un snapshot completo nuevo contiene 36 filas: 3 comerciales semanales, 1 de
  producción nacional mensual y 32 climáticas.
- La unión conserva `fecha_snapshot` y `fecha_dato`; las fuentes pueden tener
  fechas de disponibilidad diferentes.
- El snapshot inicial `snapshot_2026-06-21.csv` precede esa validación y tiene
  un FX fechado un día después del snapshot. Se conserva como evidencia; las
  corridas nuevas bloquean esa inconsistencia.

### Histórico

- `procesar/historico.py` acepta rangos, excluye semanas parciales y actualiza
  de forma idempotente.
- Rango validado: `2023-01-08` a `2026-06-14`, 180 semanas completas.
- Resultados validados: 33.409 observaciones de fuente y 6.341 filas agregadas,
  sin nulos ni duplicados. Las 41 filas adicionales son meses de producción
  entre enero de 2023 y mayo de 2026; no se repiten en semanas intermedias.
- Mercado y precio FNC usan el último dato disponible de cada semana.
  Producción conserva el mes real publicado. Clima suma lluvia y calcula
  mínima, máxima y promedio semanal.

### Indicadores, preparación visual y dashboard

- Ranking 1 significa valor numérico más alto; no significa mejor, oportunidad
  ni menor riesgo.
- Validación: 45.015 filas derivadas, 180 semanas, rankings de 1 a 8 y cero
  duplicados.
- La preparación visual genera 6.341 filas listas para gráficos, 35 filas de
  resumen reciente y un catálogo de 8 variables.
- El tablero tiene tres pestañas: `Panorama nacional`, el detalle climático del
  departamento elegido y `Simulador`. La pestaña `Comparación` (ranking semanal
  y evolución frente a la mediana departamental) se retiró para acercar la
  herramienta a un producto enfocado; sigue recuperable en el historial de git.
- `Panorama nacional` muestra café ICE, USD/COP y precio interno FNC. No cambia
  al elegir departamento porque esas series tienen alcance global/nacional.
- El panorama comercial permite descargar el periodo filtrado en CSV con fecha
  real del dato, unidad, variaciones, fuente y alcance. También muestra cobertura
  y tratamiento semanal de cada serie.
- Producción aparece como bloque mensual separado, con cambio mensual e
  interanual, fecha real y sin relleno semanal. Las barras tienen ancho fijo y
  representan una observación por mes, sin sugerir continuidad semanal.
- El rango puede elegirse con presets o fechas personalizadas. El mismo periodo
  genera un brief Markdown descargable con cifras, lectura neutral, fuentes,
  cobertura, cadencias y limitaciones.
- Los periodos disponibles incluyen 3 y 6 meses, 1 y 3 años y todo el histórico.
- La pestaña `Simulador` permite mover Coffee C, USD/COP, precio FNC base,
  costo de producción y número de cargas. Muestra precio interno proyectado,
  ingreso, costo, margen por carga, margen total y una matriz de sensibilidad.
  El resumen económico se presenta como una cuenta (ingreso − costo = margen)
  y existe un botón para descargar un informe Markdown del escenario con los
  supuestos, resultados, metodología y limitaciones
  (`reporte.generar.generar_informe_simulador`).
- El costo inicial es el costo medio nacional FEPCafé de abril de 2026:
  1.624.000 COP por carga de 125 kg, publicado en el reporte mensual de mayo de
  2026. La interfaz muestra fecha, fuente y permite sustituirlo por un supuesto
  de finca.
- Al cambiar departamento se activa su pestaña y aparece el municipio de
  referencia. No existe selector municipal: por ahora hay una coordenada
  representativa por departamento.
- El tema claro está fijado en `.streamlit/config.toml`; los colores editables
  se centralizan en `config.py`.
- Validación tras el último ajuste: 39 pruebas unitarias, arranque local de
  Streamlit headless con endpoint de salud `ok` y sin excepciones, e informe del
  simulador generado y revisado. La versión pública con simulador ya fue
  verificada por el usuario.
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
- Ese mismo descargable contiene la hoja de producción registrada mensual desde
  1956. El proyecto conserva solo enero de 2023 a mayo de 2026 por coherencia
  con su ventana histórica actual.
- GDELT puede responder `RateLimitError`. El fallback vacío funciona, pero
  sigue pendiente decidir otra estrategia si el límite se vuelve recurrente.
- El PDF FNC por ciudad fue descartado por fragilidad y escasa diferencia
  frente al precio nacional. No reabrir esa decisión sin una necesidad de
  producto concreta.
- Las coordenadas climáticas son referencias municipales y no representan toda
  la variación interna de cada departamento.
- El simulador está calibrado al precio FNC observado. Usa transmisión
  proporcional de Coffee C y USD/COP; no reproduce la fórmula oficial completa
  ni debe presentarse como predicción.
- La fórmula aplicada es: precio FNC base × (USD/COP escenario ÷ USD/COP base)
  × (Coffee C escenario ÷ Coffee C base). El margen bruto resta el costo por
  carga editable y lo multiplica por el número de cargas.

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
