# Plan de Orquestación — Clúster Distribuido con Replicación de Datos

---

## 1. Resumen del Proyecto

**Nombre:** Implementación de un Clúster Distribuido con Replicación de Datos  
**Materia:** Sistemas Distribuidos  
**Modalidad:** Prototipo funcional + Informe técnico + Video demostrativo  

### ¿Qué es exactamente este proyecto?

Es un **sistema de 3 nodos** que forman un clúster distribuido. Cada nodo funciona como un **servidor autónomo** que:

- Expone una **API REST** para operaciones CRUD sobre datos.
- Se comunica con los otros nodos para **replicar datos** en tiempo real.
- Participa en un **algoritmo de elección de líder** (Bully o Ring).
- Puede **fallar** y el clúster se recupera automáticamente.

Es, en esencia, una **base de datos distribuidas minimalista** con tolerancia a fallos y autorreparación, orquestada con **Docker Compose**.

### ¿Qué NO es?

- No es un bot ni una automatización de procesos.
- No es un sistema de mensajería (aunque los nodos se envían mensajes entre sí).
- No es una aplicación web con interfaz de usuario (solo APIs).

---

## 2. Stack Tecnológico Recomendado

| Componente | Tecnología | Justificación |
|---|---|---|
| **Lenguaje** | Python 3.11+ | Curva de aprendizaje baja, bibliotecas maduras para HTTP y concurrencia, ideal para prototipado rápido |
| **Framework API** | FastAPI (con Uvicorn) | Asíncrono, rendimiento alto, documentación OpenAPI automática (`/docs`) |
| **Base de datos** | SQLite (por nodo) | Sin servidor externo, cada nodo tiene su propio archivo `.db`, facilita replicación y pruebas. **Configurado en modo WAL para mejor concurrencia.** |
| **Serialización** | JSON | Formato estándar para comunicación entre nodos |
| **Cliente HTTP** | `httpx` (asíncrono) | Para que los nodos se comuniquen entre sí |
| **Contenedores** | Docker + Docker Compose | Entorno reproducible, red aislada, facilita orquestación local y en la nube |
| **Algoritmo de líder** | Bully Algorithm | Más sencillo de implementar que Ring; los 3 nodos se conocen entre sí |
| **Replicación** | Maestro-Esclavo (Primary-Replica) | El líder acepta escrituras y replica a los seguidores; los seguidores sirven lecturas |

### Dependencias Python (`requirements.txt`)

```
fastapi==0.115.0
uvicorn[standard]==0.30.0
httpx==0.27.0
pydantic==2.9.0
```

---

