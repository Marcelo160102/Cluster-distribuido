# Clúster Distribuido con Replicación de Datos

Sistema de 3 nodos que forman un clúster distribuido con replicación Maestro-Esclavo, algoritmo de elección Bully y tolerancia a fallos. Cada nodo funciona como un registro de **Endpoints VoIP activos** (SIP, WebRTC, PJSIP) con persistencia en SQLite, comunicación asíncrona vía HTTP y sincronización automática ante recuperación de caídas.

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    RED DOCKER (cluster-net)                 │
│                                                             │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐     │
│  │   Nodo 1     │   │   Nodo 2     │   │   Nodo 3     │     │
│  │  (LÍDER)     │   │  (SEGUIDOR)  │   │  (SEGUIDOR)  │     │
│  │              │   │              │   │              │     │
│  │ FastAPI      │   │ FastAPI      │   │ FastAPI      │     │
│  │ SQLite (WAL) │   │ SQLite (WAL) │   │ SQLite (WAL) │     │
│  │ Puerto 8001  │   │ Puerto 8002  │   │ Puerto 8003  │     │
│  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘     │
│         │                  │                  │             │
│         └──────────────────┴──────────────────┘             │
│              HTTP (httpx) asíncrono entre nodos             │
└─────────────────────────────────────────────────────────────┘
```

### Estructura del Proyecto

```
cluster-distribuido/
├── docker-compose.yml           # Orquestación de 3 contenedores
├── Dockerfile                   # Imagen Python 3.11-slim + curl
├── requirements.txt             # fastapi, uvicorn, httpx, pydantic
├── .env.example                 # Plantilla de variables de entorno
├── .gitignore
├── .dockerignore
├── README.md
│
├── app/
│   ├── main.py                  # Punto de entrada FastAPI + heartbeat loop
│   │
│   ├── core/                    # Infraestructura base
│   │   ├── config.py            # Variables de entorno y constantes
│   │   └── database.py          # SQLite en WAL + CRUD parametrizado
│   │
│   ├── domain/                  # Modelos de dominio
│   │   └── schemas.py           # VoipEndpoint, ItemCreate, ReplicaRequest, etc.
│   │
│   ├── api/                     # Capa de presentación (routers)
│   │   ├── routes_data.py       # CRUD público (/data)
│   │   └── routes_cluster.py    # Endpoints internos (/health, /replicate, /election, /sync)
│   │
│   └── services/                # Capa de negocio
│       ├── replication.py       # Replicación a seguidores + quórum
│       ├── leader_election.py   # Algoritmo Bully
│       └── node_client.py       # Cliente HTTP asíncrono (httpx)
│
└── tests/
    └── test_integration.py      # Pruebas de integración
```

### Flujo de Datos (Escritura)

```
Cliente ──POST /data──→ LÍDER
                          ├── 1. Valida con Pydantic (VoipEndpoint)
                          ├── 2. Persiste en SQLite local
                          ├── 3. Replica a SEGUIDORES (POST /replicate)
                          │     ├── nodo2 → ACK
                          │     └── nodo3 → ACK
                          ├── 4. Quórum ≥ 2 → OK → responde 201
                          └── 5. Quórum < 2 → rollback + auto-degradación → 503
