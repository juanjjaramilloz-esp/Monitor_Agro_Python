# Paquete de portafolio — Pulso Cafetero (Monitor Agro Colombia)

> **Documento interno de trabajo.** Plan de validación y publicación; no es
> documentación del producto.

Este documento reúne el material que debe completarse fuera del código. No se
publicará una reseña ni se atribuirá apoyo institucional sin permiso explícito.

## 1. Prueba de utilidad con CRECE

Pedir a la participante que elija una tarea que realmente deba resolver. No
explicar cada pantalla de antemano: interesa observar si la herramienta se
entiende por sí sola.

Registrar:

- fecha, tarea o pregunta y entregable que estaba preparando;
- fuentes o procedimiento que usaría normalmente;
- tiempo aproximado habitual y tiempo empleado con la aplicación;
- periodo, indicadores y pantallas consultadas;
- descargas utilizadas: Excel, PDF o informe del simulador;
- resultado que pudo reutilizar;
- confusiones, verificaciones externas y mejoras solicitadas.

### Preguntas al terminar

1. ¿Qué tarea intentabas resolver y para qué entregable?
2. ¿Qué parte de la aplicación resultó más útil?
3. ¿Pudiste reutilizar alguna cifra, gráfica o descarga?
4. ¿Qué tuviste que verificar por fuera de la aplicación?
5. ¿Te ahorró tiempo? ¿Cuánto, aproximadamente?
6. ¿Qué información faltó o resultó confusa?
7. ¿La volverías a usar para una tarea similar? ¿Por qué?

### Las tres preguntas clave para la reseña de LinkedIn

Si solo hay tiempo para tres, estas producen las respuestas más citables
(impacto concreto + tiempo ahorrado + credibilidad institucional). Pedir
respuestas de 2-3 frases y conservar la aprobación textual por escrito:

1. **¿Para qué tarea o entregable real la usaste, y qué pudiste reutilizar
   directamente (una cifra, gráfica, el Excel o el PDF)?** → demuestra uso
   real, no demo.
2. **Frente a tu forma habitual de reunir y verificar estas series, ¿cuánto
   tiempo te ahorró, aproximadamente?** → el dato cuantificable que más pesa
   ("de X horas a Y minutos").
3. **¿Qué te dio la confianza para usar estos datos en un contexto profesional
   o institucional?** → la cita de credibilidad (fuentes, trazabilidad,
   metodología) dicha por una directora de investigación.

### Autorización de la reseña

Redactar la reseña después de la conversación y enviarla para aprobación
literal. Conservar autorización escrita sobre:

- texto exacto, nombre, cargo y mención de CRECE;
- publicación en GitHub, hoja de vida y LinkedIn.

Publicar junto a ella: “Opinión personal derivada de una prueba de uso; no
representa patrocinio, adopción ni aval institucional de CRECE”.

## 2. Evidencia para el README

Cuando termine la prueba, reemplazar el estado provisional de “Impacto y
validación” por un mini caso verificable:

```text
Tarea probada:
Entregable que estaba preparando:
Cómo la resolvía antes:
Qué utilizó en la app:
Resultado reutilizado:
Tiempo estimado antes / con la app:
Mejora solicitada:

“Reseña aprobada textualmente”.
— Nombre, cargo, CRECE
```

Si el ahorro de tiempo no puede medirse, describir el resultado cualitativo sin
inventar una cifra.

## 3. Capturas y demostración

- `panorama.png`: escritorio a 1440 px, con encabezado, métricas y primera
  gráfica; sin navegador ni datos personales.
- `simulador.png`: escenario legible, resultados y parte superior del mapa de
  sensibilidad.

Antes de publicarlas, comprobar que fecha y cifras coincidan con la app en vivo.
La composición debe tomarse de la interfaz estable restaurada el 30 de junio;
no usar capturas del rediseño experimental que fue revertido.

### Guion de video o GIF (30–45 segundos)

1. Abrir `Panorama nacional` (3 s).
2. Cambiar el periodo y mostrar la respuesta de las gráficas (7 s).
3. Señalar fecha, unidad y fuente; descargar Excel o PDF (8 s).
4. Entrar a `Simulador` y modificar Coffee C y USD/COP (10 s).
5. Mostrar precio, margen y mapa de sensibilidad (8 s).
6. Cerrar con el enlace y “Datos de mercado convertidos en evidencia lista
   para analizar y reportar” (4 s).

Grabar a 1440×900, sin audio o con subtítulos breves, cursor lento y zoom al
100 %. Exportar MP4 para LinkedIn y GIF solo si el texto sigue siendo legible.

## 4. Entrada para la hoja de vida

**Pulso Cafetero — Proyecto de análisis de datos y negocios**  
Python · pandas · Streamlit · Plotly · GitHub Actions

- Desarrollé una aplicación bilingüe que integra Coffee C, USD/COP, precio FNC,
  producción y exportaciones de café desde 2023 para consulta y análisis.