## 3. Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                     RED DOCKER (bridge)                      │
│                                                             │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   │
│  │   Nodo 1     │   │   Nodo 2     │   │   Nodo 3     │   │
│  │  (LÍDER)     │   │  (SEGUIDOR)  │   │  (SEGUIDOR)  │   │
│  │              │   │              │   │              │   │
│  │ FastAPI      │   │ FastAPI      │   │ FastAPI      │   │
│  │ SQLite       │   │ SQLite       │   │ SQLite       │   │
│  │ Puerto 8001  │   │ Puerto 8002  │   │ Puerto 8003  │   │
│  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘   │
│         │                  │                  │           │
│         └──────────────────┴──────────────────┘           │
│                    HTTP (httpx) entre nodos                │
└─────────────────────────────────────────────────────────────┘
```

### Componentes internos de cada nodo

```
┌──────────────────────────────────┐
│             NODO                  │
│  ┌────────────────────────────┐  │
│  │     FastAPI Server         │  │
│  │  - POST /data             │  │
│  │  - GET /data              │  │
│  │  - PUT /data/{id}         │  │
│  │  - DELETE /data/{id}      │  │
│  │  - GET /health            │  │
│  │  - POST /replicate        │  │
│  │  - POST /election         │  │
│  │  - POST /leader-announce  │  │
│  └────────────────────────────┘  │
│  ┌────────────────────────────┐  │
│  │   Motor de Replicación     │  │
│  │   - Envía copias a otros   │  │
│  │   - Recibe réplicas        │  │
│  │   - Resuelve conflictos    │  │
│  └────────────────────────────┘  │
│  ┌────────────────────────────┐  │
│  │   Módulo de Liderazgo      │  │
│  │   - Bully Algorithm        │  │
│  │   - Heartbeat detector     │  │
│  │   - Timeout management     │  │
│  └────────────────────────────┘  │
│  ┌────────────────────────────┐  │
│  │   Almacenamiento Local     │  │
│  │   - SQLite (data.db)       │  │
│  │   - metadata.json          │  │
│  └────────────────────────────┘  │
└──────────────────────────────────┘
```

### Mensajes intercambiados entre nodos (API interna)

| Endpoint | Origen → Destino | Propósito |
|---|---|---|
| `POST /replicate` | Líder → Seguidores | Enviar operación de escritura para replicar |
| `GET /health` | Cualquiera → Cualquiera | Heartbeat / verificar si el nodo está vivo |
| `POST /election` | Seguidor → Todos | Iniciar elección (Bully: nodo con mayor ID gana) |
| `POST /leader-announce` | Nuevo líder → Todos | Anunciar quién es el nuevo líder |
| `GET /cluster/sync` | Seguidor → Líder | Sincronización total por estado completo — el seguidor recuperado obtiene todo el listado de endpoints VoIP |

---

## 4. Fases del Plan de Orquestación

---

### FASE 1: Diseño y Planificación (Día 1)

**Objetivo:** Tener el blueprint completo antes de escribir una sola línea de código.

**Actividades:**

1.1. **Dibujar diagrama de arquitectura** (Draw.io / Mermaid)  
1.2. **Definir el esquema de datos** — tabla `items` con campos: `id (UUID)`, `data (TEXT)` (JSON stringificado con la información del endpoint VoIP), `created_at`, `updated_at`. El contexto del proyecto es el **Registro Distribuido de Endpoints VoIP (SIP, WebRTC, etc.)**, donde cada registro representa una extensión activa en una infraestructura de comunicaciones (extensiones SIP tradicionales, WebPhones basados en WebRTC, etc.).  
1.3. **Especificar cada endpoint REST** con request/response (contrato de API)  
1.4. **Seleccionar el algoritmo de elección**: se recomienda **Bully Algorithm**  
1.5. **Acordar el modelo de replicación**: Maestro-Esclavo  
1.6. **Crear repositorio Git** con `.gitignore` (Python, Docker, SQLite) y `README.md` inicial

**Entregable:** Documento de diseño compartido (Notion / Google Docs) + repo Git inicializado.

---

### FASE 2: Setup del Entorno de Desarrollo (Día 2)

**Objetivo:** Entorno reproducible y funcionando en ambas máquinas locales y en la nube.

**Actividades:**

2.1. **Crear estructura de carpetas del proyecto:**

```
cluster-distribuido/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example  # Archivo de ejemplo; el .env real debe ser .gitignore-d
├── .gitignore
├── README.md
├── src/
│   ├── __init__.py
│   ├── main.py              # Punto de entrada FastAPI
│   ├── config.py            # Configuración por nodo
│   ├── database.py          # Conexión SQLite + esquema
│   ├── models.py            # Modelos Pydantic
│   ├── routes_data.py       # Endpoints CRUD
│   ├── routes_cluster.py    # Endpoints de cluster (health, elección, replicación)
│   ├── replication.py       # Motor de replicación
│   ├── leader_election.py   # Algoritmo Bully
│   └── node_client.py       # Cliente HTTP para comunicación entre nodos
├── tests/
│   ├── test_replication.py
│   └── test_election.py
└── docs/
    └── arquitectura.png
```

2.2. **Crear `Dockerfile`** (imagen base Python 3.11-slim)  
2.3. **Crear `docker-compose.yml`** con 3 servicios (`nodo1`, `nodo2`, `nodo3`) más una red bridge  
2.4. **Verificar** que `docker compose up --build` levanta los 3 contenedores sin errores

**Entregable:** Proyecto corriendo localmente con `docker compose up`.

---

2.5. **Ejemplos de Archivos de Configuración (Base)**

**`Dockerfile`:**
```dockerfile
FROM python:3.11-slim-buster

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src

