# Briefing estratégico - Monitor Agro Colombia

Vigencia del briefing: **24 de junio de 2026**.

## Cómo usar este archivo

Este documento permite iniciar un chat nuevo sobre estrategia, diseño o
dirección del proyecto sin depender de conversaciones anteriores, del código ni
de otros archivos. Puede entregarse por sí solo a una IA web normal.

El chat debe ayudar a pensar el producto y convertir decisiones en próximos
pasos claros. No debe inventar avances técnicos, datos o conocimiento cafetero
que aquí aparezcan como pendientes.

Este es el único documento que debe poder viajar solo. Por eso incluye un
resumen mínimo del producto y su estado, aunque esos hechos también existan en
el repositorio.

---

## La creadora y lo que busca

La creadora es estudiante de Negocios Internacionales, próxima a graduarse,
autodidacta en análisis de datos y radicada en Manizales, Colombia. Quiere
orientarse hacia roles de análisis de negocios/datos que conecten comercio,
economía y geopolítica.

Este proyecto cumple dos objetivos:

1. Ser una pieza de portafolio que demuestre criterio de negocio, manejo de
   datos y capacidad de construir una herramienta completa.
2. Llegar a ser útil para personas reales del sector cafetero colombiano.

La comunicación debe ser en español, directa, práctica y clara para una persona
principiante en programación. Conviene explicar el porqué sin condescendencia,
proponer pasos pequeños y terminables, y evitar ampliar el alcance sin una razón
de producto.

---

## Qué es el producto

**Monitor Agro Colombia** se está consolidando como un kit de consulta y
reporte del que se extrae evidencia para análisis, informes y reuniones.
Conserva su pipeline y snapshots, pero su valor visible no es solo consultar
una semana: es integrar, comparar y exportar series. Combina:

- precio interno de referencia de la Federación Nacional de Cafeteros (FNC);
- precio internacional del café arábica ICE Coffee C;
- tasa de cambio USD/COP;
- producción nacional mensual registrada por la FNC;
- lluvia y temperaturas en ocho departamentos cafeteros;
- señales nacionales de noticias, todavía secundarias.

Los ocho departamentos iniciales son Huila, Antioquia, Tolima, Cauca, Nariño,
Caldas, Risaralda y Quindío. Cada uno usa por ahora un municipio como referencia
climática; esto no representa toda su diversidad interna.

El proyecto nació comparando cinco países latinoamericanos, pero se reorientó a
Colombia porque las beneficiarias reales trabajan con el sector cafetero
nacional. El contexto internacional se mantiene mediante el precio ICE y el
tipo de cambio. La intención es ganar profundidad y utilidad, no exhibir más
países sin una necesidad clara.

---

## Para quién se diseña

Hay dos beneficiarias principales y dos lentes complementarios:

- **Tía vinculada a CRECE:** lente económico, comercial y de investigación.
  Trabaja integrando información sobre productores, territorios, productividad,
  sostenibilidad, precios, mercado y programas de apoyo. Le sirven series
  limpias y comparables, tendencias, fuentes citables, metodología clara y
  salidas reutilizables en análisis, informes, presentaciones y reuniones.
- **Mamá vinculada a Fundación Manuel Mejía:** lente del productor y
  pedagógico. Le sirve entender cómo clima, precio y costos pueden traducirse
  en condiciones relevantes para caficultores y procesos de formación.

Ellas y sus colegas son las usuarias directas; el tablero no está pensado para
que un caficultor lo opere necesariamente. Debe sentirse ejecutivo y riguroso,
pero comprensible.

La prioridad aproximada sigue siendo 60% portafolio y 40% utilidad inmediata.
Una mejora gana valor cuando fortalece ambos objetivos.

---

## Estado actual, explicado sin código

Ya existe un MVP funcional con:

- histórico semanal desde enero de 2023, con 180 semanas completas;
- tres variables comerciales nacionales/globales;
- producción nacional mensual desde enero de 2023;
- cuatro variables climáticas para cada uno de los ocho departamentos;
- tendencias, cambios, promedios móviles, anomalías estadísticas neutrales y
  comparaciones entre departamentos;
