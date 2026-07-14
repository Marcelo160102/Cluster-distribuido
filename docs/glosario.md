# Glosario de Términos Técnicos — Clúster VoIP Distribuido

> **Fase 5 — Documentación Técnica**

---

| Término | Definición |
|---|---|
| **3PC (Three-Phase Commit)** | Protocolo de consenso distribuido en tres fases (CanCommit, PreCommit, DoCommit) que permite commits atómicos sin bloqueo mutuo, a diferencia de 2PC. |
| **ACK** | Acuse de recibo (Acknowledgement). Respuesta positiva en una comunicación entre nodos. |
| **Ansible** | Herramienta de automatización de TI sin agente que usa YAML para definir infraestructura como código. |
| **API Key** | Clave de autenticación enviada en el header HTTP `X-API-Key` para autorizar acceso a los endpoints `/data`. |
| **Balanceo de carga (Load Balancing)** | Técnica para distribuir peticiones entre múltiples servidores. En este proyecto: nginx con round-robin. |
| **Bully Algorithm** | Algoritmo de elección de líder donde el nodo con mayor ID (o prioridad) se convierte en el coordinador. |
| **cAdvisor** | Agente de Google que expone métricas de uso de recursos (CPU, RAM, red, disco) de contenedores Docker. |
| **C4 Model** | Notación estándar para diagramas de arquitectura de software en 4 niveles: Contexto, Contenedores, Componentes y Código. |
| **Consenso distribuido** | Acuerdo entre múltiples nodos sobre un mismo valor o estado, incluso en presencia de fallos. Ej: 3PC. |
| **CRUD** | Create, Read, Update, Delete — operaciones básicas sobre una base de datos. |
| **Docker Compose** | Herramienta para definir y ejecutar aplicaciones multi-contenedor con un archivo YAML. |
| **EndPoint VoIP** | Registro de una extensión telefónica SIP o WebRTC en el clúster. Contiene extensión, protocolo, IP, estado y agente de usuario. |
| **Fail-over** | Proceso automático de transferencia del rol de líder a otro nodo cuando el líder actual falla. |
| **FastAPI** | Framework web Python asíncrono para construir APIs REST con documentación OpenAPI automática. |
| **Grafana** | Plataforma de visualización y dashboards para métricas de monitoreo. |
| **HA (High Availability)** | Capacidad del sistema de mantenerse operativo a pesar de fallos de componentes individuales. |
| **Heartbeat** | Señal periódica entre nodos para verificar que están vivos y funcionando. |
| **HTTP** | Protocolo de transferencia de hipertexto. En el proyecto: comunicación entre nodos (3PC, elecciones). |
| **HTTPS** | HTTP sobre TLS/SSL. En el proyecto: nginx termina TLS, comunicación cliente→LB es cifrada. |
| **httpx** | Biblioteca Python asíncrona para realizar peticiones HTTP. Usada para comunicación entre nodos. |
| **Leader** | Nodo que coordina las escrituras y acepta peticiones POST/PUT/DELETE. Solo uno a la vez. |
| **Latencia** | Tiempo que tarda una petición en completarse. Se mide en milisegundos (ms). |
| **LB (Load Balancer)** | Ver "Balanceo de carga". En el proyecto: nginx. |
| **Middleware** | Capa de software que intercepta peticiones HTTP para agregar funcionalidades (ej: validación de API Key). |
| **Nodo** | Instancia individual del clúster. Cada nodo ejecuta FastAPI + SQLite en un contenedor Docker. |
| **p50 / p95 / p99** | Percentiles de latencia: el 50%/95%/99% de las peticiones están por debajo de ese valor. |
| **Prometheus** | Sistema de monitoreo y alerta que recolecta métricas de los nodos y contenedores. |
| **Protocolo** | Conjunto de reglas para la comunicación entre nodos (3PC, HTTP, Bully). |
| **Quórum** | Número mínimo de nodos que deben estar de acuerdo para que una operación sea válida. En este proyecto: ≥ 2 para 3 nodos. |
| **Round-robin** | Algoritmo de balanceo que distribuye peticiones secuencialmente entre los servidores disponibles. |
| **Sincronización total** | Proceso por el cual un nodo recuperado descarga todo el estado del líder y reemplaza su base de datos local. |
| **Split-brain** | Escenario donde dos nodos se creen líderes simultáneamente, causando inconsistencias. |
| **SQLite WAL** | Modo Write-Ahead Logging de SQLite que permite lecturas concurrentes sin bloquear escrituras. |
| **Throughput** | Cantidad de peticiones procesadas por unidad de tiempo. Se mide en req/s. |
| **TLS** | Transport Layer Security. Protocolo criptográfico para comunicación segura. |
| **Uvicorn** | Servidor ASGI usado para ejecutar FastAPI. |
| **VoIP** | Voice over IP. Tecnología para transmitir voz sobre redes IP. |
| **WAL (Write-Ahead Log)** | Ver "SQLite WAL". Técnica de logging que escribe cambios en un log antes de aplicar a la base de datos. |
| **wrk/hey** | Herramientas de línea de comandos para realizar benchmarks HTTP. Reemplazadas por `tests/benchmark.py` en este proyecto. |
