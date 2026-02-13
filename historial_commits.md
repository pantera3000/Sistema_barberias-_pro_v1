# Historial de Cambios (Commits)

Lista de todos los puntos de restauración creados en este proyecto.

| Hash | Fecha y Hora | Descripción |
| :--- | :--- | :--- |
| **Commit** | 2026-02-11 18:08:00 | - **Phase 35: Interfaz Dinámica y Sincronización Pro**<br>- Dashboard dinámico: Los widgets se ocultan/muestran según las features del plan.<br>- Sync Automático: Los cambios en Planes (Superadmin) se propagan de inmediato a todos los negocios.<br>- Refinado de Límites: Se ocultan límites irrelevantes (SMS/Storage en 0) para una interfaz más limpia.<br>- Fix de Sidebar: Barra de progreso de clientes forzada a entero y con estilo de alto contraste. |
| **Commit** | 2026-02-11 12:05:00 | - **Onboarding 2.1: Refinamiento de Flujo y UX**<br>- Prevención de duplicados: No se permiten múltiples `StampRequest` pendientes por cliente.<br>- Éxito Personalizado: La pantalla de éxito muestra el progreso real de la tarjeta + 1 sello pendiente animado.<br>- Nudge Inteligente: El formulario de cumpleaños se oculta automáticamente si el dato ya existe.<br>- Mejora en lógica de sesión para asegurar carga correcta de datos de cliente. |
| **Commit** | 2026-02-11 11:55:00 | - **Retención y Engagement: Perfil Premium (Nudge)**<br>- Añadido banner inteligente en el Dashboad del cliente que detecta perfiles incompletos.<br>- Implementado Modal "Quick-Capture" para DNI, Email y Cumpleaños vía AJAX.<br>- Refuerzo positivo: Celebración con confeti al completar datos personales.<br>- Mejora UX: El cliente se siente incentivado a dar sus datos por "sorpresas". |
| **Commit** | 2026-02-11 11:45:00 | - **UX Refinement: Tarjeta Digital "Fantasma"**<br>- Los nuevos clientes ya no ven el dashboard vacío mientras esperan aprobación.<br>- Implementada visualización de solicitudes pendientes como tarjetas en estado "Validando".<br>- Optimización de la lógica de "Estado Vacío" en el tablero del cliente. |
| **Commit** | 2026-02-11 11:25:00 | - **Mega-Upgrade: Onboarding de Cliente 2.0**<br>- Implementado **Auto-Login** instantáneo tras primer registro vía QR.<br>- Rediseño total de la pantalla de éxito con estética Premium y vista previa de tarjeta digital.<br>- Añadida sección interactiva para captura de **Cumpleaños** tras el registro.<br>- Mejora en la retención: Botón directo al tablero digital del cliente. |
| **Commit** | 2026-02-11 11:20:00 | - **UX Upgrade: Modal de Actividad Diaria vs Descarga Directa**<br>- El botón "Reporte Hoy" ahora abre un modal visual con la actividad detallada del día.<br>- Implementada `daily_activity_api` para carga asíncrona de movimientos.<br>- Botón de "Descargar CSV" movido dentro del modal como opción secundaria.<br>- Fix: Corrección de error de navegación de campos (`card__customer`) en el reporte. |
| **Commit** | 2026-02-11 11:15:00 | - **Mega-Upgrade Dashboard 3.1: Profesional & Funcional**<br>- Rediseño total de la cabecera con estilo minimalista.<br>- Implementada función de **Reporte Diario (Exportación CSV)** funcional.<br>- Nuevo botón de **Compartir Enlace** que copia la URL de registro al portapapeles.<br>- Integración de widget de **Cumpleañeros del Día** con confeti.<br>- Optimización de gráficos de crecimiento y distribución. |
| **Commit** | 2026-02-11 10:45:00 | - **UX Upgrade: Escáner QR Global + Fallback Manual "Plan B"**<br>- Integrado Escáner QR en Modal Global accesible desde cualquier página.<br>- Implementada búsqueda manual AJAX dentro del modal de escaneo como mecanismo de respaldo.<br>- Fix: Corregida ruta de redirección en buscador manual (singular vs plural). |
| **Commit** | 2026-02-11 09:45:00 | - **Fix Navigation UX: Sidebar Inteligente + Preparación QR Modal**<br>- Corregida lógica del Sidebar: Los submenús (Sellos/Marketing) ahora están siempre abiertos pero la iluminación `active` es estrictamente condicional.<br>- Preparación de infraestructura para el Escáner QR Global en Modal. |
| **Commit** | 2026-02-11 02:40:00 | - **Mega-Upgrade UX: Dashboard 2.0, Búsqueda AJAX y Modal Global**<br>- Rediseñado **Dashboard de Dueño 2.0** con estética Glassmorphism y métricas avanzadas (Retención, Caja Estimada).<br>- Implementada **Búsqueda AJAX en tiempo real** para asignación de sellos y puntos (Nombre/Teléfono/DNI).<br>- Nuevo **Modal Global de Asignación** accesible desde el sidebar en todas las páginas.<br>- Fix: Manejo de error cuando un trabajador no tiene avatar (autogeneración de iniciales). |
| **Commit** | 2026-02-11 02:10:00 | - **Mega-Expansión Superadmin: Planes, Monitor, Búsqueda y Auditoría**<br>- Implementado **Buscador Maestro Global** con soporte multientidad.<br>- Nuevo **Sistema de Planes (Básico, Gold, VIP)** con syncing automático de límites.<br>- Creado **Monitor de Uso Visual** con semáforo de consumo.<br>- Dashboard Superadmin con **Timeline de Actividad en Vivo**.<br>- Bugfixes: NameError (is_superuser) y FieldError (customer count). |
| **Commit** | 2026-02-10 20:48:00 | - **Fix: Zona Horaria (Perú) y Notificaciones QR Ultra-Visuales**
    - Sincronización total con hora de Lima para cumpleaños y reportes.
    - Implementado sistema de alertas: Sonido, Toast, Pulsos y Banner Naranja.
    - Refactorizado: Solicitudes QR movidas a su propia página dedicada.
    - Optimización: El sonido solo suena una vez por nueva solicitud (SessionStorage). |
