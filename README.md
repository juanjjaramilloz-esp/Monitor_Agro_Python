# Monitor Agro Colombia

Monitor semanal de condiciones comerciales y climáticas que afectan al café
colombiano. Compara ocho departamentos cafeteros y conserva datos históricos
para analizar tendencias antes de construir un score.

## Estado actual

- Fuentes activas: USD/COP, café arábica internacional, precio interno FNC,
  producción nacional mensual y clima de ocho departamentos.
- Histórico diario: 33.409 observaciones desde 2023.
- Histórico agregado: 180 semanas completas para mercado y clima, más 41
  observaciones mensuales de producción.
- Indicadores: cambios, promedios móviles, anomalías y comparación departamental.
- Preparación visual: etiquetas humanas, categorías, colores e índice base 100.
- Dashboard publicado: panorama comercial, producción mensual y detalle
  climático departamental.
- Kit de consulta: filtros por periodo, descarga comercial en CSV y brief
  ejecutivo en PDF con las gráficas (matplotlib + reportlab).
- Simulador de escenarios: controles para Coffee C, USD/COP, precio FNC base,
  costo por carga, volumen y factor de rendimiento, con margen bruto, mapa de
  sensibilidad clicable, botón para restablecer e informe del escenario
  descargable en Markdown.
- Automatización: GitHub Actions cada 2 días (`.github/workflows/actualizar-datos.yml`)
  que refresca el histórico y hace commit/push; el push redespliega la app.
- Calidad: validaciones de fechas, nulos, duplicados, cobertura y semanas
  incompletas.
- Pendiente: validar el kit con una tarea real de CRECE y definir criterios
  expertos antes de construir el score.

## Cómo probarlo

Abre PowerShell en `E:\Monitor_Agro_Python` y ejecuta:

```powershell
.\.venv\Scripts\Activate.ps1
python main.py
```

Para comprobar la lógica sin depender de internet:

```powershell
python -m unittest discover -s tests -v
```

## Cómo actualizar el histórico

La configuración predeterminada descarga desde el 1 de enero de 2023:

```powershell
python -m procesar.historico
```

También puedes elegir un rango:

```powershell
python -m procesar.historico --desde 2025-01-01 --hasta 2025-12-31
```

El proceso es idempotente: repetir un rango actualiza los registros existentes
sin duplicarlos.

## Cómo calcular indicadores

Después de actualizar el histórico, ejecuta:

```powershell
python -m procesar.indicadores
```

La terminal muestra la última semana para Caldas, Colombia y el mercado global.
Los rankings ordenan de mayor a menor valor numérico; no significan todavía
"mejor" o "peor".

## Cómo preparar datos para gráficos

```powershell
python -m procesar.visualizacion
```

Este paso agrega etiquetas legibles, orden estable, municipio de referencia,
colores y escalas comparables. No genera score ni interpreta riesgo.

## Cómo abrir las visualizaciones

```powershell
streamlit run app.py
```

Luego abre `http://localhost:8501`. El tablero tiene tres vistas (la de entrada
es `Panorama nacional`):

- `Panorama nacional`: café, USD/COP y precio interno en una escala base 100,
  producción nacional mensual, descarga de series en CSV y brief del periodo en
  PDF con las gráficas.
- `Simulador`: escenarios de precio interno y margen al modificar Coffee C,
  USD/COP, costo medio, número de cargas y factor de rendimiento; el escenario se
  fija con los controles o clicando el mapa de sensibilidad, con botón de
  restablecer e informe del escenario descargable.
- `Climatología cafetera`: lluvia y temperaturas de la referencia municipal del
  departamento elegido en el panel izquierdo.

Esta es una versión para feedback. El simulador no es un pronóstico y el
tablero no contiene score ni semáforos de riesgo.

## Actualización automática

`.github/workflows/actualizar-datos.yml` corre en GitHub Actions cada 2 días
(10:00 UTC) y también a mano (`workflow_dispatch`). Refresca una ventana reciente
del histórico de forma idempotente, recalcula indicadores y visualización, y hace
commit/push solo si hay datos nuevos. Ese push redespliega la app en Streamlit
Community Cloud, así que los datos se actualizan sin intervención. Los pasos de
datos toleran fallos puntuales de las fuentes (scraping/yfinance).

## Archivos de resultados

- `datos/historico/historico_diario.csv`: observaciones originales normalizadas.
- `datos/historico/historico_semanal.csv`: semanas comparables, listas para
  tendencias y gráficos; la producción conserva únicamente sus meses
  publicados.
- `datos/indicadores/indicadores_semanales.csv`: capa derivada completa.
- `datos/indicadores/resumen_ultima_semana.csv`: vista compacta de la última
  semana disponible.
- `datos/visualizacion/series_visualizacion.csv`: 6.341 filas listas para
  gráficos; es derivado y se regenera con el comando anterior.
- `datos/visualizacion/resumen_visual.csv`: última semana con metadatos.
- `datos/visualizacion/catalogo_variables.csv`: etiquetas, descripciones,
  colores y formatos de las ocho variables.
- `datos/snapshots/`: fotografías archivadas de las ejecuciones semanales.

La semana se cierra el domingo. Café, USD/COP y precio FNC usan el último dato
disponible de la semana. La lluvia se suma y las temperaturas se agregan a
mínimo, máximo y promedio.

## Cobertura geográfica

Huila, Antioquia, Tolima, Cauca, Nariño, Caldas, Risaralda y Quindío. El clima
de cada departamento usa por ahora una coordenada municipal representativa,
definida en `config.py`; no representa toda la variación interna departamental.

## Licencia

© 2026 Juan José Jaramillo. **Todos los derechos reservados.**

Este repositorio es público solo con fines de evaluación y muestra de
portafolio. No se permite copiar, modificar, reutilizar ni redistribuir el
código sin autorización previa y por escrito del autor. Ver [LICENSE](LICENSE).