# Recomendación: ejecutar como usuario no-root
RUN adduser --system --group appuser
USER appuser

ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**`docker-compose.yml`:**
```yaml
version: '3.8'

services:
  nodo1:
    build: .
    ports:
      - "8001:8000" # Mapear puerto del host al puerto del contenedor
    environment:
      - NODE_ID=nodo1
      - NODE_PORT=8000
      - PEERS=http://nodo2:8000,http://nodo3:8000
    volumes:
      - nodo1_data:/app/data # Volumen persistente para SQLite
    networks:
      - cluster-net
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 5s
      timeout: 3s
      retries: 3
    # restart: on-failure # Habilitar restart policy si se desea

  nodo2:
    build: .
    ports:
      - "8002:8000"
    environment:
      - NODE_ID=nodo2
      - NODE_PORT=8000
      - PEERS=http://nodo1:8000,http://nodo3:8000
    volumes:
      - nodo2_data:/app/data
    networks:
      - cluster-net
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 5s
      timeout: 3s
      retries: 3

  nodo3:
    build: .
    ports:
      - "8003:8000"
    environment:
      - NODE_ID=nodo3
      - NODE_PORT=8000
      - PEERS=http://nodo1:8000,http://nodo2:8000
    volumes:
      - nodo3_data:/app/data
    networks:
      - cluster-net
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 5s
      timeout: 3s
      retries: 3

volumes:
  nodo1_data:
  nodo2_data:
  nodo3_data:

networks:
  cluster-net:
    driver: bridge
```

**`.env.example`:**
```ini
# .env.example
# Este archivo no debe ser versionado en Git.
# Usar .env y añadirlo a .gitignore

# Configuración de Nodos
NODE_ID=nodo1
NODE_PORT=8000 # Puerto interno del contenedor
PEERS=http://nodo2:8000,http://nodo3:8000 # Lista de otros nodos
LEADER_ID=None # Inicialmente no hay líder
```

---

### FASE 3: Implementación del Núcleo del Nodo (Días 3-4)

**Objetivo:** Cada nodo funciona como servidor independiente con su base de datos local.

**Actividades:**

3.1. **`config.py`** — Variables de entorno: `NODE_ID`, `NODE_PORT`, `PEERS` (lista estática de otros nodos para Docker Compose), `LEADER_ID`
3.2. **`database.py`** — Inicializar SQLite, crear tabla `items`. **Importante:** Configurar `PRAGMA journal_mode=WAL;` para mayor concurrencia y usar **consultas parametrizadas** en todas las funciones CRUD (`get_all`, `get_by_id`, `create`, `update`, `delete`) para prevenir SQL Injection.  
3.3. **`models.py`** — Modelos Pydantic: `ItemCreate`, `ItemUpdate`, `ItemResponse`, `ReplicaRequest`, `ElectionMessage`, `HealthStatus`

    **Esquema VoIP (contenido del campo `data` almacenado como JSON stringificado):**
    ```python
    class VoipEndpoint(BaseModel):
        extension: str       # Número de extensión (ej. "101", "2001")
        protocol: str        # Protocolo del endpoint (ej. "SIP", "WebRTC")
        ip_address: str      # Dirección IP del endpoint (ej. "192.168.1.50")
        status: str          # Estado del endpoint (ej. "online", "offline", "busy")
        user_agent: str      # Cliente VoIP (ej. "Yealink T48S", "Jitsi Meet", "Linphone")
    ```

    - El campo `data` de la tabla `items` almacenará este modelo serializado a JSON (`.model_dump_json()`).
    - Al leer un registro, se parsea con `VoipEndpoint.model_validate_json()` para validar y acceder tipadamente.  
