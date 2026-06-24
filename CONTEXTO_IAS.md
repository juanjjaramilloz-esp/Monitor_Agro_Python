# Continuidad técnica — Monitor Agro Colombia

Bitácora operativa para asistentes con acceso al repo. Solo estado y hallazgos
que no conviene reconstruir. Contrato técnico estable: `CLAUDE.md`. Estrategia:
`BRIEFING_CHAT.md`.

**Cómo retomar:** leer `CLAUDE.md` y este archivo; correr `git status --short` y
`git log --oneline -8`; verificar con código/pruebas cualquier dato operativo.
`BRIEFING_CHAT.md` solo si la tarea depende de audiencia o producto.

## Punto de control (2026-06-24)

- MVP descriptivo completo: fuentes, calidad, histórico desde 2023, indicadores
  neutrales, preparación visual, dashboard y brief del periodo en PDF con gráficas.
- Prioridad (feedback CRECE): convertir el panorama comercial en herramienta
  reutilizable para investigación/informes/reuniones. La capa climática se
  conserva pero no se amplía. Score y conocimiento experto siguen pausados.
- Simulador separado del score: desplaza el último precio FNC proporcional a
  Coffee C × USD/COP, ajusta por factor de rendimiento (aprox.), edita costo por
  carga y calcula margen bruto. No modela prima, calidad, pasilla, logística,
  impuestos ni causalidad.
- Única ampliación de datos confirmada: producción nacional mensual FNC (no
  departamental/municipal).
- Remoto `origin` en GitHub; app desplegada en Streamlit Community Cloud,
  verificada por el usuario. `ACERCA_DE.md` = guía para visitantes de la app
  pública; `README.md` = guía técnica local.
- Próximo: validar kit, brief y simulador con una tarea real de CRECE antes de
  ampliar datos o formatos.

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

**Dashboard (3 pestañas).** Orden: `Panorama nacional` (entrada por defecto),
`Simulador` y `Climatología cafetera` (detalle climático del departamento; antes
se llamaba con el nombre del departamento·municipio). La pestaña `Comparación` se
retiró (recuperable en git). El panorama no cambia al elegir departamento (series
global/nacional);
permite descargar el periodo en CSV (fecha real, unidad, variaciones, fuente,
alcance) y un brief en PDF (`reporte/pdf.py`, `generar_pdf_brief`: dos gráficas,
variaciones, cobertura, limitaciones; gráficas con matplotlib, `st.cache_data`,
descarga en un clic). El brief Markdown (`reporte.generar.generar`) se conserva
como pieza testeada. Producción es un bloque mensual aparte (cambio mensual e
interanual, fecha real, barras de ancho fijo, sin relleno semanal). Periodos: 3
y 6 meses, 1 y 3 años, todo. Al cambiar departamento se activa su pestaña con su
municipio; no hay selector municipal (una coordenada por departamento). Nombre
del autor (Juan José Jaramillo) al pie del sidebar y del pie de página. Tema
claro en `.streamlit/config.toml`; colores en `config.py`.

**Simulador.** Controles: Coffee C, USD/COP, precio FNC base, costo, cargas y
factor de rendimiento (ref. 94 en `config.py`), todos con `key` en session_state
(prefijo `sim_`) y un botón "Restablecer valores predeterminados" (callback
`_restablecer_simulador` que limpia esas claves). El escenario se fija con
sliders o haciendo clic en el mapa de sensibilidad: el Heatmap no emite eventos
de clic, así que se superpone un Scatter transparente (capa "celdas") y con
`hovermode="closest"` + `on_select="rerun"` un clic elige el punto de grilla más
cercano; la matriz se alinea al rango exacto de los sliders. Muestra precio
proyectado, ingreso, costo, margen por carga/total, una cuenta (ingreso − costo
= margen) y la matriz. Botón para descargar un informe Markdown
(`generar_informe_simulador`). Costo inicial: 1.624.000 COP/carga 125 kg, FEPCafé
abril 2026 (editable).

**Validación última.** 39 pruebas unitarias; Streamlit headless con salud `ok`
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
- Coordenadas climáticas = referencias municipales, no toda la variación interna.
- Simulador: transmisión proporcional anclada al FNC observado; fórmula = FNC
  base × (USD/COP esc ÷ base) × (Coffee C esc ÷ base) × (94 ÷ factor); no es la
  fórmula oficial ni una predicción.

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
