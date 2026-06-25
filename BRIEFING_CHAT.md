# Briefing estratégico - Monitor Agro Colombia

Vigencia del briefing: **25 de junio de 2026**.

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
- exportaciones nacionales mensuales de café registradas por la FNC;
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
- exportaciones nacionales mensuales desde enero de 2023 y comparación con la
  producción mediante una diferencia descriptiva por mes;
- cuatro variables climáticas para cada uno de los ocho departamentos;
- tendencias, cambios, promedios móviles, anomalías estadísticas neutrales y
  comparaciones entre departamentos;
- un dashboard publicado con dos vistas, en orden: panorama nacional (entrada)
  y simulador;
- periodos predefinidos;
- selector de fechas personalizadas, descarga CSV y brief en PDF por periodo,
  con las gráficas, las variaciones y las fuentes incluidas;
- estimador de supuestos para Coffee C, USD/COP, costo por carga y factor de
  rendimiento, con precio FNC estimado, margen bruto, mapa de sensibilidad
  clicable, botón de restablecer e informe del escenario descargable;
- calibración principal del estimador con el último trío coherente de precio
  interno, Coffee C y TRM publicado por la FNC para una misma fecha, y una
  calibración estadística reciente como respaldo si esa fuente falla;
- actualización automatizada cada 2 días (GitHub Actions) que refresca los datos y
  redespliega la app sin intervención;
- tema visual claro.

El dashboard actual es una herramienta para obtener feedback, no el producto
final. Todavía no contiene un score de oportunidad/riesgo ni interpreta que un
valor sea bueno o malo.

La capa climática y sus datos se conservan en el pipeline, pero la vista
climática y el selector departamental fueron retirados de la interfaz para
concentrar el producto visible en consulta, reporte y simulación comercial.

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
- **Estimación antes que pronóstico:** el escenario comercial estima el precio
  FNC a partir de Coffee C, USD/COP y un coeficiente implícito derivado del
  último trío que la FNC publica conjuntamente. El precio FNC observado calibra
  y permite comparar, pero no funciona como entrada editable ni como piso.
  Sirve para explorar supuestos, no para afirmar cuál será el precio futuro.
- **Costo con trazabilidad y edición:** el simulador parte del costo medio
  nacional de 1.624.000 COP por carga de 125 kg para abril de 2026, publicado
  en el reporte mensual de mayo de 2026 de FEPCafé. Permite modificarlo porque
  no representa la estructura particular de cada finca.
- **Diferencial incorporado de forma implícita:** la prima del café colombiano,
  conversiones y otros componentes no se modelan como controles separados; su
  efecto conjunto queda recogido en el coeficiente derivado de las referencias
  oficiales de la FNC.
- **Factor de rendimiento aproximado:** a petición del usuario se añadió un
  ajuste por factor de rendimiento (referencia 94) como multiplicador simple,
  marcado explícitamente como aproximado y no como la fórmula oficial de la FNC.
- **Fuentes coherentes para estimar:** no mezclar el precio FNC oficial con
  cierres de Coffee C y USD/COP de otro proveedor u otra hora cuando exista el
  trío diario publicado conjuntamente por la FNC. Los cierres de Yahoo se
  conservan para las series de mercado y como respaldo estadístico.
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
  semanal; producción y exportaciones se muestran únicamente en sus meses
  publicados.
- **Diferencia mensual sin sobreinterpretación:** producción menos exportaciones
  ayuda a detectar meses en que un flujo supera al otro, pero no equivale a
  inventarios, reservas ni consumo interno sin fuentes adicionales.

---

## Información experta pendiente

Estas preguntas deben resolverse con las beneficiarias o fuentes cafeteras
confiables antes de diseñar el score:

1. Calendario de cosecha y floración por región, y qué clima preocupa en cada
   etapa.
2. Qué define una buena o mala semana para el productor: precio, costos, margen
   u otra combinación.
3. Cómo adaptar el costo medio nacional a regiones, tamaños y sistemas
   productivos, incluidos insumos sensibles al dólar.
4. Si resulta útil mostrar condiciones favorables para roya y broca.
5. Qué unidades usa su público: carga, arroba, factor de rendimiento u otras.
6. Qué fuentes y reportes consultan hoy, para complementar en vez de duplicar.
7. Si la prima o diferencial de los suaves colombianos debe aparecer como
   control explícito, además de estar incorporado implícitamente en la
   calibración.

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

- **Margen aproximado del productor:** implementado como simulación bruta:
  precio interno estimado menos costo por carga editable, con metodología y
  limitaciones explícitas.
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
- **Producción y productividad territorial:** ampliación a evaluar más adelante.
  La cobertura actual incluye producción y exportaciones nacionales mensuales;
  el nivel departamental o municipal queda fuera de alcance.
- **Automatización cada 2 días:** ya implementada con GitHub Actions; queda
  validar su primera corrida real y, opcionalmente, archivar snapshots.

---

## Riesgos y límites conocidos

- Algunas fuentes comerciales provienen de scraping y pueden cambiar.
- La fuente de noticias puede limitar consultas; no debe tratarse una noticia
  aislada como un hecho confirmado.
- Una coordenada municipal no describe todo un departamento.
- Una anomalía estadística no equivale por sí sola a riesgo agronómico.
- Un score sin calendario productivo, costos y validación experta parecería
  preciso, pero sería conceptualmente débil.
- El estimador no reproduce la fórmula oficial completa. Usa el ajuste implícito
  del último trío coherente publicado por la FNC y supone que se mantiene en el
  escenario; la prima no es un control separado. Aplica un ajuste aproximado por
  factor de rendimiento y no modela por separado calidad, pasilla, acopio,
  impuestos ni logística.
- La referencia oficial diaria depende de scraping y puede cambiar de estructura.
  Si falla, se usa una calibración estadística reciente como respaldo, cuyo error
  histórico medio validado es aproximadamente 26.376 COP por carga (1,02%).
- Con la calibración oficial del 25 de junio de 2026, el estimador reproduce
  2.160.000 COP para TRM 3.435,99 y Coffee C 276,40. Aplicado a los valores del
  24 de junio de 2026 estima 2.163.736 COP frente a 2.165.000 COP observados:
  una diferencia de 1.264 COP (0,06%), sin fijar manualmente el resultado.
- El código está respaldado en GitHub y la aplicación está publicada y funcional
  en Streamlit Community Cloud, verificada por el usuario. La actualización
  automática de datos ya está implementada (GitHub Actions semanal); falta
  validar su primera corrida real en el runner.
- El repositorio es público solo para portafolio, con licencia propietaria
  ("Todos los derechos reservados"): el código no puede reutilizarse sin permiso.

---

## Próximo objetivo

Convertir el panorama comercial en una herramienta reutilizable para
investigación y preparación de entregables. El orden de trabajo confirmado es:

1. Compartir la aplicación publicada y probar el kit y el brief con una tarea
   real de CRECE.
2. Ajustar contenido, jerarquía y formato según ese uso.
3. Validar si el estimador ayuda a responder preguntas reales, si la calibración
   oficial se mantiene precisa en nuevas fechas y si requiere mostrar la prima
   como control explícito, costos regionales o escenarios guardables.
4. Evaluar después si hace falta producción territorial u otra nueva fuente.
5. El brief del periodo ya es un PDF con gráficas, tablas y fuentes; queda
   validar con CRECE si el formato y el contenido sirven para sus entregables.
6. Retomar posibles scores solo cuando existan datos y conocimiento experto
   suficientes.

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