3.4. **`routes_data.py`** — Endpoints CRUD públicos:
    - `POST /data` — Crear registro VoIP (solo líder). Ejemplo de payload:
      ```json
      {
        "data": "{\"extension\": \"101\", \"protocol\": \"SIP\", \"ip_address\": \"192.168.1.50\", \"status\": \"online\", \"user_agent\": \"Yealink T48S\"}"
      }
      ```
    - `GET /data` — Listar todos los endpoints VoIP registrados (cualquier nodo).
    - `GET /data/{id}` — Obtener un endpoint VoIP por su ID (cualquier nodo).
    - `PUT /data/{id}` — Actualizar datos de un endpoint VoIP (solo líder).
    - `DELETE /data/{id}` — Eliminar un endpoint VoIP del registro (solo líder).
3.5. **`main.py`** — Arrancar FastAPI con Uvicorn, incluir routers

**Regla de negocio clave:** Si un nodo no es líder y recibe una escritura (`POST`, `PUT`, `DELETE`), debe **redirigir** la petición al líder o responder `503 Service Unavailable` con la dirección del líder.

**Entregable:** Cada nodo responde a peticiones HTTP en `localhost:8001`, `localhost:8002`, `localhost:8003`.

---

### FASE 4: Comunicación entre Nodos (Días 5-6)

**Objetivo:** Los 3 nodos se descubren y monitorean entre sí.

**Actividades:**

4.1. **`node_client.py`** — Cliente HTTP asíncrono con funciones:
    - `health_check(node_url)` → `GET /health`
    - `send_replica(node_url, data)` → `POST /replicate`
    - `send_election(node_url, msg)` → `POST /election`
    - `announce_leader(node_url, leader_id)` → `POST /leader-announce`
    - Manejo de `HTTP_TIMEOUT = 1.5` segundos (configurado en `config.py`) y captura de `httpx.TimeoutException` (nodo caído o no responde)

4.2. **`routes_cluster.py`** — Endpoints internos:
    - `GET /health` — Retorna `{"node_id": "nodo1", "role": "leader|follower", "status": "alive"}`
    - `POST /replicate` — Recibe datos del líder y los persiste localmente
    - `POST /election` — Recibe mensaje de elección (implementación del algoritmo en Fase 6)
    - `POST /leader-announce` — Recibe anuncio de nuevo líder y actualiza `config.LEADER_ID`

4.3. **Heartbeat loop** — Cada nodo ejecuta un `asyncio` task en background que cada `HEARTBEAT_INTERVAL = 3.0` segundos (configurado en `config.py`) verifica `GET /health` de todos los peers. Si un nodo no responde tras `MAX_FAILED_ATTEMPTS = 3` intentos consecutivos (cada intento con `HTTP_TIMEOUT = 1.5` s), se declara muerto.

**Entregable:** Logs que muestran heartbeats periódicos entre nodos.

---

### FASE 5: Replicación de Datos (Días 7-9)

**Objetivo:** Las escrituras en el líder se propagan automáticamente a los seguidores.

**Actividades:**

5.1. **Implementar `replication.py`:**
    - Función `replicate_to_followers(operation, data)`:
        - `operation`: `"create"`, `"update"`, `"delete"`
        - Envía `POST /replicate` a cada seguidor con el payload
        - Espera confirmación (ACK) de al menos 2 seguidores (quórum de escritura >= 2 para 3 nodos, N/2 + 1)
        - **Regla crítica de negocio:** Si el líder no logra recibir el ACK de la mayoría del clúster (quórum < 2) debido a un fallo de red, debe:
            1. Ejecutar rollback de la escritura en su base de datos local.
            2. Responder al cliente con `503 Service Unavailable`.
            3. Auto-degradarse inmediatamente al rol de Seguidor.

5.2. **Integrar en `routes_data.py`:**
    - Después de escribir en SQLite local, llamar a `replicate_to_followers()`
    - Si la replicación falla según la regla de quórum (Fase 5.1), ejecutar rollback de la escritura local, responder `503 Service Unavailable` y auto-degradar el nodo a Seguidor

