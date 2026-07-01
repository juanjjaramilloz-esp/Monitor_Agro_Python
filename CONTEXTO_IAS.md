# Continuidad técnica — Monitor Agro Colombia

Bitácora operativa para asistentes con acceso al repo. Solo estado y hallazgos
que no conviene reconstruir. Contrato técnico estable: `CLAUDE.md`. Estrategia:
`BRIEFING_CHAT.md`.

**Cómo retomar:** leer `CLAUDE.md` y este archivo; correr `git status --short` y
`git log --oneline -8`; verificar con código/pruebas cualquier dato operativo.
`BRIEFING_CHAT.md` solo si la tarea depende de audiencia o producto.

## Punto de control (2026-06-25)

- MVP descriptivo completo: fuentes, calidad, histórico desde 2023, indicadores
  neutrales, preparación visual, dashboard y brief del periodo en PDF con gráficas.
- Prioridad (feedback CRECE): convertir el panorama comercial en herramienta
  reutilizable para investigación/informes/reuniones. La capa climática se
  conserva pero no se amplía. Score y conocimiento experto siguen pausados.
- Simulador separado del score: estima el precio FNC desde Coffee C × USD/COP
  mediante el coeficiente implícito del último trío coherente que publica la FNC
  (FNC, Coffee C y TRM de la misma fecha). Evita mezclar el FNC oficial con
  cierres Yahoo de otra hora. Si falla esa fuente usa como respaldo la calibración
  reciente de cinco días. El FNC observado calibra y permite comparar, pero no es
  un piso. Ajusta por factor de rendimiento (aprox.), edita costo por carga y
  calcula margen bruto.
- Ampliaciones mensuales confirmadas: producción y exportaciones nacionales FNC
  (no departamentales/municipales). El panorama compara ambos flujos por mes y
  muestra producción menos exportaciones sin interpretarlo como inventario.
- Remoto `origin` en GitHub; app desplegada en Streamlit Community Cloud,
  verificada por el usuario. `ACERCA_DE.md` = guía para visitantes de la app
  pública; `README.md` = guía técnica local.
- Fase 6 (automatización) implementada y **validada en runner real**
  (2026-06-25): la primera corrida manual (`workflow_dispatch`, run 28207717834)
  terminó en `success`, descargó datos frescos y pusheó el commit automático
  `Datos: actualización automática...`, confirmando el ciclo refresca→commit→push→
  redespliegue. `.github/workflows/actualizar-datos.yml` corre cada 2 días (10:00
  UTC). Aún falta producir un snapshot semanal en CI.
- Próximo: validar kit, brief y simulador con una tarea real de CRECE; preparar
  el resultado y la reseña autorizada para el portafolio. El README ya presenta
  problema, solución, evidencia, decisiones e impacto pendiente; la guía
  `docs/portfolio/GUIA.md` contiene entrevista, autorización, textos para CV y
  LinkedIn y guion audiovisual. Siguen pendientes las capturas y el video/GIF:
  Edge headless no esperó el render interactivo de Streamlit, por lo que se
  descartaron las capturas de carga y deben grabarse con un navegador normal.

## Estado verificable

**Cobertura/calidad.** Pivote LatAm → 8 departamentos cafeteros completo.
Snapshot completo = 37 filas (3 comerciales semanales, 2 series mensuales, 32
clima). La unión conserva `fecha_snapshot` y `fecha_dato`. El snapshot inicial
`snapshot_2026-06-21.csv` tiene un FX fechado un día después; se conserva como
evidencia y las corridas nuevas bloquean esa inconsistencia.

**Histórico (`procesar/historico.py`).** Acepta rangos, excluye semanas
parciales, idempotente. Validado `2023-01-08`→`2026-06-14`: 180 semanas, 33.450
observaciones de fuente y 6.382 filas agregadas (41 meses de producción y 41 de
exportaciones, 2023-01..2026-05, sin repetir en semanas). Mercado y FNC usan el
último dato semanal; las series mensuales conservan el mes publicado; clima suma
lluvia y agrega min/max/promedio.

**Indicadores/visual.** Ranking 1 = mayor valor numérico (no mejor/oportunidad/
menor riesgo). Derivados: 45.084 filas, rankings 1-8, sin duplicados. Visual:
6.382 filas para gráficos, 35 de resumen reciente, catálogo de 9 variables.

**App.** Título visible = "Herramienta Consultas y Reportes" (page_title,
`st.title` y los entregables PDF/brief/informe). Internamente el proyecto/repo
sigue llamándose Monitor Agro Colombia.

