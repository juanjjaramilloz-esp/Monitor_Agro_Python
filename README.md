# Monitor Agro Colombia

Monitor semanal de condiciones comerciales y climáticas que afectan al café
colombiano. Compara ocho departamentos cafeteros y conserva datos históricos
para analizar tendencias antes de construir un score.

## Estado actual

- Fuentes activas: USD/COP, café arábica internacional, precio interno FNC y
  clima de ocho departamentos.
- Histórico diario: 33.368 observaciones desde 2023.
- Histórico semanal: 180 semanas completas, con 35 indicadores por semana.
- Indicadores: cambios, promedios móviles, anomalías y comparación departamental.
- Preparación visual: etiquetas humanas, categorías, colores e índice base 100.
- Calidad: validaciones de fechas, nulos, duplicados, cobertura y semanas
  incompletas.
- Pendiente: criterios cafeteros, score, reporte y dashboard.

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

## Archivos de resultados

- `datos/historico/historico_diario.csv`: observaciones originales normalizadas.
- `datos/historico/historico_semanal.csv`: semanas comparables, listas para
  tendencias, gráficos y score.
- `datos/indicadores/indicadores_semanales.csv`: capa derivada completa.
- `datos/indicadores/resumen_ultima_semana.csv`: vista compacta de 35 filas.
- `datos/visualizacion/series_visualizacion.csv`: 6.300 filas listas para
  gráficos; es derivado y se regenera con el comando anterior.
- `datos/visualizacion/resumen_visual.csv`: última semana con metadatos.
- `datos/visualizacion/catalogo_variables.csv`: etiquetas, descripciones,
  colores y formatos de las siete variables.
- `datos/snapshots/`: fotografías de cada futura ejecución semanal.

La semana se cierra el domingo. Café, USD/COP y precio FNC usan el último dato
disponible de la semana. La lluvia se suma y las temperaturas se agregan a
mínimo, máximo y promedio.

## Cobertura geográfica

Huila, Antioquia, Tolima, Cauca, Nariño, Caldas, Risaralda y Quindío. El clima
de cada departamento usa por ahora una coordenada municipal representativa,
definida en `config.py`; no representa toda la variación interna departamental.