- Automaticé la validación, actualización y publicación cada dos días;
  implementé 69 pruebas y entregables en Excel, PDF y Markdown.
- Diseñé la herramienta con enfoque de investigación del sector cafetero y la
  estoy validando mediante una tarea real con una directora de investigación
  para evaluar su utilidad en consultas, informes y escenarios.

Tras la prueba, reemplazar la tercera viñeta por su resultado comprobado.
Enlazar el nombre del proyecto directamente a la aplicación.

## 5. Borrador para LinkedIn

### Versión final (español) — lista para pegar

> Encontrar el precio del café es fácil. Convertirlo en evidencia lista para
> un informe es otra historia.
>
> Quien prepara un análisis del sector cafetero pierde horas reuniendo series
> de varias fuentes, verificando fechas y unidades, y rearmando las mismas
> gráficas para cada entregable. Construí Pulso Cafetero para eliminar ese
> trabajo.
>
> ☕ Qué hace:
> • Integra el precio internacional (ICE Coffee C), USD/COP, el precio
> interno FNC y la producción y exportaciones de Colombia desde 2023.
> • Muestra el último precio de mercado del dólar y del café (~15 min de
> retraso) junto al histórico semanal.
> • Exporta la evidencia en Excel y en un brief PDF de tres páginas, en
> español o inglés.
> • Simula escenarios de precio interno y margen bruto por carga.
>
> 🔧 Cómo está hecho: Python, pandas, Streamlit y Plotly; 69 pruebas
> unitarias que corren en CI; datos que se actualizan solos cada 2 días con
> GitHub Actions.
>
> 📊 La decisión de la que más aprendí no fue técnica: me negué a fabricar un
> "índice de riesgo" sin conocimiento experto que lo respaldara. Preferí
> trazabilidad, cadencias honestas y utilidad verificable — el mismo criterio
> que pide un análisis serio.
>
> [RESULTADO DE LA PRUEBA — 2-3 líneas: tarea real resuelta, tiempo ahorrado
> y cita aprobada de la directora de investigación, con el disclaimer de no
> aval institucional.]
>
> 👉 Pruébala (sin registro): https://kitconsultayreporte.streamlit.app/
> 📂 Código y metodología: https://github.com/juanjosejaramillozarate-png/Monitor_Agro_Python
>
> #AnálisisDeDatos #Python #Streamlit #DataAnalytics #Café #Colombia

Notas de uso: la primera línea es el gancho (LinkedIn corta ahí el "ver
más"); adjuntar el video como primera pieza (o las dos capturas de
`docs/img/` como carrusel si el video no está listo); publicar martes a
jueves en la mañana; responder los comentarios del primer día.

### Versión corta (inglés) — primer comentario o segundo post

> Finding a coffee price is easy. Turning it into report-ready evidence is
> not.
>
> I built Coffee Pulse, a bilingual (ES/EN) data tool for the Colombian
> coffee sector: it integrates ICE Coffee C, USD/COP, the FNC internal price
> and national production/exports since 2023, shows near-real-time market
> prices, exports Excel workbooks and a PDF brief, and simulates price/margin
> scenarios.
>
> Python · pandas · Streamlit · 69 unit tests in CI · automated data refresh
> every 2 days.
>
> Try it (no sign-up): https://kitconsultayreporte.streamlit.app/

En “Destacados”, incluir la app, la publicación y una muestra legible del
PDF. En “Proyectos”, asociar Python, pandas, análisis de datos, inteligencia
de negocios, visualización de datos y comercio internacional.

## 6. Checklist final de publicación

**El post (contenido):**
- [ ] El resultado de la prueba reemplazó el marcador [RESULTADO DE LA PRUEBA].
- [ ] La participante aprobó literalmente reseña y atribución (por escrito).
- [ ] La reseña incluye el disclaimer de no aval institucional de CRECE.
- [ ] El video (30-45 s) está grabado según el guion de la sección 3, o en su
      defecto se usan las dos capturas de `docs/img/` como carrusel.

**La vitrina (app + repo):**
- [ ] La app pública muestra "Pulso Cafetero" (hacer Reboot en Streamlit
      Cloud si aún muestra el nombre anterior).
- [ ] El badge de Pruebas está en verde (pestaña Actions del repo).
- [ ] Descripción y topics del repo aplicados en GitHub.
- [ ] La protección de rama de `main` quedó reactivada tras el force-push.
- [ ] Cifras y fechas de las capturas coinciden con la app en vivo.
- [ ] App, README y enlaces abren sin iniciar sesión (probar en incógnito).

**El perfil:**
- [ ] "Destacados" con la app, el post y una muestra del PDF.
- [ ] Proyecto añadido en "Proyectos" con las skills asociadas.
- [ ] Titular del perfil coherente con el rol buscado.
- [ ] CV y LinkedIn describen el aporte personal en primera persona.
