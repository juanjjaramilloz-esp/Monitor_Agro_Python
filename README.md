# Monitor Agro Colombia

Monitor semanal de condiciones comerciales y climáticas que afectan al café
colombiano. Compara ocho departamentos cafeteros y conserva datos históricos
para analizar tendencias antes de construir un score.

## Estado actual

- Fuentes activas: USD/COP, café arábica internacional, precio interno FNC y
  clima de ocho departamentos.
- Histórico diario: 33.368 observaciones desde 2023.
- Histórico semanal: 180 semanas completas, con 35 indicadores por semana.
- Calidad: validaciones de fechas, nulos, duplicados, cobertura y semanas
  incompletas.
- Pendiente: indicadores de tendencia, score, reporte y dashboard.

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

## Archivos de resultados

- `datos/historico/historico_diario.csv`: observaciones originales normalizadas.
- `datos/historico/historico_semanal.csv`: semanas comparables, listas para
  tendencias, gráficos y score.
- `datos/snapshots/`: fotografías de cada futura ejecución semanal.

La semana se cierra el domingo. Café, USD/COP y precio FNC usan el último dato
disponible de la semana. La lluvia se suma y las temperaturas se agregan a
mínimo, máximo y promedio.

## Cobertura geográfica

Huila, Antioquia, Tolima, Cauca, Nariño, Caldas, Risaralda y Quindío. El clima
de cada departamento usa por ahora una coordenada municipal representativa,
definida en `config.py`; no representa toda la variación interna departamental.