5.3. **Sincronización de datos (Nodos Recuperados) — Sincronización Total por Estado Completo:**
    - Cuando un nodo seguidor se reincorpora tras una caída, debe ejecutar la siguiente estrategia oficial:
        1. **Vaciar** su tabla local de SQLite (`DELETE FROM items`).
        2. Realizar una petición `GET /cluster/sync` al líder para obtener el listado completo de endpoints VoIP.
        3. **Insertar** todos los registros recibidos en una **única transacción atómica** (iniciar transacción, ejecutar todos los INSERT, hacer commit).
        4. Durante este proceso, el nodo no debe aceptar escrituras externas ni participar en elecciones.
    - **CRÍTICO:** La transacción única garantiza atomicidad: si algo falla a medio camino, el nodo mantiene su estado vacío y reintenta la sincronización completa.

**Entregable:** Al crear un registro en el líder (ej. `POST /data` en nodo1), aparecen los mismos datos en nodo2 y nodo3 automáticamente.

---

### FASE 6: Algoritmo de Elección de Líder (Días 10-12)

**Objetivo:** Implementar el **Bully Algorithm**. Cuando el líder cae, los seguidores eligen uno nuevo automáticamente.

**Actividades:**

6.1. **Implementar `leader_election.py` (Bully Algorithm):**

**Flujo de Elección (incluyendo el arranque inicial):**
1. **Arranque/Detección de Fallo:** Al iniciar un nodo, o cuando un nodo detecta que el líder actual no responde (Fase 4.3), entra en estado de elección.
2. **Mensaje de Elección:** El nodo envía un mensaje "ELECTION" a todos los nodos con un ID mayor que el suyo.
3. **Respuesta "OK":** Si un nodo con un ID mayor responde "OK" (está vivo), ese nodo toma la iniciativa de la elección y el nodo actual espera el anuncio del nuevo líder.
4. **Auto-declaración de Líder:** Si ningún nodo con un ID mayor responde después de un `timeout` (ej. 1 segundo), este nodo se autodeclara líder.
5. **Anuncio de Líder (COORDINATOR):** El nuevo líder envía un mensaje "LEADER" (también conocido como "COORDINATOR") a todos los nodos restantes.
6. **Actualización de Líder:** Todos los nodos actualizan su `LEADER_ID` con el ID del nuevo líder.

6.2. **Integrar en `routes_cluster.py`:**
    - `POST /election` — Recibe mensaje ELECTION, responde OK si el ID local es mayor
    - `POST /leader-announce` — Recibe anuncio de nuevo líder y actualiza `config.LEADER_ID`

6.3. **Timers, Timeouts y Reintentos (configurados en `config.py`):**
    - `HEARTBEAT_INTERVAL = 3.0` — segundos entre cada ping de health check.
    - `HTTP_TIMEOUT = 1.5` — segundos máximos de espera en cada petición HTTP entre nodos.
    - `MAX_FAILED_ATTEMPTS = 3` — intentos fallidos consecutivos antes de declarar muerto a un nodo.
    - Timeout de espera por respuesta "OK" en elección: `HTTP_TIMEOUT` (1.5 s).
    - Detección de caída de líder: `MAX_FAILED_ATTEMPTS × HTTP_TIMEOUT ≈ 4.5 s` (sin backoff) o con backoff exponencial hasta ~12-15 s.
    - **Importante:** El cliente `httpx` en `node_client.py` debe estar preparado para capturar la excepción `httpx.TimeoutException` provocada por estos límites. Implementar **backoff exponencial** en los reintentos para evitar saturar nodos con problemas temporales.