| **Backup** | 2026-02-10 20:48:23 | - **Respado tras corrección de zona horaria y mejoras QR** |
| **Commit** | 2026-02-10 13:20:00 | - **Mejora Premium: WhatsApp con Editor de Mensajes y 6 Plantillas**
    - Añadido **Editor de Mensajes (textarea)** en el modal de WhatsApp para personalización total.
    - Ampliada la librería a **6 plantillas premium** (Puntos, Premios, Fidelización, Cumpleaños, Novedades, Gracias).
    - Refactorizado JS para carga de plantillas en editor y envío codificado. |
| **Commit** | 2026-02-10 13:15:00 | - **Mejora Premium: Perfil 360°, WA Marketing y ADN del Cliente**
    - Implementado **WhatsApp Marketing** con botón flotante y plantillas dinámicas.
    - Algoritmo de **ADN del Cliente**: Frecuencia, Servicio Favorito y Última Visita.
    - Sistema de **Etiquetas (Tags)** de colores con gestión en creación/edición.
    - UX: Visualización de tags en perfil y grid interactivo en formularios. |
| **Backup** | 2026-02-10 13:00:00 | - **Punto de restauración antes de mejoras avanzadas de perfil**
    - Respaldo previo a la implementación de WhatsApp, Estadísticas ADN y Etiquetas. |
| **Backup** | 2026-02-10 12:55:00 | - **Módulo de Auditoría y Gestión Avanzada de Clientes**
    - Implementado **Módulo de Auditoría y Logs** (Modelos, Vistas y Templates).
    - Perfil de Cliente 360° con **Canje Directo** de premios acumulados.
    - Acciones de eliminación con confirmación modal y registro en auditoría.
    - Mejoras UX: nombres cliqueables en listado y visual de premios listos. |
