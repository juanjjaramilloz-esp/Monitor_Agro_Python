# Contexto entre IAs - Monitor Agro Colombia

Este archivo sirve como bitacora de continuidad para trabajar alternando entre
asistentes, IDEs y sesiones. Antes de retomar el proyecto, leer en este orden:

1. `CLAUDE.md` - reglas, fases y contratos del proyecto.
2. `CONTEXTO_IAS.md` - novedades, decisiones recientes y punto exacto de avance.
3. `git log --oneline -5` y `git status --short` - confirmar historial y arbol limpio.

Regla practica: cuando una IA o el usuario cierre una unidad de trabajo
validada, registrar aqui lo importante y hacer commit.

---

## Estado actual

Proyecto: monitor semanal de condiciones para la agroexportacion de cafe de
**Colombia**, comparando sus departamentos cafeteros entre si.

Fase actual: **Bloque 2 - backfill historico completado**. Existen series
diarias normalizadas y semanas comparables desde enero de 2023.

Siguiente paso recomendado: **Bloque 3 - indicadores utiles** (variaciones,
promedios moviles, tendencias y anomalias), antes de definir el score.

Commits relevantes:

- `3ef2d23` - Agregar modo historico a fuentes numericas.
- `9536939` - Agregar controles de calidad para snapshots.
- `53dfbf4` - Pivote a Colombia: retrofit geografico end-to-end.
- `8db29b7` - Fuente extra: `fuentes/precio_interno.py` (scraping FNC).
- `e47bd1c` - Fase 2: implementar `procesar/unir.py` y primer snapshot.
- `4791a62` - Fase 1d: implementar `fuentes/noticias.py` con GDELT.
- `e14bfad` - Fase 1c: implementar `fuentes/clima.py` con Open-Meteo.
- `cc08a46` - Fase 1b: implementar `fuentes/cafe.py` con yfinance.
- `6410d74` - Fase 1a: implementar `fuentes/fx.py` con yfinance.
- `d0767f0` - Fase 0: esqueleto y contratos base.

---

## Convenciones que no se deben romper

- Cada modulo en `fuentes/` expone una unica funcion publica `obtener()`.
- Las fuentes numericas devuelven exactamente:
  `fecha`, `geografia`, `variable`, `valor`, `unidad`, `fuente`.
- Noticias devuelve exactamente:
  `fecha`, `geografia`, `titulo`, `url`, `fuente`, `idioma`, `tono`, `categoria`.
- `geografia` tiene tres niveles: `GLOBAL` (cafe), `COLOMBIA` (FX, precio
  interno, noticias) y nombre de departamento cafetero (clima).
- Si una fuente falla, debe devolver un `DataFrame` vacio con columnas correctas.
- Todo parametro editable debe vivir en `config.py`.
- No mezclar fases en un mismo cambio.
- Hacer commits entre cambios validados para poder alternar entre asistentes.

---

## Hallazgos y decisiones tecnicas

### FX - Fase 1a

- Tras el pivote a Colombia, FX queda reducido a una sola fila USD/COP.
- Se usa `config.TICKER_FX = "USDCOP=X"` y `config.MONEDA = "COP"`.
- La salida usa `geografia = "COLOMBIA"`, variable `fx_usd_local`, unidad
  `COP/USD`, fuente `yfinance`.
- Frankfurter/BCE no cubre COP; por eso se usa yfinance.
- `yfinance` puede devolver columnas `MultiIndex`; para extraer cierre se usa
  `datos["Close"]` y, si es `DataFrame`, `iloc[:, 0]`.

### Cafe - Fase 1b

- Se usa `config.TICKER_CAFE_ARABICA = "KC=F"`.
- El precio del cafe es global, por eso `geografia = "GLOBAL"`.
- Variable: `precio_cafe_arabica`.
- Unidad: `USc/lb`.
- Fuente fragil: `yfinance` raspa Yahoo Finance y puede romperse.
- Ultima validacion real: `2026-06-18`, valor aproximado `256.10 USc/lb`.

### Clima - Fase 1c

- Se usa Open-Meteo con coordenadas de `config.REGIONES_CAFE`.
- Las regiones activas son 8 departamentos cafeteros: Huila, Antioquia,
  Tolima, Cauca, Narino, Caldas, Risaralda y Quindio.
- Variables configuradas:
  `temperature_2m_min`, `temperature_2m_max`, `precipitation_sum`.
- Mapeo de salida diario:
  `temp_min` (`grados C`), `temp_max` (`grados C`), `precipitacion` (`mm`).
- En la union semanal se agregan 4 variables por departamento:
  `precipitacion_semanal`, `temp_min_semanal`, `temp_max_semanal`,
  `temp_promedio_semanal`.

### Noticias - Fase 1d