6.4. **Transición de rol y Mitigación de Split-Brain:**
    - Cuando un nodo se convierte en líder, empieza a aceptar y coordinar escrituras.
    - Cuando un nodo se convierte en seguidor, rechaza escrituras directas (las redirige al líder conocido) y solo acepta réplicas del líder.
    - **Auto-degradación por quórum:** Un líder que no logra replicar una escritura a la mayoría (quórum < 2) debe ejecutar rollback local, responder `503 Service Unavailable` y auto-degradarse inmediatamente a Seguidor (ver Fase 5.1).
    - **Mitigación de Split-Brain:** La implementación del Bully Algorithm debe ser robusta. Si dos nodos se creen líderes simultáneamente (split-brain), el nodo con el **mayor ID siempre prevalece** y el otro debe revertir a seguidor o iniciar una nueva elección si no hay un líder claro.

**Entregable:** Matar el líder (`docker stop nodo1`), observar que otro nodo toma el liderazgo y el servicio continúa.

---

### FASE 7: Pruebas de Funcionamiento (Días 13-14)

**Objetivo:** Demostrar todos los escenarios obligatorios de la rúbrica.

**Actividades:**

7.1. **Prueba 1 — Replicación exitosa:**
    - `POST /data` al líder con payload VoIP real:
      ```json
      {
        "data": "{\"extension\": \"101\", \"protocol\": \"SIP\", \"ip_address\": \"192.168.1.50\", \"status\": \"online\", \"user_agent\": \"Yealink T48S\"}"
      }
      ```
      → `GET /data` en cada seguidor → verificar que el endpoint VoIP aparece replicado

7.2. **Prueba 2 — Sincronización correcta:**
    - Registrar varios endpoints VoIP (extensiones 101, 102, 103 con distintos protocolos y estados), modificar el estado de uno a "busy", eliminar otro → verificar estado consistente en los 3 nodos

7.3. **Prueba 3 — Caída del líder (simulación de partición de red):**
    - `docker network disconnect cluster-net nodo1` → verificar que nodo2 y nodo3 detectan la pérdida de conectividad con el líder
    - Esta técnica simula una partición de red real (latencias severas e incomunicación) sin apagar el proceso, validando que el sistema tolera fallos de red sin colapsar

7.4. **Prueba 4 — Elección automática:**
    - Tras la caída del líder, verificar que un nuevo líder se elige en < 15 segundos
    - Verificar logs: `NEW LEADER ELECTED: nodo2`

7.5. **Prueba 5 — Continuidad del servicio:**
    - Con el líder aislado de la red, hacer `POST /data` al nuevo líder con payload VoIP real → datos se replican al otro seguidor
    - Restaurar la conectividad del nodo aislado (`docker network connect cluster-net nodo1`) → verificar que se sincroniza mediante la Sincronización Total por Estado Completo

7.6. **Crear script de pruebas automatizado** (`tests/run_tests.sh`) que ejecute todos los escenarios.

**Entregable:** Evidencias (capturas, logs, script de test) y video demostrativo.

---

### FASE 8: Despliegue en la Nube (Días 15-16)

**Objetivo:** El clúster corre en la nube y ambos integrantes pueden acceder y monitorear.

**Actividades:**

8.1. **Elegir proveedor cloud (gratuito / estudiante):**
    - **Opción A:** Oracle Cloud Free Tier (VM siempre gratis, 4 OCPU, 24 GB RAM)
    - **Opción B:** AWS Free Tier (t2.micro, 1 año gratis)
    - **Opción C:** Google Cloud Free Tier (e2-micro, 90 días + crédito $300)
    - **Opción D:** DigitalOcean ($200 crédito para estudiantes de GitHub Education)
    - **Opción E:** VPS contratado (Hetzner ~€4/mes)

8.2. **Aprovisionar una VM** (1 instancia es suficiente; los 3 nodos van en Docker Compose dentro de la misma VM)

8.3. **Configurar la VM:**
    ```bash
    # Instalar Docker y Docker Compose
    sudo apt update && sudo apt install -y docker.io docker-compose-plugin
    sudo systemctl enable docker
    # Clonar repositorio
    git clone <repo-url> /opt/cluster
    cd /opt/cluster
    sudo docker compose up -d --build
    ```

8.4. **Abrir puertos en firewall / security group:**
    - `8001`, `8002`, `8003` — API de cada nodo (acceso público o restringido por IP)
    - `22` — SSH (restringir a IPs del equipo)