- un dashboard local con tres vistas: panorama nacional, detalle climático del
  departamento elegido y comparación entre departamentos;
- filtros de periodo y departamento;
- selector de fechas personalizadas, descarga CSV y brief Markdown por periodo;
- tema visual claro y selección departamental visible mediante su municipio de
  referencia.

El dashboard actual es una herramienta para obtener feedback, no el producto
final. Todavía no contiene un score de oportunidad/riesgo ni interpreta que un
valor sea bueno o malo.

Importante: el panorama comercial no cambia al seleccionar departamento porque
precio internacional, USD/COP y precio FNC son variables globales o nacionales.
El selector sí cambia las vistas climáticas departamentales.

---

## Decisiones estratégicas vigentes

- **MVP antes que sofisticación:** probar comprensión y utilidad antes de
  construir más capas.
- **Colombia antes que LatAm:** profundidad subnacional para usuarias reales.
- **Precio interno FNC como centro del lente productor:** el precio ICE es
  contexto internacional, no sustituto del precio recibido localmente.
- **Lenguaje neutral por ahora:** ranking alto significa mayor valor numérico,
  no mejor resultado ni menor riesgo.
- **No construir el score a ciegas:** primero se necesita conocimiento experto
  sobre cosecha, clima, costos y lectura del negocio cafetero.
- **Credibilidad visible:** el producto final debe explicar fuentes,
  metodología, alcance y limitaciones.
- **Integrar antes que multiplicar:** para CRECE, el valor principal está en
  reducir el trabajo de buscar, limpiar, comparar y verificar varias fuentes,
  no en añadir indicadores sin una pregunta de uso.
- **Reutilización como función central:** los datos y gráficos deben poder
  descargarse o exportarse con periodo, unidad, fuente y fecha claramente
  identificados.
- **Lente comercial y de investigación primero:** fortalecer la lectura conjunta
  del precio interno FNC, Coffee C y USD/COP antes de ampliar el componente
  climático o construir interpretaciones causales.
- **Kit de consulta y reporte:** el brief exportable por periodo es una salida
  central, no un complemento tardío del tablero.
- **Cadencia honesta por serie:** precio, dólar y clima conservan su tratamiento
  semanal; producción se muestra únicamente en sus meses publicados.

---

## Información experta pendiente

Estas preguntas deben resolverse con las beneficiarias o fuentes cafeteras
confiables antes de diseñar el score:

1. Calendario de cosecha y floración por región, y qué clima preocupa en cada
   etapa.
2. Qué define una buena o mala semana para el productor: precio, costos, margen
   u otra combinación.
3. Cómo incorporar costos de producción e insumos, incluidos fertilizantes
   sensibles al dólar.
4. Si resulta útil mostrar condiciones favorables para roya y broca.
5. Qué unidades usa su público: carga, arroba, factor de rendimiento u otras.
6. Qué fuentes y reportes consultan hoy, para complementar en vez de duplicar.
7. Si la prima o diferencial de los suaves colombianos debe aparecer.

Ya está confirmado que trabajan con alcance nacional, no únicamente con Caldas.

## Feedback confirmado de CRECE

La beneficiaria de CRECE trabaja principalmente desde la investigación y el
análisis, conectando la realidad del productor con las dinámicas económicas,
comerciales e institucionales del sector. Sus entregables incluyen informes
técnicos, presentaciones, cifras para reuniones, propuestas, boletines y
reportes con periodicidad variable, además de solicitudes rápidas.

El problema principal no es encontrar un precio puntual. Es reunir series
limpias, comparables y actualizadas desde fuentes oficiales o especializadas,
depurarlas y comprobar su consistencia antes de usarlas.