**Dashboard (2 pestañas).** `Panorama nacional` (entrada) y `Simulador`. La
pestaña climática (`Climatología cafetera`) se **retiró de la UI** por petición
del usuario, junto con el selector de departamento y las funciones
`_grafico_lluvia`/`_grafico_temperaturas`/`_metricas_clima`/`_delta_absoluto`
(recuperables en git). El pipeline climático se conserva: `fuentes/clima.py`,
`REGIONES_CAFE`, la agregación en `historico.py` y los datos siguen en el repo;
el clima se sigue recolectando, solo no se muestra. El panorama permite descargar
el periodo en **Excel** (`reporte/excel.py`) con hojas de resumen, series
filtrables y diccionario; incluye formatos semánticos, panel congelado, tabla y
una gráfica de producción/exportaciones. El brief en PDF (`reporte/pdf.py`,
`generar_pdf_brief`) tiene tres páginas intencionales: panorama y variaciones;
producción/exportaciones/diferencia; cobertura, limitaciones y fuentes. Incluye
pie con autor y número de página; las gráficas usan matplotlib y la generación
mantiene `st.cache_data`.
**Compatibilidad Excel (2026-06-30):** la tabla `CommercialSeries` conserva su
autofiltro propio; no se añade además `ws.auto_filter` sobre el mismo rango.
Duplicar ambos filtros hacía que Excel reparara el archivo y eliminara
`table1.xml`. El libro corregido se abrió con Excel de escritorio en modo lectura
sin reparación y conservó sus tres hojas y la tabla.
El brief Markdown (`reporte.generar.generar`) se conserva como pieza testeada.
Producción y exportaciones forman un bloque mensual aparte (fecha real, barras
de ancho fijo, sin relleno semanal), con una tercera gráfica de producción menos
exportaciones para meses comparables. La diferencia no se presenta como
inventario. Periodos: 3 y 6 meses, 1 y 3 años, todo. Nombre del autor (Juan José
Jaramillo) al pie del sidebar y del pie de
página, con aviso `© 2026 ... Todos los derechos reservados` (`LICENSE`
propietario; repo público solo para portafolio, prohibido reutilizar). Tema
claro en `.streamlit/config.toml`; colores en `config.py`.
**Pulido visual (2026-06-25):** en `_layout` el título de los gráficos va
arriba-izquierda con margen superior amplio y la leyenda justo encima del área de
trazado, para que el título no se monte sobre las etiquetas (afecta a todos los
gráficos). Las unidades técnicas del contrato se traducen a etiquetas legibles
solo al mostrar (`UNIDADES_LEGIBLES`/`_unidad_legible`: `COP/carga_125kg`→
`COP/carga`, `USc/lb`→`US¢/lb`) en métricas, tabla de cobertura y hover comercial;
el contrato y los CSV no cambian. Los `subheader` (h3) pasaron de 1rem a 1,18rem
en negrita con más margen para marcar bloques. Para previsualizar local con el
servidor gestionado existe `.claude/launch.json` (config `streamlit`).
**Ejes mensuales adaptables (2026-06-30):** producción, exportaciones y su
diferencia ya no fuerzan una etiqueta por mes (`dtick="M1"`). Comparten
`configuracion_eje_mensual`, que limita a unas 12 marcas mediante una muestra
uniforme de fechas reales, mantiene las etiquetas horizontales y las ancla a
cada barra. Usa `tickmode="array"` para impedir marcas intermedias
que, al ocultar el día, duplicaban visualmente algunos meses. Corrige la
superposición observada en laptops a zoom 100 % sin ocultar barras ni datos.
Los periodos predefinidos filtran por cadencia: mercado conserva 13/26/52/156
semanas y cada serie mensual toma sus últimos 3/6/12/36 meses publicados desde
su propia fecha más reciente. Esto evita que el rezago mensual deje solo una o
cuatro barras. Las fechas personalizadas siguen siendo límites literales; Excel
y PDF reciben el mismo conjunto mixto mostrado en pantalla.
**Formato numérico según idioma.** `_numero(valor, decimales)` (antes
`_numero_es`) formatea según `IDIOMA`: español = miles `.` / decimal `,`; inglés
= miles `,` / decimal `.` (base de Python). En Plotly, `_layout` pone
`separators=",."` (es) o `".,"` (en), que cubre hover, ejes y barra de color de
**todas** las gráficas (pasan por `_layout`). Los strings preformateados que
`separators` no toca (etiquetas de barra del gráfico de resultado, porcentajes de
error de calibración, costo del `st.info`) usan `_numero`. **Límite asumido:** los
campos editables del simulador (`st.number_input` de Tasa, Costo y Coffee C)
**no** pueden mostrar separador de miles ni coma decimal —el `format` printf de
Streamlit se valida con `"%...f" % n` y rechaza la coma, y el decimal siempre es
punto—; se conservan así para no perder los botones +/− (decidido con el usuario).
Por eso Coffee C se ve `277.5` en el campo aunque el resto de la página respete el
idioma.
**Idioma EN (completo).** Interfaz bilingüe español/inglés: selector `Idioma /
Language` en la barra lateral fija `IDIOMA` ("es"/"en"); todo el texto visible
sale de `TEXTOS` vía `_t()`. Cubre cabecera, barra lateral, pestañas, panorama,
bloque producción/exportaciones, simulador completo, títulos/ejes/hover de las
gráficas y encabezados de tablas. Las etiquetas de datos en español de
`config.py` (indicadores, fuentes, alcance, cadencia, método) se traducen con
mapas de presentación en `app.py` (`ETIQUETAS_VAR_EN`, `DESCRIPCIONES_VAR_EN`,
`FUENTES_NOMBRE_EN`, `ALCANCE_EN`, `CADENCIA_EN`, `METODO_EN`, `PERIODOS_EN`) y
helpers (`_etiqueta_var`, `_descripcion_var`, `_metodo`, `_indicador_en`,
`_periodo_label`, `_carga_palabra`), **sin tocar el contrato ni los CSV**. Las
opciones que son clave de lógica (periodo, Mensual/Semanal, tipo de rango)
conservan su valor español y se muestran traducidas con `format_func`. Las tablas
de variaciones y cobertura **siguen generándose en español** porque también
alimentan el PDF; se traducen solo en pantalla con `_variaciones_para_pantalla` /
`_cobertura_para_pantalla` (la primera además formatea los % con
`_pct_con_signo`). **Quedan en español a propósito:** el brief PDF
(`reporte/pdf.py`) y el informe Markdown del simulador (`generar_informe_simulador`),
que son documentos descargables aparte; y los tres campos `st.number_input` del
simulador (límite de Streamlit). Las fechas se mantienen en dd/mm/aaaa en ambos
idiomas.
**Sigla FNC.** En el texto con espacio (introducción, captions, ayudas, pie,
metodología) se expande a "Federación Nacional de Cafeteros (FNC)" la primera vez
y luego "FNC". Se **conserva la sigla** en los espacios estrechos para no romper
el diseño: etiquetas de tarjetas (`Precio FNC estimado`, `Precio interno de
referencia FNC`), título y eje del mapa de sensibilidad y la categoría `Último FNC
observado`. La tabla de Fuentes ya mostraba el nombre completo. Verificado en
Preview (snapshot ok, sin errores de consola, maquetación intacta).
Las tres tarjetas de mercado tienen un control segmentado **Mensual/Semanal**
(`modo_comparacion_mercado`, predeterminado Mensual) que cambia la variación
mostrada: semanal = contra el cierre previo (un paso atrás, como antes); mensual =
contra el último cierre con fecha ≤ hace 28 días (`_variacion_comparacion`,
aproximación honesta a mes contra mes pese al punto de referencia diario al final
de la serie). Reemplaza a `_delta_pct`/"vs cierre semanal".
Panorama y simulador usan como referencia actual el mismo último trío coherente
FNC/Coffee C/TRM guardado en `calibracion_fnc.csv`; el panorama conserva además
el histórico semanal cerrado y distingue ambas fechas en el encabezado.