- Se usa `gdeltdoc` con `GdeltDoc` y `Filters`.
- `gdeltdoc` esta en `requirements.txt` y fue instalado en `.venv`.
- Se agrego `NOTICIAS_MAX_REGISTROS = 25` en `config.py`.
- Tras el pivote, GDELT se consulta solo a nivel nacional con
  `config.PAIS_FIPS = "CO"` y `geografia = "COLOMBIA"`.
- Ultima validacion real devolvio `RateLimitError`; el fallback funciono y
  devolvio `DataFrame` vacio con columnas correctas.
- La normalizacion fue probada con un DataFrame artificial estilo GDELT:
  `seendate`, `title`, `url`, `language` -> contrato de noticias.
- `tono` queda como `NaN` float; `categoria` queda pendiente para fase posterior.

### Precio interno FNC - fuente extra (scraping)

- Modulo: `fuentes/precio_interno.py`. Variable `precio_interno_referencia`,
  `geografia = "COLOMBIA"`, unidad `COP/carga_125kg`, fuente `FNC`, `valor`
  entero.
- Fuente elegida: la **pagina de estadisticas cafeteras** de la FNC
  (`config.URL_PRECIO_INTERNO_FNC`), por estabilidad. Es WordPress/Elementor:
  el HTML lo entrega el servidor (no requiere JS). El precio esta en el menu de
  cabecera ("Precio interno de referencia: $X.XXX.XXX") y la fecha en un bloque
  "Fecha: AAAA-MM-DD".
- **Descartado el PDF de precios por ciudad**: agrega fragilidad (otro parseo,
  otro formato) y la diferencia frente al precio de referencia unico es minima
  para el objetivo del monitor. Anotado por si se quiere granularidad luego.
- **Excel historico** de la FNC: anotado como fuente futura para series de
  tiempo del precio interno; no se usa ahora (el monitor es puntual/semanal).
- Formato colombiano: "$2.110.000" -> el punto es separador de MILES. Se limpia
  quitando "$" y los puntos -> `2110000` (int). Bug clasico evitado: NO leerlo
  como float decimal (2.11). Se agrego una banda de plausibilidad
  (500.000-10.000.000) que ademas atrapa ese error de parseo.
- Dependencia nueva: `beautifulsoup4` (agregada a `requirements.txt` e instalada
  en `.venv`). Se usa `User-Agent` de navegador en la peticion.
- Misma fragilidad declarada que el cafe: si cambia la maquetacion, el modulo
  devuelve `DataFrame` vacio con columnas correctas (regla del contrato).
- Validacion real (`python -m fuentes.precio_interno`): 1 fila,
  `2026-06-18`, `2.110.000 COP/carga_125kg`.
- Para historico, el modulo descubre en la pagina FNC el Excel mas reciente de
  "Precios, area y produccion de cafe". La hoja diaria contiene datos desde
  2003; el backfill activo filtra desde 2023. Se usa `openpyxl` para leerla.

### Pivote a Colombia (retrofit geografico)

- Decision de producto: el monitor deja de comparar paises de LatAm y pasa a
  comparar los **departamentos cafeteros de Colombia** entre si. Mas honesto y
  accionable para el foco real (cafe colombiano).
- Paises LatAm retirados (Brasil, Peru, Honduras, Mexico): **recuperables en el
  historial de git**, no se borran del proyecto, solo de la config activa.
- `config.PAISES` -> reemplazado por `config.REGIONES_CAFE`: 8 departamentos
  (Huila, Antioquia, Tolima, Cauca, Narino, Caldas, Risaralda, Quindio), cada
  uno con un municipio cafetero representativo y su lat/lon para Open-Meteo.
- FX: se reduce a **solo USD/COP** (`config.TICKER_FX`, `config.MONEDA`). Se
  quitaron las otras cuatro monedas.
- Geografia nacional: `config.GEOGRAFIA_PAIS = "COLOMBIA"` y
  `config.PAIS_FIPS = "CO"` (GDELT).
- **Rename de columna `pais` -> `geografia`** en todas las fuentes numericas y
  en noticias, mas `procesar/unir.py` y docs. Motivo: la columna ahora mezcla
  tres niveles (GLOBAL / COLOMBIA / departamento); `pais` ya no describe bien.
- `precio_interno` **integrado a la union**: es una fila puntual de COLOMBIA, se
  trata igual que FX/cafe (rename `fecha`->`fecha_dato`, se le agrega
  `fecha_snapshot`).
- `noticias.py`: ahora consulta GDELT **solo a nivel nacional** (un solo query
  con `PAIS_FIPS`), no pais por pais.
- `precio_interno.py`: solo el rename de columna; la logica del scraper NO se
  toco.