8.5. **Configurar HTTPS (opcional pero recomendado):**
    - Usar Nginx como reverse proxy + Let's Encrypt / Caddy
    - O acceder directamente por IP + puerto con HTTP para pruebas

8.6. **Monitoreo básico:**
    - Logs de Docker: `docker compose logs -f`
    - Script simple `health_status.sh` que consulta `GET /health` de cada nodo cada 5 segundos
    - Opcional: Configurar Prometheus + Grafana si se desea algo más visual

8.7. **Acceso para ambos integrantes:**
    - Compartir IP pública y puertos
    - Cada integrante puede hacer `curl http://<IP>:8001/data` desde su máquina
    - Crear un usuario `team` en la VM para que ambos hagan SSH con su clave pública

**Entregable:** Clúster funcionando en la nube, accesible desde internet.

---

### FASE 9: Documentación y Entregables Finales (Días 17-20)

**Objetivo:** Completar la rúbrica al 100%.

**Actividades:**

9.1. **Informe técnico (15 páginas máx.):**
    - Portada, introducción, objetivos
    - Arquitectura (diagrama + descripción)
    - Implementación (explicación de cada componente)
    - Pruebas realizadas (capturas de pantalla)
    - Conclusiones y lecciones aprendidas
    - Referencias

9.2. **Diagrama de arquitectura final** (exportar a PNG)

9.3. **Video demostrativo (10 min máx.):**
    - Mostrar los 3 nodos funcionando
    - Crear/actualizar/eliminar datos
    - Replicación en tiempo real
    - Matar el líder → elección → continuidad
    - Recuperar nodo caído → sincronización
    - Mostrar tanto local como en la nube

9.4. **Presentación final:**
    - Slides con: problema, solución, arquitectura, demo, resultados

9.5. **Código fuente documentado:**
    - README con guía de ejecución (local y cloud)
    - Comentarios docstring en funciones clave
    - `requirements.txt` y `Dockerfile` listos

**Entregable:** Todo el repositorio + PDF + video.

---

## 5. Cronograma Resumido

| Fase | Días | Descripción |
|---|---|---|
| F1 | 1 | Diseño y planificación |
| F2 | 1 | Setup Docker + estructura |
| F3 | 2 | Núcleo del nodo (FastAPI + SQLite) |
| F4 | 2 | Comunicación entre nodos (heartbeat) |
| F5 | 3 | Replicación de datos |
| F6 | 3 | Algoritmo de elección (Bully) |
| F7 | 2 | Pruebas de funcionamiento |
| F8 | 2 | Despliegue en la nube |
| F9 | 4 | Documentación y entregables |
| **Total** | **20** | |

---

## 6. Distribución de Tareas (2 personas)

| Persona | Áreas |
|---|---|
| **Integrante A** | F3 (núcleo del nodo), F5 (replicación), F7 (pruebas), F9 (informe + video) |
| **Integrante B** | F4 (comunicación entre nodos), F6 (elección de líder), F8 (despliegue nube), F9 (presentación) |
| **Ambos** | F1 (diseño), F2 (setup), F9 (diagrama + README) |

---

## 7. Consideraciones de Seguridad y Vulnerabilidades (CRÍTICO)