**Simulador.** Controles: Coffee C, USD/COP, costo, cargas y factor de
rendimiento (ref. 94 en `config.py`), todos con `key` en session_state
(prefijo `sim_`) y un botón "Restablecer valores predeterminados" (callback
`_restablecer_simulador` que limpia esas claves). El escenario se fija **solo con
los dos campos numéricos** (Coffee C y USD/COP). **Mapa de sensibilidad = solo
lectura (decidido 2026-06-25):** se intentó clic-para-seleccionar pero es inviable
con este stack y se descartó tras validarlo con el usuario. Por qué: Streamlit solo
propaga la selección de trazas *scatter* (no de heatmap), pero **cualquier scatter
alineado en columnas devuelve la X correcta y colapsa la Y a la fila superior**
(quirk de Plotly con X repetida, da igual densidad/tamaño de marcador) → síntoma
"X bien, Y siempre al tope". El heatmap sí mapea el clic correcto por geometría,
pero Streamlit no lo registra (clic real no seleccionaba). Estado final: se
quitaron `on_select`/`selection_mode`/`key`, la rejilla y el parser del clic; el
heatmap conserva su `hovertemplate` (hover con el precio `z` de cada celda) como
exploración, el marcador del escenario es la curva 1, y `_mantener_escenario_en_rango`
solo reajusta el escenario guardado al rango vigente. La matriz coloreada se alinea
al rango exacto de los controles. Las métricas margen-por-carga y margen-total muestran su ratio dentro
de la tarjeta con `delta` pero ocultan la flecha por CSS (contenedores
`st.container(key="metrica_margen_carga"/"metrica_margen_total")` → clases
`st-key-*`), porque un ratio no indica subida/bajada. Muestra precio
estimado, ingreso, costo, margen por carga/total, una cuenta (ingreso − costo
= margen) y la matriz. Botón para descargar un informe Markdown
(`generar_informe_simulador`). Costo inicial: 1.624.000 COP/carga 125 kg, FEPCafé
abril 2026 (editable). El estimador usa `TRM × Coffee C × coeficiente implícito`.
La calibración principal se guarda en `datos/historico/calibracion_fnc.csv` y el
workflow la actualiza desde la publicación diaria de la FNC; la calibración
estadística de respaldo se valida caminando sin datos futuros (MAE 26.376
COP/carga, MAPE 1,02%, últimas 300 observaciones). Con la referencia oficial del
25/06/2026 reproduce 2.160.000 COP para TRM 3.435,99 y Coffee C 276,40; aplicada
a los valores del 24/06/2026 estima 2.163.736 frente a 2.165.000 (error 1.264
COP, 0,06%). Los botones +/- del escenario se mueven en pasos legibles
(`PASO_FX=20` COP, `PASO_CAFE=2,5` US¢/lb); la tasa se muestra sin decimales
(`%.0f`) y el Coffee C con uno (`%.1f`). El default y `_mantener_escenario_en_rango`
ajustan al mismo paso.