```

### Protocolo entre Nodos

| Endpoint | Origen → Destino | Propósito |
|---|---|---|
| `GET /health` | Cualquiera → Cualquiera | Heartbeat (cada 3s) |
| `POST /replicate` | Líder → Seguidores | Replicar operación CRUD |
| `POST /election` | Seguidor → Todos | Iniciar elección Bully |
| `POST /leader-announce` | Nuevo líder → Todos | Anunciar liderazgo |
| `GET /cluster/sync` | Seguidor → Líder | Sincronización total post-caída |

---

## Requisitos Previos

| Herramienta | Versión Mínima | Instalación |
|---|---|---|
| Docker | 24+ | [Linux](https://docs.docker.com/engine/install/) / [Windows](https://docs.docker.com/desktop/install/windows-install/) |
| Docker Compose | v2+ | Incluido en Docker Desktop o `docker compose` (plugin) |
| curl | cualquier | `apt install curl` / `pacman -S curl` |
| jq | cualquier (opcional) | Para formatear JSON: `apt install jq` |

### Windows (WSL2)

1. Instalar [Docker Desktop](https://docs.docker.com/desktop/install/windows-install/) con backend WSL2
2. Abrir una terminal **WSL2** (Ubuntu recomendado) o **Git Bash**
3. Clonar el repositorio dentro del filesystem de Linux (`/home/usuario/...`)
4. Todos los comandos de este tutorial (`curl`, `jq`, `docker compose`) deben ejecutarse en la terminal WSL2, **no en cmd/PowerShell**, a menos que tengas `curl` y `jq` instalados nativamente en Windows

### Linux

Docker Engine nativo + plugin Compose.

### VSCode

Extensiones recomendadas:
- **Docker** (ms-azuretools.vscode-docker) — ver logs, contenedores, redes
- **Python** (ms-python.python) — resaltado de sintaxis
- **Even Better TOML** (opcional)

---

## Instalación y Ejecución

### 1. Clonar el repositorio

```bash
git clone <url-del-repositorio> cluster-distribuido
cd cluster-distribuido
```

### 2. Construir y levantar los 3 nodos

```bash
docker compose up --build
```

La primera vez descargará `python:3.11-slim` e instalará las dependencias (~2-5 minutos).

### 3. Verificar que los 3 nodos están vivos

En una terminal separada (o nueva pestaña):

```bash
curl -s http://localhost:8001/ | jq .
curl -s http://localhost:8002/ | jq .
curl -s http://localhost:8003/ | jq .
```

Salida esperada (el líder será el nodo con mayor ID, normalmente nodo3):

```json
{
  "node_id": "nodo3",
  "role": "leader",
  "status": "alive",
  "leader": null
}
```

Los seguidores mostrarán `"role": "follower"` y `"leader": "nodo3"`.

### 4. Ver logs en vivo

```bash
docker compose logs -f
```

Para filtrar por nodo:

```bash
docker compose logs -f nodo1
```

O desde VSCode: icono de Docker → clic derecho en el contenedor → "View Logs".

---

## Tutorial de Pruebas Paso a Paso

### Prueba 1: Replicación Exitosa

Crear un endpoint VoIP en el líder:

```bash
# Identificar el líder
curl -s http://localhost:8001/ | jq .role
curl -s http://localhost:8002/ | jq .role
curl -s http://localhost:8003/ | jq .role

# POST al líder
curl -s -X POST http://localhost:8003/data \
  -H "Content-Type: application/json" \
  -d '{"data": "{\"extension\": \"101\", \"protocol\": \"SIP\", \"ip_address\": \"192.168.1.50\", \"status\": \"online\", \"user_agent\": \"Yealink T48S\"}"}' | jq .
