# Continuidad técnica — Pulso Cafetero (Monitor Agro Colombia)

> **Documento interno de trabajo.** Bitácora de desarrollo asistido; no es
> documentación del producto. Para conocer el proyecto ver `README.md` y
> `ACERCA_DE.md` en la raíz.

Bitácora operativa para asistentes con acceso al repo. Solo estado y hallazgos
que no conviene reconstruir. Contrato técnico estable: `CLAUDE.md`. Estrategia:
`BRIEFING_CHAT.md`.

**Cómo retomar:** leer `CLAUDE.md` y este archivo; correr `git status --short` y
`git log --oneline -8`; verificar con código/pruebas cualquier dato operativo.
`BRIEFING_CHAT.md` solo si la tarea depende de audiencia o producto.

## Punto de control (2026-06-30)

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
  `docs/internal/GUIA_PORTAFOLIO.md` contiene entrevista, autorización, textos para CV y
  LinkedIn y guion audiovisual. Las capturas del README ya existen
  (`docs/img/panorama.png` y `docs/img/simulador.png`, tomadas el 03/07 con
  Playwright + Chrome a 1440px, `--client.toolbarMode viewer` para ocultar el
  botón Deploy); sigue pendiente el video/GIF, que debe grabarse a mano.
- El rediseño visual integral probado el 30/06 fue revertido por solicitud del
  usuario tras un fallo de importación en Streamlit Cloud. La app conserva la
  interfaz anterior y todas las mejoras funcionales previas: filtros mensuales,
  ejes sin etiquetas duplicadas y descargables Excel/PDF. No describir como
  vigentes la portada compacta, la gráfica mensual integrada ni los supuestos
  avanzados plegables del experimento revertido.
- **Auditoría y pulido visual (2026-06-30, post-revert).** Mejoras solo-CSS en
  `_estilos()` (`app.py`), sin tocar imports, `procesar/*` ni el contrato de
  datos, para no repetir el fallo de importación del rediseño revertido: h1
  con más peso y `letter-spacing`; breakpoint intermedio (1024px) entre el
  ancho fijo del `block-container` y el móvil (768px); tabs con borde inferior
  de acento en la pestaña activa y hover en las inactivas; `st.info`/alertas y
  `st.dataframe` estilizados con el mismo lenguaje visual de tarjeta (borde,
  radio, acento) que las métricas y gráficas; hover de acento en los títulos
  de `st.expander`. Verificado con `python -c "import app"` (sin excepciones)
  y las pruebas unitarias de entonces (hoy 69, OK).
- **Robustez tras auditoría de código (2026-06-30).** Correcciones quirúrgicas,
  sin dependencias nuevas ni cambios de contrato: (1) las tarjetas de mercado
  ya no lanzan `IndexError` cuando la referencia viene del respaldo diario y
  las series no comparten fecha máxima (caen a la última fila de cada serie);
  (2) `referencia_mercado_fnc` valida bandas de plausibilidad por variable y
  descarta el trío completo si un valor sale de rango (p. ej. un cambio a
  formato numérico estadounidense en la página), con prueba unitaria nueva
  (60 en total); (3) `_leer_series` crea vacías las columnas numéricas
  ausentes en CSV derivados de versiones anteriores; (4) la caché del brief
  PDF también se invalida al cambiar `calibracion_fnc.csv`; (5) el workflow
  tiene `timeout-minutes: 20` y hace `git pull --rebase` antes del push;
  (6) `.gitignore` cubre `outputs/`.
- **Descarga FNC compartida (2026-07-02).** Nuevo `fuentes/_fnc_comun.py`:
  caché por proceso de la página de estadísticas y de los Excel FNC
  (`descargar_texto`/`descargar_binario`/`limpiar_cache`). Las cuatro fuentes
  FNC (precio_interno, produccion, exportaciones, referencia_mercado_fnc) lo
  usan; antes cada corrida pedía la misma página hasta 4 veces y el mismo
  Excel 2 veces (riesgo de WAF). Las descargas fallidas no se cachean y el
  contrato no cambió. Los tests que mockeaban `requests` por módulo ahora
  parchean `fuentes._fnc_comun.requests.get` y limpian la caché en `setUp`.
- **Brief PDF bilingüe (2026-07-02).** Ver bloque "Idioma EN". Prueba
  unitaria nueva del PDF en inglés (61 pruebas en total). Verificado
  extrayendo el texto de PDFs de muestra en ambos idiomas (títulos,
  indicadores, fuentes, unidades y pie traducidos; el ES quedó idéntico).
