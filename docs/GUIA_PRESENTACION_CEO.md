# GUÍA DE PRESENTACIÓN — SISTEMA HOTEL MANTENIMIENTO
### Para presentar a CEOs / Líderes empresariales

---

## ANTES DE ENTRAR — MENTALIDAD

**NO eres un programador explicando código.**
**ERES el experto que resolvió un problema de negocio real.**

> Regla de oro: Cada vez que expliques algo técnico,
> termina con "...lo que significa que el hotel **ahorra / evita / gana**..."

---

## FRASE DE APERTURA (memorízala)

> *"¿Cuánto pierden cuando una habitación sale de servicio de emergencia
> a las 11 de la noche porque falló el aire acondicionado?
> ¿Y si pudieran saberlo con 2 semanas de anticipación?"*

---

## LA SOLUCIÓN EN UNA FRASE

> *"Desarrollé un sistema que le dice al hotel QUÉ se va a romper,
> CUÁNDO, CUÁNTO va a costar, y QUIÉN es el mejor técnico
> para arreglarlo — todo ANTES de que ocurra el problema."*

**→ Pausa aquí. Deja que eso aterrice.**

---

## ESTRUCTURA (30–45 minutos)

### PASO 1 — El problema (3 min)

Los hoteles hoy trabajan de forma **reactiva**:
- Algo se rompe → llaman a un técnico → habitación fuera de servicio
- No saben qué técnico mandar hasta que el problema ya ocurrió
- No saben cuánto va a costar hasta que tienen la factura
- La limpieza se asigna por número de habitación, no por urgencia real

---

### PASO 2 — Demo en vivo (20 min)

Sigue este orden exacto:

**1. Dashboard** (`/dashboard`)
> "En segundos el gerente ve cuántas habitaciones están disponibles,
> cuántas en riesgo y cuánto ha costado el mantenimiento este mes."

**2. Predicciones de falla** (`/predicciones`)
> "La IA calcula la probabilidad de falla de cada equipo en 7, 14 o 30 días."
> *(Señala un item en rojo)*
> "Este aire acondicionado tiene 78% de probabilidad de fallar
> en los próximos 7 días. Sin este sistema, el hotel no lo sabría
> hasta que deja de funcionar en plena temporada alta."

**3. Auto-Programación** (`/automatizacion`)
> "El sistema genera automáticamente el plan de mantenimiento del mes.
> El administrador solo aprueba o rechaza con un clic.
> El hotel pasa de **reactivo** a **proactivo**."

**4. Detección Visual** (`/vision`)
> "El personal toma una foto con el celular. El sistema detecta
> automáticamente daños, manchas o problemas — sin que el empleado
> necesite saber qué buscar. Crea un registro fotográfico automático."

**5. Predicción de Costos** (`/costos`)
> "Antes de aprobar cualquier mantenimiento, el sistema ya tiene
> una estimación de cuánto costará, con rango mínimo y máximo
> para poder presupuestar."

**6. Recomendación de Técnicos** (`/tecnicos`)
> "El sistema sabe qué técnico tiene mejor desempeño para cada tipo
> de equipo, cuántas órdenes tiene pendientes y cuánto tarda en promedio.
> Recomienda al mejor automáticamente."

**7. Priorización de Limpieza** (`/limpieza`)
> "En lugar de limpiar en orden numérico, el sistema calcula cuál
> necesita atención URGENTE: cuándo se fue el huésped, cuándo llega
> el siguiente y la categoría de la habitación."
> *(Muestra el mapa de calor)*
> "Este mapa le muestra al supervisor en segundos dónde mandar
> a su equipo primero."

**8. Reportes PDF** (`/reporte`)
> "Con un clic, genera un reporte ejecutivo listo para presentar
> a dirección o a los dueños."

---

### PASO 3 — Los números (5 min)

| Problema actual | Lo que hace el sistema | Impacto |
|---|---|---|
| Habitación fuera de servicio inesperada | Anticipa falla 7–30 días antes | Evita pérdida de ingreso por habitación no vendida |
| Técnico incorrecto para el trabajo | Recomienda al especialista correcto | Reduce tiempo de reparación 20–40% |
| Presupuesto de mantenimiento sin control | Predice costos con anticipación | Menos sorpresas, presupuesto más preciso |
| Limpieza tardía en suite premium | Prioriza por categoría y urgencia | Más satisfacción del huésped VIP |
| Mantenimiento reactivo = emergencias | Plan preventivo automático | Reparaciones programadas cuestan 3–5× menos |