| Riesgo | Mitigación |
|---|---|
| **Exposición de APIs internas** (Líder, Replicación, Elección) a internet | **CRÍTICO:** **NO** exponer públicamente los puertos de Docker Compose (8001, 8002, 8003) en la VM de la nube. Si el acceso a la API es necesario desde fuera, implementar un Reverse Proxy (Nginx/Caddy) que solo redirija el tráfico externo a un puerto específico del líder (ej. 80 o 443 con HTTPS) y que solo acceda al endpoint `/data`. El tráfico entre nodos debe permanecer en la red privada de Docker (o una VPN en multi-VM). Restringir acceso SSH (puerto 22) por IP en firewall. |
| **Sin autenticación en APIs (CRUD externas)** | **Recomendado:** Para un prototipo educativo, es aceptable. Para cualquier uso fuera de este contexto, agregar JWT o API Keys para endpoints CRUD públicos (`/data`). |
| **Gestión de secretos (`.env`)** | El archivo `.env` (o equivalente) **NO debe ser versionado en Git**. Para despliegue en la nube, las variables de entorno deben ser inyectadas de forma segura (ej. desde el gestor de la nube, Docker Secrets). |
| **Riesgo de SQL Injection** | **Obligatorio:** `database.py` debe usar **consultas parametrizadas** en todas las operaciones SQLite. Esto es fundamental. |
| **Permisos de Archivos en Contenedor** | Ejecutar el proceso principal del contenedor con un **usuario no-root** (ej. `USER appuser` en Dockerfile). Asegurar permisos restrictivos en los directorios de datos de SQLite. |
| Sin HTTPS | Para API externa en la nube, **muy recomendado** usar Nginx/Caddy con Let's Encrypt. Para comunicación inter-nodo en red Docker interna, HTTP es aceptable. |
| Sin cifrado entre nodos (multi-VM) | En la red Docker interna es aceptable. En despliegues multi-VM, usar **TLS mutuo** para asegurar la comunicación entre nodos. |
| SQLite no es concurrente | SQLite soporta **WAL mode**. **Configurar WAL explícitamente** en `database.py` para mejorar la concurrencia de lecturas y escrituras. Para 3 nodos con bajo volumen de escrituras (solo líder), es suficiente. |
| **Sin persistencia en Docker para DB** | **Obligatorio:** Usar **volúmenes Docker** para los archivos SQLite (`data.db`) de cada nodo para garantizar la persistencia de los datos entre reinicios de contenedores. Esto se ha añadido al ejemplo de `docker-compose.yml`. |
| **Condición de carrera en sincronización de nodo recuperado** | **Solución oficial — Sincronización Total por Estado Completo:** El nodo recuperado vacía su tabla local y solicita al líder el listado completo vía `GET /cluster/sync`, insertándolo en una única transacción atómica. Durante este proceso el nodo no acepta escrituras externas. |
| **Quórum de escritura débil** | **CRÍTICO:** Quórum de escritura >= **2** para 3 nodos (N/2 + 1). Si el líder no recibe ACK de la mayoría, debe ejecutar rollback local, responder `503 Service Unavailable` y auto-degradarse a Seguidor inmediatamente. |
| **Split-Brain (múltiples líderes)** | **Mitigación 1:** La implementación del Bully Algorithm debe ser robusta para resolver disputas, donde el nodo con el ID más alto siempre gana y propaga su liderazgo. **Mitigación 2 (Quórum):** Si el líder no logra replicar una escritura a la mayoría (ACK < 2 de 3 nodos), debe hacer rollback local, responder `503 Service Unavailable` y auto-degradarse a Seguidor, evitando escrituras inconsistentes. |
| **Reintentos sin backoff** | Implementar **backoff exponencial** en el cliente HTTP (`node_client.py`) para evitar saturar nodos con problemas temporales. |

---

## 8. Notas Clave

- **El líder no es un punto único de fallo** porque el algoritmo Bully elige uno nuevo automáticamente.
- **Los 3 nodos pueden estar en la misma máquina** (Docker Compose) o en 3 VMs separadas. Se recomienda empezar local y luego pasar a 1 VM con Docker Compose.
- **Persistencia de Datos:** Es crucial el uso de **volúmenes Docker** para los archivos de base de datos SQLite de cada nodo, garantizando que los datos no se pierdan al recrear contenedores.
- **FastAPI expone `/docs`** con Swagger UI, lo que facilita las pruebas interactivas sin necesidad de Postman.
- **Cada integrante debe tener Docker instalado** en su máquina local para desarrollo paralelo.
- Usar **Git con ramas** (`main`, `feature/replication`, `feature/election`) para trabajar en paralelo sin conflictos.

---

*Documento generado como guía de orquestación para el proyecto final de Sistemas Distribuidos 2026.*