- **Higiene tras auditoría (2026-07-03).** Seis mejoras de calidad sin
  cambios visibles ni de contrato (69 pruebas OK, import 3.13 y 3.14):
  (1) `fuentes/_fnc_comun.py` gana `buscar_url_excel(sopa, patron)` y
  `buscar_hoja(nombres, prefijo)` (normaliza tildes/mayúsculas); las cuatro
  fuentes FNC dejan de duplicar la búsqueda de URL y unifican el matching de
  hojas (antes cada una comparaba distinto). (2) Parámetros a `config.py`:
  `PROYECCION_PASO_FX/CAFE`, `PRECIO_INTERNO_MIN/MAX`, `BANDAS_PLAUSIBLES_FNC`
  (antes "quemados" en app.py, precio_interno y referencia_mercado_fnc).
  (3) Formato numérico único en `reporte/formato.py` (`numero`), usado por
  `reporte/pdf.py` y `reporte/generar.py`; el `_numero` de app.py se deja
  intacto a propósito (usa el global IDIOMA). (4) `_agregar_puntuales`
  (historico) vectorizado con groupby.agg. (5) Pruebas nuevas: helpers
  `_fnc_comun`, `noticias._normalizar_articulos` y
  `calibracion_fnc.guardar` (merge idempotente). Nada queda pendiente de la
  auditoría de código.
- **Optimización para LinkedIn (2026-07-03, pedido del usuario).** (1) Marca
  nueva: la app se llama **"Pulso Cafetero"** (EN "Coffee Pulse"), subtítulo
  "Consultas, reportes y simulación del café colombiano"; renombrados
  page_title, TEXTOS, títulos/pie del PDF, títulos del Excel y del brief/
  informe Markdown, y los nombres de archivo descargables
  (`brief_pulso_cafetero_*`…); el repo y la URL no cambian. (2) Docs internos
  movidos a `docs/internal/` (CONTEXTO_IAS, BRIEFING_CHAT, GUIA_PORTAFOLIO)
  con encabezado de "documento interno"; CLAUDE.md §0 y §9 apuntan a las
  rutas nuevas. (3) Nuevo workflow `.github/workflows/pruebas.yml` (unittest
  en push/PR) con badge en el README. (4) README renovado: badges, resumen en
  inglés, cifras corregidas (69 pruebas, conteos no congelados), features
  nuevas (intradía, PDF bilingüe), instalación reproducible con git clone,
  sección "Vistazo" con capturas en `docs/img/`. (5) GUIA con las 3 preguntas
  clave para la reseña de CRECE.

- **Cambio de etapa (2026-07-06, pedido del usuario).** El MVP se declara
  terminado; `CLAUDE.md` fue reescrito (queda local, está en `.gitignore`):
  las fases dan paso a **mejora continua orientada a portafolio** con criterio
  costo/beneficio y libertad creativa, sujeta a invariantes (no romper la app
  desplegada, contrato de fuentes, honestidad de datos, config centralizada,
  bilingüismo, secretos). Regla nueva de docs: el README se actualiza siempre
  que un cambio altere lo que afirma; los demás siguen bajo petición.
- **Primera tanda de mejoras (2026-07-06).** (1) Linting con **ruff**
  (E/W/F/B/UP/I, config en `pyproject.toml`, `requirements-dev.txt`, job
  `lint` en `pruebas.yml`); se corrigieron los 42 hallazgos (imports, orden,
  `zip(strict=...)`, cierres sobre variables de bucle ligados por argumento)
  sin cambios de comportamiento. (2) **Descarga CSV** de la tabla comercial
  del periodo junto al Excel (`_a_csv`, UTF-8 BOM, fechas AAAA-MM-DD,
  contrato en español estable entre idiomas); README al día. Validación de
  ambas: lint limpio, `import app` OK, 69 pruebas OK.
- **Snapshot semanal en CI (2026-07-06), cierra el pendiente de Fase 6.**
  `procesar.unir.unir()` vuelve a golpear las fuentes en vivo (no lee el
  histórico ya actualizado), incluida la página FNC que la misma corrida ya
  consulta dos veces (`historico` + `calibracion_fnc`); y como identifica el
  snapshot por fecha exacta del día, correrlo en cada ejecución (~15/mes)
  generaría un archivo casi cada 2 días, no uno semanal. Se añadió un paso
  nuevo en `actualizar-datos.yml` que solo invoca `python -m procesar.unir`
  si `datos/snapshots/` no tiene ya un snapshot fechado dentro de la semana
  ISO en curso (lunes–hoy, comparación lexicográfica de nombres
  `snapshot_AAAA-MM-DD.csv`, verificada con 4 casos límite en bash local:
  vacío, semana pasada, hoy, lunes exacto). `continue-on-error: true` como
  el resto de pasos de datos; el commit ya incluía `datos/` completo, sin
  cambios ahí. Queda pendiente observar en un run real si la tercera
  consulta semanal a la FNC es tolerada por su WAF.