**Validación última.** 59 pruebas unitarias; Streamlit headless con salud `ok`
sin excepciones; PDF e informe generados y revisados; factor de rendimiento
verificado (94 neutro, 90 → +4,4%, 100 → −6%); revisión de seguridad sin
hallazgos (sin eval/exec/subprocess/pickle; `unsafe_allow_html` solo con
contenido controlado; sin red en runtime; `.gitignore` cubre `.env`). URL local:
`http://localhost:8501`.

## Hallazgos que evitan retrabajo

- yfinance puede devolver `MultiIndex`; la normalización contempla `datos["Close"]`
  como `DataFrame`.
- El precio FNC usa puntos como miles; el parser convierte `$2.110.000`→`2110000`
  con banda de plausibilidad (evita leer `2.11`).
- El Excel FNC (desde la página de estadísticas) trae precio diario desde 2003 y
  producción mensual desde 1956; se filtran a 2023+ (producción hasta 2026-05).
- El Excel separado de exportaciones FNC trae volumen mensual desde 1958 en
  miles de sacos de 60 kg; se filtra a 2023+ (hasta 2026-05).
- GDELT puede dar `RateLimitError`; el fallback vacío funciona (estrategia
  alterna pendiente si se vuelve recurrente).
- PDF: no usar `plotly`+`kaleido` (kaleido 0.2.1 se cuelga con Plotly 6.8 en
  Python 3.13/Windows; v1 exige Chrome). Gráficas del brief con matplotlib.
- El PDF FNC por ciudad se descartó (frágil, poca diferencia con el nacional).
- Automatización (`actualizar-datos.yml`): el histórico es idempotente y hace
  merge, por eso el workflow refresca solo una ventana de 120 días (no desde
  2023). `procesar.visualizacion` recalcula indicadores en memoria desde
  `historico_semanal.csv`, así que basta versionar el histórico para que el app
  refresque; el push dispara el redespliegue de Streamlit. La app regenera el
  dataset visual ignorado por Git si el histórico es más reciente o contiene
  variables ausentes, evitando reutilizar derivados viejos entre despliegues.
  GitHub deshabilita los cron tras 60 días de inactividad del repo.
- Coordenadas climáticas = referencias municipales, no toda la variación interna.
- Simulador: fórmula = USD/COP escenario × Coffee C escenario × coeficiente
  implícito × (94 ÷ factor). El coeficiente principal se deriva del último trío
  publicado conjuntamente por la FNC y resume diferencial, conversiones y otros
  componentes no modelados. El FNC observado calibra el coeficiente, pero no
  funciona como piso; no es la fórmula oficial completa ni una predicción.

## Límites vigentes

- No iniciar score ni interpretación agronómica sin feedback e info experta
  (razones/preguntas en `BRIEFING_CHAT.md`).
- Commits entre unidades de trabajo validadas.
- No volver municipal el selector departamental sin ampliar antes la cobertura.

## Restricciones operativas

- El proxy del sandbox puede bloquear la red; validar fuentes reales puede
  requerir permisos.
- En Windows, `py_compile`/temporales pueden fallar al limpiar `__pycache__`/
  `%TEMP%`; validar sintaxis con `ast.parse`.
- Git puede requerir permisos para escribir en `.git`.

## Mantenimiento

Actualizar solo al cambiar estado, decisión, limitación, validación relevante o
próximo paso. Reemplazar lo obsoleto, no acumular. No copiar `CLAUDE.md` ni
volverla changelog (Git ya guarda el historial). Mantenerla corta.