- Validacion del flujo (`python -m procesar.unir`): **35 filas** = 1 cafe
  (GLOBAL) + 1 FX (COLOMBIA) + 1 precio interno (COLOMBIA) + 32 clima
  (8 departamentos x 4 variables). Snapshot regenerado:
  `datos/snapshots/snapshot_2026-06-21.csv`.

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
- Usuarios/beneficiarias potenciales reales: personas del ecosistema cafetero
  en Manizales/Caldas, incluyendo entorno profesional de CRECE, Gobernacion y
  Fundacion Manuel Mejia.
- El usuario quiere mantener el habito de commits entre cambios, sin importar
  que asistente hizo el trabajo.
- El usuario quiere que este archivo registre novedades, decisiones del chat,
  hallazgos y cualquier instruccion relevante para que otras IAs retomen bien.
- `BRIEFING_CHAT.md` se deja quieto por ahora; sirve para darle contexto a una
  IA web en un chat nuevo.
- Antes de hacer score, el usuario quiere revisar bien el proyecto y pensar
  mejoras/funciones que hagan el MVP mas completo.

---

## Preguntas abiertas / no asumir

- No definir todavia score final sin mas criterio del negocio cafetero.
- Si GDELT sigue con `RateLimitError`, falta decidir si se reintenta con otra
  estrategia o se complementa con otra fuente.

---

## Backfill historico - Bloque 2

- Modulo ejecutable: `python -m procesar.historico`.
- Rango inicial configurable: `2023-01-01` hasta hoy menos 5 dias por el retraso
  de disponibilidad del archivo climatico.
- Fuentes con `obtener(desde, hasta)`: USD/COP, cafe, clima y precio interno FNC.
- Semana comparable: lunes a domingo; semanas parciales se excluyen.
- Mercado y FNC: ultimo dato disponible de la semana.
- Clima: lluvia acumulada, minima, maxima y promedio de pares diarios.
- Persistencia idempotente: una nueva corrida reemplaza la misma clave, no la
  duplica.
- Archivos generados:
  `datos/historico/historico_diario.csv` y
  `datos/historico/historico_semanal.csv`.
- Validacion real: 33.368 filas diarias y 6.300 filas semanales.
- Cobertura: 180 semanas desde `2023-01-08` hasta `2026-06-14`; todas con 35
  indicadores, 8 departamentos climaticos, cero nulos y cero duplicados.

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

### Unir - Fase 2

- Esquema de salida: `fecha_snapshot`, `fecha_dato`, `geografia`, `variable`,
  `valor`, `unidad`, `fuente`.
- Decision de fechas: se mantienen dos columnas separadas.
  `fecha_snapshot` = hoy (parametrizable para pruebas).
  `fecha_dato` = fecha real del ultimo dato disponible segun la fuente.
  Motivo: las fuentes no comparten exactamente el mismo dia (yfinance devuelve
  el ultimo cierre disponible, Open-Meteo cierra el dia anterior), y ocultar
  esa diferencia seria deshonesto para un proyecto de portafolio.
- Clima: se agrega de diario a semanal con cuatro variables por departamento:
  `precipitacion_semanal` (suma), `temp_min_semanal` (min de minimas),
  `temp_max_semanal` (max de maximas), `temp_promedio_semanal` (media de
  puntos medios diarios). `fecha_dato` = dia mas reciente de la ventana.
- Primer snapshot validado: `datos/snapshots/snapshot_2026-06-21.csv`,
  35 filas = 1 cafe (GLOBAL) + 1 FX USD/COP (COLOMBIA) + 1 precio interno FNC
  (COLOMBIA) + 32 clima (8 departamentos x 4 variables).
- Ese primer snapshot es anterior a la capa de calidad: contiene un FX con
  `fecha_dato=2026-06-22`, posterior a `fecha_snapshot=2026-06-21`. Se conserva
  sin inventar ni cambiar datos; las corridas nuevas bloquean esa inconsistencia.
- Si una fuente devuelve vacio, la union omite esa parte sin romper.
- El reporte de calidad marca cada componente como `OK`, `VACIO`, `INCOMPLETO`
  o `FECHA_FUTURA`.
- La temperatura promedio semanal empareja minima y maxima por fecha.
- Un snapshot existente solo se reemplaza usando `sobrescribir=True`.
- Snapshot guardado como CSV (utf-8, sin indice): legible y diff-eable en git.
- Pruebas: `python -m unittest discover -s tests -v`.

---

## Proxima tarea sugerida

Implementar **Bloque 2 - backfill historico**:

- Disenar almacenamiento historico separado de los snapshots operativos.
- Obtener historico de cafe, USD/COP, clima y precio interno FNC.
- Crear semanas comparables sin etiquetar consultas actuales como historicas.
- Validar continuidad, cobertura y faltantes antes de calcular tendencias.