- **Criterio de priorización corregido (2026-07-06, pedido del usuario):**
  dejar de priorizar backend/infra/solidez (eso ya está bien); priorizar
  mejoras que quien **usa la app** note de inmediato — y por consecuencia el
  reclutador que la abra. Registrado también en la memoria del asistente.
- **Tanda de mejoras visibles (2026-07-06).** Tres features nuevas en la app,
  bilingües, validadas con lint + 69 pruebas + `import app` con datos reales:
  (1) **Lectura rápida del periodo** (panorama, bajo la gráfica base 100):
  frases autogeneradas con cierre/variación/máx/mín con fechas de las tres
  series y el último mes de producción vs. exportaciones (comparadas solo si
  es el mismo mes), listas para copiar en informes; lenguaje descriptivo.
  (2) **Correlación móvil** FNC↔Coffee C y FNC↔USD/COP (panorama, tras la
  tabla de variaciones): Pearson sobre variaciones semanales, ventana de 26
  semanas (`CORRELACION_VENTANA_SEMANAS` en config), calculada en todo el
  histórico y mostrada en el periodo elegido; con datos reales da 0,86–0,96
  contra Coffee C y −0,33–0,07 contra USD/COP (último año). (3)
  **Equivalencias del precio estimado** en el simulador: COP/kg y COP/arroba
  (`CARGA_KG`, `ARROBAS_POR_CARGA`), marcadas como aritmética. README al día.
- **Comentario del periodo con IA — Versión A implementada (2026-07-06).**
  Nuevo `reporte/comentario_ia.py`: construye un contexto de cifras exactas
  desde `historico_semanal.csv` (cierre/variación/máx/mín de las 3 series de
  mercado en `COMENTARIO_IA_SEMANAS`=4 semanas, último mes de producción y
  exportaciones con variación mensual/interanual, correlaciones de 26 semanas)
  y llama a Claude (`claude-opus-4-8`, salida estructurada JSON con
  `comentario_es`/`comentario_en`; el prompt prohíbe predecir/recomendar y
  citar cifras no entregadas). El resultado se versiona en
  `datos/comentario/comentario_periodo.json` con fecha y modelo. Paso nuevo en
  `actualizar-datos.yml` (`continue-on-error`, secret `ANTHROPIC_API_KEY`);
  la app **no** hace llamadas de IA en runtime: `cargar()` lee el JSON y el
  Panorama lo muestra tras la correlación con caption de trazabilidad
  bilingüe (si el archivo no existe, el bloque no aparece). `anthropic==0.116.0`
  pinneado en requirements. 7 pruebas nuevas con cliente mockeado (76 en
  total), ruff limpio, `import app` OK. **Pendiente del usuario:** crear la
  API key en console.anthropic.com y guardarla como secret `ANTHROPIC_API_KEY`
  del repo; el primer comentario real aparecerá tras la siguiente corrida del
  workflow (se puede disparar a mano con `workflow_dispatch`). Evolución
  futura posible: incluir el comentario en el brief PDF y la Versión B (chat).
  **Iteración por feedback del usuario (2026-07-06):** el primer comentario
  real solo repetía cifras visibles en el tablero y citaba un USD/COP
  "desactualizado" (el cierre semanal, días más viejo que la tarjeta en vivo).
  Dos correcciones: (1) el prompt ahora exige **cruzar** series (compensación
  dólar↔Coffee C, comparar los dos coeficientes de correlación, contrastar
  mensuales con mercado solo si el mes coincide) en vez de resumir cada una;
  (2) el contexto incluye `referencia_diaria` desde `calibracion_fnc.csv`
  (trío oficial FNC del día, con brecha % frente al cierre semanal por serie)
  y el prompt ancla los niveles "actuales" ahí, usando las semanas cerradas
  solo como trayectoria. `construir_contexto(historico, calibracion=None)`
  mantiene compatibilidad. Caption de la app actualizado. 78 pruebas OK.
- **Cadencia diaria de la automatización (2026-07-06, pedido del usuario).**
  El cron de `actualizar-datos.yml` pasó de cada 2 días a **lunes a viernes**
  (`"0 10 * * 1-5"`) para que `calibracion_fnc.csv` (el trío oficial FNC) se
  actualice el mismo día hábil en que la FNC lo publica, en vez de quedar
  hasta 2 días atrás como pasaba con el comentario de IA. README, ACERCA_DE y
  CLAUDE.md (local) actualizados; nombre del workflow y mensaje de commit ya
  no dicen "cada 2 días". Estimado de llamadas a Claude sube de ~15 a ~20/mes
  (sigue siendo trivial en costo). **Riesgo a vigilar:** la página de
  estadísticas FNC se consultará ~5 veces/semana en vez de ~3-4; si el WAF de
  la FNC empieza a bloquear, el síntoma sería `referencia_diaria` ausente del
  comentario y `calibracion_fnc.csv` sin fila nueva pese a la corrida — no
  hay retroceso automático, habría que volver a cron cada 2 días si ocurre.
