# Acerca de Monitor Agro Colombia

Esta página reúne, en un solo lugar, las **condiciones de mercado y clima que
afectan al café colombiano**. Está pensada para apoyar análisis, informes y
reuniones del sector cafetero: integra varias fuentes oficiales y públicas, las
deja limpias y comparables, y permite consultarlas, graficarlas y exportarlas
sin tener que buscarlas y depurarlas una por una.

No necesita instalar nada. Todo funciona desde el navegador.

---

## Qué puede hacer aquí

- **Ver la evolución comercial** del café en una sola escala comparable: precio
  internacional (ICE Coffee C), tasa de cambio USD/COP y precio interno de
  referencia de la Federación Nacional de Cafeteros (FNC).
- **Consultar la producción nacional mensual** registrada por la FNC.
- **Consultar el clima** (lluvia y temperaturas) de cada uno de ocho
  departamentos cafeteros.
- **Descargar las series** del periodo que elija, en CSV, con fecha real del
  dato, unidad y fuente; y generar un **brief en PDF** con las gráficas, las
  variaciones y las fuentes, listo para un informe o una reunión.
- **Explorar escenarios** de precio interno y margen con el simulador.

---

## Las tres vistas

1. **Panorama nacional** (la vista de entrada). Precio internacional del café,
   USD/COP y precio interno FNC en una escala base 100 para compararlos en un
   mismo gráfico, más la producción nacional mensual. Aquí están las descargas
   por periodo: las series comerciales en CSV y un brief en PDF con las gráficas.
2. **Simulador.** Escenarios de precio interno y margen al mover supuestos de
   Coffee C, USD/COP, costo, volumen y factor de rendimiento, con la opción de
   descargar un informe del escenario (ver más abajo).
3. **Climatología cafetera.** Lluvia y temperaturas del departamento elegido en
   el panel izquierdo, usando un municipio como referencia climática.

> El panorama comercial **no cambia** al elegir un departamento: precio
> internacional, USD/COP y precio FNC son variables globales o nacionales. El
> selector de departamento solo afecta la vista de clima.

---

## El simulador, en palabras simples

El simulador permite preguntarse *"¿qué pasaría con el precio interno si el café
internacional o el dólar se mueven?"*.

Toma el **último precio interno FNC observado** como punto de partida y lo
desplaza en la misma proporción en que usted suponga que cambian el precio
internacional (Coffee C) y la tasa de cambio:

> precio interno proyectado = precio FNC base × (USD/COP escenario ÷ USD/COP base)
> × (Coffee C escenario ÷ Coffee C base) × (factor referencia ÷ factor de rendimiento)

Con ese precio y un **costo de producción por carga** —que puede editar— estima
el margen bruto por carga y para el volumen que indique. El costo inicial es la
referencia nacional FEPCafé (1.624.000 COP por carga de 125 kg, dato de abril de
2026); cámbielo para representar el supuesto de una finca distinta. El **factor
de rendimiento** (94 de referencia) ajusta de forma aproximada el precio: un
factor menor lo sube, uno mayor lo baja.

Puede fijar el escenario moviendo los controles o **haciendo clic directamente
en el mapa de sensibilidad**, y volver a los valores iniciales con el botón
**Restablecer**. Cuando termine, puede **descargar un informe en Markdown** con
los valores introducidos, los resultados, la metodología y las limitaciones,
listo para anexar a un análisis o una presentación.

**Qué es y qué no es:**

- Es una herramienta para **explorar supuestos**, no un pronóstico.
- El margen es **bruto**: no incluye prima por café suave, calidad, pasilla,
  acopio, impuestos, logística ni financiación.
- El ajuste por factor de rendimiento es **aproximado**, no la fórmula oficial
  completa de la FNC; el resto de factores se mantienen constantes.

---

## De dónde salen los datos

| Variable | Fuente | Cadencia |
|----------|--------|----------|
| Precio internacional del café (Coffee C) | Futuro ICE Coffee C | Semanal |
| Tasa de cambio USD/COP | Mercado | Semanal |
| Precio interno de referencia | Federación Nacional de Cafeteros (FNC) | Semanal |
| Producción nacional | Federación Nacional de Cafeteros (FNC) | Mensual |
| Clima (lluvia y temperatura) | Open-Meteo | Semanal |
| Costo de producción de referencia | FEPCafé | Mensual |

El histórico arranca en enero de 2023. Cada serie conserva su **cadencia
honesta**: precio, dólar y clima se muestran por semana; la producción solo
aparece en los meses efectivamente publicados, sin rellenar las semanas
intermedias.

**Departamentos cubiertos:** Huila, Antioquia, Tolima, Cauca, Nariño, Caldas,
Risaralda y Quindío.

---

## Cómo interpretarla (y cómo no)

- Es una **herramienta de consulta y reporte**, no un sistema de recomendación.
  Todavía **no** asigna "bueno", "malo", "oportunidad" ni "riesgo": describe lo
  que pasó, sin calificar si un valor es favorable o desfavorable.
- Una coordenada municipal **no describe** todo un departamento.
- Una anomalía estadística en el clima **no equivale** por sí sola a un riesgo
  agronómico.
- Las noticias y señales cualitativas son secundarias: ninguna nota aislada
  debe tomarse como hecho confirmado.

Estas limitaciones son intencionales: la herramienta prefiere ser honesta sobre
lo que sabe antes que aparentar una precisión que aún no tiene.

---

## En qué punto está

Esta es una versión para recibir retroalimentación de sus usuarias reales
(equipos de investigación y formación del sector cafetero). El objetivo cercano
es validar que el kit de consulta y el brief sean útiles en una tarea real antes
de ampliar fuentes o incorporar un índice. La **actualización de datos cada 2
días ya está automatizada** (la página se refresca sola). Un eventual score de
oportunidad/riesgo queda para más adelante, solo cuando exista conocimiento
experto que lo respalde.

---

© 2026 Juan José Jaramillo. Todos los derechos reservados.