> *"Una sola habitación fuera de servicio en temporada alta representa
> entre $200 y $500 dólares perdidos por noche.
> Este sistema puede evitar varios de esos casos al mes."*

---

### PASO 4 — Cómo está construido (sin tecnicismos) (3 min)

> "El sistema tiene tres capas:"
> 1. **La base de datos** — Guarda todo el historial: habitaciones, equipos, fallas, costos, técnicos.
> 2. **La inteligencia artificial** — 6 módulos que aprenden del historial y generan predicciones.
> 3. **La interfaz web** — Accesible desde cualquier computadora o tablet, solo con el navegador.

---

### PASO 5 — Cierre con propuesta concreta (3 min)

> *"Lo que propongo es una fase piloto con [X habitaciones / X semanas].
> En ese tiempo pueden ver el sistema funcionando con datos reales del hotel
> y medir el impacto antes de cualquier compromiso mayor."*

> *"¿Qué necesitarían ver para tomar una decisión?"*

---

## LOS 6 MÓDULOS DE IA — Para explicar rápido

| Módulo | En palabras simples |
|---|---|
| Predicción de fallas | "Dice cuándo se va a romper un equipo antes de que pase" |
| Detección visual | "Analiza fotos y detecta problemas automáticamente" |
| Prioridad de limpieza | "Ordena qué habitación limpiar primero según urgencia real" |
| Predicción de costos | "Estima cuánto va a costar arreglar algo antes de hacerlo" |
| Recomendación de técnicos | "Elige al mejor técnico para cada trabajo automáticamente" |
| Plan preventivo | "Genera el calendario de mantenimiento del mes automáticamente" |

---

## PREGUNTAS FRECUENTES

**"¿Es seguro poner todos los datos del hotel aquí?"**
> "Los datos quedan en el propio servidor del hotel, no salen a ningún lado externo.
> El acceso está protegido por usuarios y contraseñas encriptadas."

**"¿Qué pasa si la IA se equivoca?"**
> "La IA es una recomendación, no una orden. El administrador siempre
> aprueba o rechaza. La decisión final siempre la toma el humano."

**"¿Necesitamos capacitar a todos los empleados?"**
> "Los empleados solo ven su lista de tareas pendientes.
> Solo el administrador necesita aprender el panel completo,
> lo cual lleva menos de un día."

**"¿Cuánto cuesta mantenerlo?"**
> "Corre en cualquier servidor estándar. No hay costo de licencias
> de software externo — todo el código es propio."

**"¿Puede conectarse con nuestro sistema de reservas?"**
> "Sí, el sistema tiene una arquitectura que permite conectarse
> con otros sistemas. Es una integración que podemos planificar juntos."

---

## VOCABULARIO — USAR SIEMPRE

✅ "Mantenimiento **predictivo** vs. reactivo"
✅ "**Reducción de costos** operativos"
✅ "**Disponibilidad** de habitaciones"
✅ "**Retorno sobre la inversión** (ROI)"
✅ "**Eficiencia operativa**"
✅ "**Datos en tiempo real**"
✅ "**Toma de decisiones basada en datos**"
✅ "**Escalable** según el crecimiento del hotel"

## PALABRAS A EVITAR

❌ Flask, Python, PostgreSQL, Docker
❌ "Machine learning", "modelo", "entrenamiento"
❌ "Bug", "error", "excepción", "código", "función"

→ Reemplaza todo por: **"el sistema"**, **"la IA"**, **"la plataforma"**

---

## CHECKLIST ANTES DE LA REUNIÓN

- [ ] App corriendo en `localhost:5000` o servidor accesible
- [ ] Ir a `/automatizacion` → "Generar Equipos Demo" → "Generar Plan (4 semanas)"
- [ ] Ir a `/predicciones` → "Ejecutar Predicciones"
- [ ] Ir a `/costos` → "Ejecutar Predicción de Costos"
- [ ] Tener una foto cargada en `/vision` para mostrar detección visual
- [ ] Pantalla grande o proyector conectado
- [ ] Practicar el recorrido de la demo 2–3 veces sin leer

---

*Sistema desarrollado con: Python · PostgreSQL · Inteligencia Artificial · Visión por Computadora*
*6 módulos de IA · 14 tablas de base de datos · Interfaz web completa*