```

Respuesta esperada:

```json
{
  "id": "cece2ac8-...",
  "data": "{\"extension\": \"101\", ...}",
  "created_at": "2026-...",
  "updated_at": "2026-..."
}
```

Verificar que los datos se replicaron en los 3 nodos:

```bash
curl -s http://localhost:8001/data | jq .
curl -s http://localhost:8002/data | jq .
curl -s http://localhost:8003/data | jq .
```

Los 3 deben devolver el mismo contenido. Confirmación visual en logs:

```
nodo2-1  | INFO: ... "POST /replicate HTTP/1.1" 200 OK
nodo3-1  | INFO: ... "POST /replicate HTTP/1.1" 200 OK
```

---

### Prueba 2: Sincronización Correcta (UPDATE + DELETE)

Actualizar el estado de "online" a "busy":

```bash
# Obtener el ID del registro creado
ID=$(curl -s http://localhost:8003/data | jq -r '.[0].id')

# Actualizar al líder
curl -s -X PUT "http://localhost:8003/data/$ID" \
  -H "Content-Type: application/json" \
  -d '{"data": "{\"extension\": \"101\", \"protocol\": \"SIP\", \"ip_address\": \"192.168.1.50\", \"status\": \"busy\", \"user_agent\": \"Yealink T48S\"}"}' | jq .
```

Crear un segundo registro:

```bash
curl -s -X POST http://localhost:8003/data \
  -H "Content-Type: application/json" \
  -d '{"data": "{\"extension\": \"102\", \"protocol\": \"WebRTC\", \"ip_address\": \"192.168.1.51\", \"status\": \"online\", \"user_agent\": \"Jitsi Meet\"}"}' | jq .
```

Verificar consistencia:

```bash
echo "--- nodo1 ---"
curl -s http://localhost:8001/data | jq .
echo "--- nodo2 ---"
curl -s http://localhost:8002/data | jq .
echo "--- nodo3 ---"
curl -s http://localhost:8003/data | jq .
```

Eliminar el primer registro:

```bash
curl -s -X DELETE "http://localhost:8003/data/$ID" | jq .
```

Verificar que el registro desapareció de los 3 nodos.

---

### Prueba 3: Caída del Líder + Elección Automática

```bash
# 1. Identificar el líder actual
curl -s http://localhost:8003/ | jq .role  # debe decir "leader"

# 2. Detener el líder
docker stop cluster-distribuido-nodo3-1

# 3. Esperar ~10 segundos (3 heartbeats fallidos)
sleep 10

# 4. Verificar que otro nodo asumió el liderazgo
curl -s http://localhost:8001/ | jq .
curl -s http://localhost:8002/ | jq .
```

Logs esperados:

```
nodo2-1  | [HEARTBEAT] LÍDER nodo3 declarado MUERTO
nodo2-1  | [ELECTION] nodo2 se autodeclara LÍDER
nodo1-1  | ... "POST /leader-announce HTTP/1.1" 200 OK
```

El nuevo líder será **nodo2** (el de mayor ID entre los vivos).

---

### Prueba 4: Continuidad del Servicio

Con el nuevo líder (nodo2), crear datos:

```bash
curl -s -X POST http://localhost:8002/data \
  -H "Content-Type: application/json" \
  -d '{"data": "{\"extension\": \"103\", \"protocol\": \"PJSIP\", \"ip_address\": \"10.0.0.1\", \"status\": \"online\", \"user_agent\": \"Asterisk\"}"}' | jq .
```

Verificar replicación en nodo1:

```bash
curl -s http://localhost:8001/data | jq .
```

El servicio continúa funcionando a pesar de la caída del líder original.

---

### Prueba 5: Recuperación del Nodo Caído (Sincronización Total)

```bash
# 1. Levantar nodo3
docker start cluster-distribuido-nodo3-1

# 2. Esperar ~8 segundos (heartbeat detecta recuperación)
sleep 8

# 3. Verificar que nodo3 se unió como seguidor
curl -s http://localhost:8003/ | jq .
# Debe mostrar: "role": "follower", "leader": "nodo2"

# 4. Verificar que nodo3 tiene todos los datos (incluso los creados mientras estuvo caído)
curl -s http://localhost:8003/data | jq .
```

Logs de sincronización:

```
nodo1-1  | [HEARTBEAT] http://nodo3:8000 RECUPERADO
nodo2-1  | [HEARTBEAT] http://nodo3:8000 RECUPERADO
nodo1-1  | [SYNC] Solicitando sincronización total a http://nodo2:8000
nodo1-1  | [SYNC] Recibidos X registros del líder
nodo1-1  | [SYNC] Sincronización total completada: X registros insertados
```

---

### Prueba 6: Partición de Red (Opcional)

Simular un aislamiento de red real sin detener el proceso:

```bash
# 1. Identificar el nombre de la red Docker
docker network ls
# Buscar: cluster-distribuido_cluster-net o similar

# 2. Aislar nodo2 de la red
docker network disconnect cluster-distribuido_cluster-net cluster-distribuido-nodo2-1

# 3. Verificar que nodo3 asume liderazgo
curl -s http://localhost:8003/ | jq .

# 4. Intentar escribir en nodo1 (seguidor) → 503
curl -s -X POST http://localhost:8001/data \
  -H "Content-Type: application/json" \
  -d '{"data": "{\"extension\": \"199\", \"protocol\": \"SIP\", \"ip_address\": \"10.0.0.99\", \"status\": \"online\", \"user_agent\": \"Test\"}"}' | jq .

# 5. Reconectar nodo2
docker network connect cluster-distribuido_cluster-net cluster-distribuido-nodo2-1
sleep 8

# 6. Verificar que se reincorpora correctamente
curl -s http://localhost:8002/ | jq .
curl -s http://localhost:8002/data | jq .
```

---

## Solución de Problemas

### Error: `unable to open database file`

El directorio `/app/data` no tiene permisos para `appuser`. Solución incluida en el Dockerfile (crea el directorio con `chown` antes del `USER appuser`). Si persiste, verificar:

```bash
docker compose build --no-cache
```

### Error: `Attribute "app" not found in module`

El archivo `app/main.py` está vacío o tiene errores de importación. Verificar que la estructura de carpetas coincida con los imports en `main.py`.

### Error: `Cannot connect to the Docker daemon`

En Linux, asegurar que el servicio está corriendo:

```bash
sudo systemctl enable --now docker
```

En Windows, abrir Docker Desktop y esperar a que el motor inicie.

### Error: `network cluster-net not found`

Docker Compose asigna un prefijo al nombre de red. Usar:

```bash
docker network ls | grep cluster
docker network disconnect <nombre-exacto> <contenedor>
```

### Error: `Replication quorum failed`

El líder necesitaba ACK de al menos 2 nodos pero no lo consiguió (ej: 2 nodos vivos pero uno no responde). El líder se auto-degrada a seguidor. Verificar que todos los contenedores estén en ejecución:

```bash
docker ps
```