Las preguntas de mayor valor futuro conectan precio, producción, productividad,
costos, territorio y condiciones del productor. Por ejemplo, cambios en
ingresos, exposición de municipios o tipos de productores y relaciones entre
mercado, decisiones en finca, sostenibilidad y bienestar. Estas preguntas
requieren nuevas fuentes y no deben fingirse con los datos actuales.

---

## Oportunidades de producto ya identificadas

No son compromisos automáticos; deben priorizarse con feedback:

- **Margen aproximado del productor:** precio interno menos costo de producción
  de referencia, con metodología y limitaciones explícitas.
- **Dos lentes de lectura:** comercial/institucional y productor/pedagógico, en
  lugar de un único número que mezcle objetivos diferentes.
- **Calendario fenológico regional:** permitiría interpretar clima según la
  etapa del cultivo.
- **Señales de roya y broca:** solo si son defendibles con los datos y útiles
  para las beneficiarias.
- **Brief semanal exportable:** una página útil para informes, reuniones o
  contenidos de formación.
- **Capa metodológica:** diccionario de datos, fuentes, fecha de actualización,
  cobertura y explicación del futuro score.
- **Descarga para análisis:** series filtradas y tablas comerciales listas para
  reutilizar, conservando fecha, unidad y fuente.
- **Producción y productividad territorial:** primera ampliación de datos a
  evaluar más adelante. La ampliación confirmada actual es solo producción
  nacional mensual; el nivel departamental o municipal queda fuera de alcance.
- **Automatización semanal y publicación:** después de estabilizar contenido e
  interfaz.

---

## Riesgos y límites conocidos

- Algunas fuentes comerciales provienen de scraping y pueden cambiar.
- La fuente de noticias puede limitar consultas; no debe tratarse una noticia
  aislada como un hecho confirmado.
- Una coordenada municipal no describe todo un departamento.
- Una anomalía estadística no equivale por sí sola a riesgo agronómico.
- Un score sin calendario productivo, costos y validación experta parecería
  preciso, pero sería conceptualmente débil.
- El código está respaldado en GitHub y la aplicación está publicada y
  funcional en Streamlit Community Cloud. La actualización automática de datos
  todavía no está implementada.

---

## Próximo objetivo

Convertir el panorama comercial en una herramienta reutilizable para
investigación y preparación de entregables. El orden de trabajo confirmado es:

1. Compartir la aplicación publicada y probar el kit y el brief con una tarea
   real de CRECE.
2. Ajustar contenido, jerarquía y formato según ese uso.
3. Evaluar después si hace falta producción territorial u otra nueva fuente.
4. Considerar PDF solo si la usuaria lo necesita; Markdown es la salida inicial.
5. Retomar costos, margen, exposición y posibles scores solo cuando existan
   datos y conocimiento experto suficientes.

La capa climática existente se conserva, pero este feedback no justifica
ampliarla ni priorizar nuevas funciones climáticas.

---

## Cómo debe ayudar el nuevo chat

- Separar hechos confirmados, supuestos y recomendaciones.
- Hacer preguntas solo cuando la respuesta cambie una decisión importante.
- Dar una recomendación clara cuando existan varias opciones, explicando el
  trade-off.
- Mantener el foco en utilidad para las beneficiarias y señal de portafolio.
- No asumir que más funciones hacen mejor el producto.
- No pedir acceso al código para discutir estrategia; este briefing contiene el
  contexto necesario para hacerlo.

---

## Cómo devolver decisiones al proyecto

Cuando el chat produzca una decisión firme, debe entregarla al usuario en este
formato para incorporarla después a este briefing o al repositorio:

```text
Decisión confirmada:
- Qué se decidió:
- Por qué:
- A quién beneficia:
- Qué cambia en el producto:
- Qué queda pendiente o fuera de alcance:
```

Actualizar este archivo únicamente con decisiones estratégicas confirmadas,
cambios de audiencia, prioridades, preguntas expertas resueltas o nuevo
feedback de usuarias. No registrar commits, rutas, errores de ejecución ni
detalles de implementación; esos pertenecen a la continuidad técnica.