- **Backlog priorizado costo/beneficio (2026-07-06, reordenado al criterio
  "visible para el usuario"):** (a) escenarios comparables/guardables en el
  simulador (A vs B); (b) incluir la lectura rápida y la correlación en el
  brief PDF; (c) GIF demo del README (manual, requiere al usuario); (d)
  medir cobertura de pruebas en CI (baja prioridad bajo el nuevo criterio).
  El score sigue pausado.

## Estado verificable

**Cobertura/calidad.** Pivote LatAm → 8 departamentos cafeteros completo.
Snapshot completo = 37 filas (3 comerciales semanales, 2 series mensuales, 32
clima). La unión conserva `fecha_snapshot` y `fecha_dato`. El snapshot inicial
`snapshot_2026-06-21.csv` tiene un FX fechado un día después; se conserva como
evidencia y las corridas nuevas bloquean esa inconsistencia.

**Histórico (`procesar/historico.py`).** Acepta rangos, excluye semanas
parciales, idempotente. Estado al 30/06: mercado y clima llegan de
`2023-01-08`→`2026-06-21` (181 semanas cerradas), con 33.610 observaciones de
fuente y 6.409 filas agregadas (41 meses de producción y 41 de
exportaciones, 2023-01..2026-05, sin repetir en semanas). Mercado y FNC usan el
último dato semanal; las series mensuales conservan el mes publicado; clima suma
lluvia y agrega min/max/promedio.

**Indicadores/visual.** Ranking 1 = mayor valor numérico (no mejor/oportunidad/
menor riesgo). Indicadores versionados: 45.084 filas, rankings 1-8, sin
duplicados. Visual regenerado desde el histórico: 6.409 filas para gráficos,
27 de resumen reciente y catálogo de 9 variables.

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
`_pct_con_signo`). **El brief PDF es bilingüe desde 2026-07-02:**
`generar_pdf_brief(..., idioma)` traduce títulos, secciones, gráficas, tablas,
lecturas neutrales y pie con `_TEXTOS`/mapas propios de `reporte/pdf.py`
(espejo de los de `app.py`; no importa `app.py` para no depender de
Streamlit); las tablas de variaciones y cobertura le siguen llegando en
español y el PDF las traduce él mismo. `_brief_pdf` recibe `IDIOMA` como
argumento para que la caché distinga idiomas. **Quedan en español a
propósito:** el informe Markdown del simulador (`generar_informe_simulador`)
y los tres campos `st.number_input` del simulador (límite de Streamlit). Las
fechas se mantienen en dd/mm/aaaa en ambos idiomas.
**Sigla FNC.** En el texto con espacio (introducción, captions, ayudas, pie,
metodología) se expande a "Federación Nacional de Cafeteros (FNC)" la primera vez
y luego "FNC". Se **conserva la sigla** en los espacios estrechos para no romper
el diseño: etiquetas de tarjetas (`Precio FNC estimado`, `Precio interno de
referencia FNC`), título y eje del mapa de sensibilidad y la categoría `Último FNC
observado`. La tabla de Fuentes ya mostraba el nombre completo. Verificado en
Preview (snapshot ok, sin errores de consola, maquetación intacta).
**Precio de mercado actual en tarjetas (2026-07-02, pedido del usuario).**
Las tarjetas de USD/COP y Coffee C muestran el último precio de mercado de
Yahoo (~15 min de retraso) cuando `_precios_intradia()` lo consigue
(`st.cache_data(ttl=300)`, `history(period="1d", interval="1m")`): se
reemplaza el valor mostrado y el último punto de la serie local para que
valor, variación y minigráfico cuenten lo mismo; si Yahoo falla, las
tarjetas vuelven solas al comportamiento anterior (trío FNC). Un caption
debajo detalla precio y fecha/hora Colombia de cada dato y aclara que fuera
de horario bursátil es el cierre de la sesión (Coffee C cierra ~12:30
Colombia). **La tarjeta FNC, el simulador, el histórico y los snapshots
conservan el trío oficial FNC** — esto matiza la decisión de "coherencia
entre vistas": el panorama prioriza el mercado vivo y el simulador la
referencia oficial. Es la única llamada de red en runtime de la app y
degrada en silencio. Nota diagnóstica: tras un deploy, Streamlit Cloud puede
recargar `app.py` sin reimportar módulos ya cargados (TypeError por firma
vieja en `reporte/pdf.py`); se corrige con Manage app → Reboot.
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

**Validación última.** Tras revertir el rediseño: las pruebas unitarias (hoy 69) y la
importación completa de `app.py` pasan; el endpoint público responde HTTP 200.
La versión restaurada ya había pasado Streamlit headless con salud `ok` sin
excepciones; PDF e informe fueron generados y revisados; factor de rendimiento
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
