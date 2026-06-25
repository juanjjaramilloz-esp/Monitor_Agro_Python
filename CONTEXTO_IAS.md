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
- Única ampliación de datos confirmada: producción nacional mensual FNC (no
  departamental/municipal).
- Remoto `origin` en GitHub; app desplegada en Streamlit Community Cloud,
  verificada por el usuario. `ACERCA_DE.md` = guía para visitantes de la app
  pública; `README.md` = guía técnica local.
- Fase 6 (automatización) implementada: `.github/workflows/actualizar-datos.yml`
  refresca el histórico y hace commit/push cada 2 días (10:00 UTC +
  `workflow_dispatch`). Pendiente: validar la primera corrida real en el runner
  (las fuentes por scraping/yfinance pueden fallar allí; los pasos toleran error
  y solo commitea si hay cambios). Aún falta producir un snapshot semanal en CI.
- Próximo: lanzar la primera corrida manual del workflow y validar kit, brief y
  simulador con una tarea real de CRECE.

## Estado verificable

**Cobertura/calidad.** Pivote LatAm → 8 departamentos cafeteros completo.
Snapshot completo = 36 filas (3 comerciales semanales, 1 producción mensual, 32
clima). La unión conserva `fecha_snapshot` y `fecha_dato`. El snapshot inicial
`snapshot_2026-06-21.csv` tiene un FX fechado un día después; se conserva como
evidencia y las corridas nuevas bloquean esa inconsistencia.

**Histórico (`procesar/historico.py`).** Acepta rangos, excluye semanas
parciales, idempotente. Validado `2023-01-08`→`2026-06-14`: 180 semanas, 33.409
observaciones de fuente, 6.341 filas agregadas, sin nulos ni duplicados (41
filas extra = meses de producción 2023-01..2026-05, sin repetir en semanas).
Mercado y FNC usan el último dato semanal; producción conserva el mes publicado;
clima suma lluvia y agrega min/max/promedio.

**Indicadores/visual.** Ranking 1 = mayor valor numérico (no mejor/oportunidad/
menor riesgo). Derivados: 45.015 filas, rankings 1-8, sin duplicados. Visual:
6.341 filas para gráficos, 35 de resumen reciente, catálogo de 8 variables.

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
el periodo en CSV (fecha real, unidad, variaciones, fuente, alcance) y un brief
en PDF (`reporte/pdf.py`, `generar_pdf_brief`: dos gráficas comerciales,
variaciones, cobertura, limitaciones; gráficas con matplotlib, `st.cache_data`).
El brief Markdown (`reporte.generar.generar`) se conserva como pieza testeada.
Producción es un bloque mensual aparte (cambio mensual e interanual, fecha real,
barras de ancho fijo, sin relleno semanal). Periodos: 3 y 6 meses, 1 y 3 años,
todo. Nombre del autor (Juan José Jaramillo) al pie del sidebar y del pie de
página, con aviso `© 2026 ... Todos los derechos reservados` (`LICENSE`
propietario; repo público solo para portafolio, prohibido reutilizar). Tema
claro en `.streamlit/config.toml`; colores en `config.py`.

**Simulador.** Controles: Coffee C, USD/COP, costo, cargas y factor de
rendimiento (ref. 94 en `config.py`), todos con `key` en session_state
(prefijo `sim_`) y un botón "Restablecer valores predeterminados" (callback
`_restablecer_simulador` que limpia esas claves). El escenario se fija con
entradas numéricas o haciendo clic en el mapa de sensibilidad: el Heatmap no emite eventos
de clic, así que se superpone una rejilla fina e invisible (Scatter 45×45, capa
"celdas") y con `hovermode="closest"` + `on_select="rerun"` un clic elige el punto
más cercano (al ser densa, queda casi donde se hizo clic). El parser descarta la
curva del marcador del escenario. La matriz coloreada se alinea al rango exacto
de los controles y el heatmap conserva el hover de precios. Muestra precio
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
COP, 0,06%). TRM y Coffee C aceptan dos decimales.

**Validación última.** 46 pruebas unitarias; Streamlit headless con salud `ok`
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
- GDELT puede dar `RateLimitError`; el fallback vacío funciona (estrategia
  alterna pendiente si se vuelve recurrente).
- PDF: no usar `plotly`+`kaleido` (kaleido 0.2.1 se cuelga con Plotly 6.8 en
  Python 3.13/Windows; v1 exige Chrome). Gráficas del brief con matplotlib.
- El PDF FNC por ciudad se descartó (frágil, poca diferencia con el nacional).
- Automatización (`actualizar-datos.yml`): el histórico es idempotente y hace
  merge, por eso el workflow refresca solo una ventana de 120 días (no desde
  2023). `procesar.visualizacion` recalcula indicadores en memoria desde
  `historico_semanal.csv`, así que basta versionar el histórico para que el app
  refresque; el push dispara el redespliegue de Streamlit. GitHub deshabilita
  los cron tras 60 días de inactividad del repo.
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