| 0a1b2c3 | 2026-02-09 23:30:00 | - **Mejora: Notificaciones Automáticas (WhatsApp/Email) para Engagement**
    - Implementado Feature Flag `campaigns.auto_notifications` para control SaaS por Superadmin.
    - Creado modelo `NotificationConfig` para gestionar API Keys de WhatsApp y plantillas personalizadas por negocio.
    - Implementados Django Signals para disparar mensajes automáticos cuando falta 1 sello o se completa el premio.
    - Creado comando de gestión `send_expiration_reminders` para avisos de vencimiento (7 días).
    - Integración con API de WhatsApp local (estilo UltraMsg). |
| 428abe2 | 2026-02-09 23:05:00 | - **Mejora: Soporte para múltiples promociones, colores personalizados y vinculación con Premios**
    - Implementado sistema para definir y gestionar múltiples promociones activas simultáneamente.
    - Añadida funcionalidad para personalizar colores de la interfaz por promoción.
    - Establecida vinculación directa entre promociones y premios disponibles. |
| 351624f | 2026-02-09 22:35:00 | Mejora: vigencia de tarjetas y reglas de 'Sello Doble' |
| b6fd59e | 2026-02-09 22:15:00 | Mejora: modo kiosko (QR) y confirmación de sellos escaneados |
| 1da0ca2 | 2026-02-09 22:00:00 | Mejora: paginación AJAX en el historial de clientes |
| 3512060 | 2026-02-09 21:55:00 | Mejora: panel de configuración de negocio y bypass de seguridad |
| 2df87da | 2026-02-09 21:50:00 | Mejora: botón de 'Deshacer' (Undo) en historial de sellos |
| 844258c | 2026-02-09 21:40:00 | Mejora: auditoría de sellos y protección anti-fraude (Time-Lock) |
| 04f3ea4 | 2026-02-09 21:25:00 | Mejora: buscador AJAX real-time con debounce en lista de tarjetas |
| 1b332ca | 2026-02-09 21:05:00 | Fix: eliminada restricción UNIQUE para acumulación infinita |
| df4fb8b | 2026-02-09 21:00:00 | Mejora: vista de tarjetas agrupada por cliente y acumulación |
| e5c3ed0 | 2026-02-09 20:50:00 | Mejora: dashboard visual con gráficos interactivos (Chart.js) |
| cc5e95c | 2026-02-09 20:40:00 | Checkpoint: sistema de sellos optimizado |
| 8b44b2b | 2026-02-09 16:15:00 | Corrección: script movido a bloque extra_js para carga del DOM |
| adbe8de | 2026-02-09 16:15:00 | Corrección: sincronización de búsqueda y visibilidad en modal |
| c010e74 | 2026-02-09 16:00:00 | Mejora: buscador AJAX más rápido y UX optimizada en modal |
| 18efd81 | 2026-02-09 15:55:00 | Corrección: visibilidad y UX del buscador AJAX en modal |
| e42b142 | 2026-02-09 15:45:00 | Mejora: modal de nueva tarjeta con buscador AJAX y auto-asignación |
| b9beff2 | 2026-02-09 11:20:00 | Mejora: flujo de canje acumulativo y app del cliente para sellos |
| d3518bb | 2026-02-09 10:55:00 | Mejora: buscador, cinta de estadísticas y sello directo en tarjetas |
| 3d8a303 | 2026-02-09 10:45:00 | Mejora: Tarjeta de sellos visual (estilo punch-card) |
| 2b778cf | 2026-02-09 10:17:40 | Registro: Omitir respaldos en Git |
| 42d810c | 2026-02-09 10:14:55 | Mejora: Fecha de nacimiento parcial (Año opcional) en Clientes |
| 67aa273 | 2026-02-09 09:58:24 | Registro: Creación del archivo de historial de commits |
| f36dede | 2026-02-09 09:55:28 | Checkpoint: Fase 13 completada y datos demo cargados |
2. 🛡️ Seguridad y Anti-Fraude (Time-Lock)