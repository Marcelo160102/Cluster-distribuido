# Clúster Distribuido VoIP — Servicios Web con Alta Disponibilidad

Clúster de 3 nodos para registro distribuido de endpoints VoIP con protocolo de consenso **3PC (Three-Phase Commit)**, algoritmo de elección **Bully**, balanceo de carga con **nginx**, seguridad **HTTPS + API Key** y monitoreo con **Prometheus + Grafana**.

---

## Arquitectura

```
Cliente ──HTTP/HTTPS──→ nginx LB (:80/:443)
                              │
                ┌─────────────┼─────────────┐
                ▼             ▼             ▼
            nodo1 ── 3PC ──→ nodo2 ── 3PC ──→ nodo3
            (8000)   ←────   (8000)   ←────   (8000)
               │                              │
               └────────── Bully + Heartbeat ──┘

Monitoreo: cAdvisor → Prometheus → Grafana
```

### Componentes

| Servicio | Tecnología | Propósito |
|---|---|---|
| 3× nodo | FastAPI + SQLite WAL | API REST + persistencia local |
| Load Balancer | nginx:alpine | Round-robin, termina TLS |
| cAdvisor | gcr.io/cadvisor | Métricas de contenedores |
| Prometheus | prom/prometheus | Almacenamiento de métricas |
| Grafana | grafana/grafana | Dashboards de monitoreo |

---

## Requisitos

- Docker 24+ con Docker Compose plugin
- Git
- curl

---

## Instalación

```bash
git clone git@github.com:Marcelo160102/Cluster-distribuido.git
cd Cluster-distribuido

# Generar certificado SSL (para HTTPS)
bash scripts/gen-certs.sh

# (Opcional) API Key personalizada
export API_KEY=mi-clave-segura

# Construir y levantar
docker compose up --build -d

# Verificar estado
docker ps --format 'table {{.Names}}\t{{.Status}}'

# Smoke test
bash tests/smoke_test.sh
```

### Servicios esperados (7 contenedores)

```
cluster-distribuido-nodo1-1          Up (healthy)
cluster-distribuido-nodo2-1          Up (healthy)
cluster-distribuido-nodo3-1          Up (healthy)
cluster-distribuido-loadbalancer-1   Up
cluster-distribuido-cadvisor-1       Up
cluster-distribuido-prometheus-1     Up
cluster-distribuido-grafana-1        Up
```

---

## Pruebas de Funcionamiento

Todas las pruebas se realizan a través del **Load Balancer** en `localhost:80`.

> **Importante:** Los endpoints `/data` requieren header `X-API-Key`.
> Clave por defecto: `cluster-demo-key-2026`.

### Prueba 1: Health y estado del clúster

```bash
# Health vía LB
curl -s http://localhost:80/health

# Info del nodo
curl -s http://localhost:80/
```

### Prueba 2: Crear endpoint VoIP (replicación 3PC)

```bash
# Crear (nginx reintenta automáticamente si recibe 503 de un seguidor)
curl -s -X POST http://localhost:80/data \
  -H "Content-Type: application/json" \
  -H "X-API-Key: cluster-demo-key-2026" \
  -d '{"data": "{\"extension\": \"101\", \"protocol\": \"SIP\", \"ip_address\": \"192.168.1.50\", \"status\": \"online\", \"user_agent\": \"Yealink T48S\"}"}'

# Leer (cualquier nodo)
curl -s http://localhost:80/data -H "X-API-Key: cluster-demo-key-2026"
```

### Prueba 3: Actualizar y eliminar

```bash
# Obtener ID del primer registro
ID=$(curl -s http://localhost:80/data -H "X-API-Key: cluster-demo-key-2026" | python3 -c "import sys,json; print(json.load(sys.stdin)[0]['id'])")

# Actualizar
curl -s -X PUT "http://localhost:80/data/$ID" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: cluster-demo-key-2026" \
  -d '{"data": "{\"extension\": \"101\", \"protocol\": \"SIP\", \"ip_address\": \"192.168.1.50\", \"status\": \"busy\", \"user_agent\": \"Yealink T48S\"}"}'

# Eliminar
curl -s -X DELETE "http://localhost:80/data/$ID" \
  -H "X-API-Key: cluster-demo-key-2026"
```

### Prueba 4: Fail-over del líder

```bash
# 1. Identificar líder actual
curl -s http://localhost:80/health

# 2. Matar el líder
docker stop cluster-distribuido-nodo3-1

# 3. Esperar detección (~10s: 3 heartbeats × 3s + elección)
sleep 12

# 4. Verificar nuevo líder
curl -s http://localhost:80/health

# 5. Escribir en el nuevo líder (nginx reintenta automáticamente si cae en seguidor)
curl -s -X POST http://localhost:80/data \
  -H "Content-Type: application/json" \
  -H "X-API-Key: cluster-demo-key-2026" \
  -d '{"data": "{\"extension\": \"200\", \"protocol\": \"WebRTC\", \"ip_address\": \"10.0.0.2\", \"status\": \"online\", \"user_agent\": \"Jitsi\"}"}'

# 6. Recuperar el nodo caído
docker start cluster-distribuido-nodo3-1
sleep 8

# 7. Verificar que se sincronizó
curl -s http://localhost:80/data -H "X-API-Key: cluster-demo-key-2026"
```

### Prueba 5: Seguridad (HTTPS + API Key)

```bash
# Sin API Key → 401
curl -s http://localhost:80/data

# API Key incorrecta → 401
curl -s http://localhost:80/data -H "X-API-Key: wrong"

# HTTPS con cert self-signed
curl -sk https://localhost:443/data -H "X-API-Key: cluster-demo-key-2026"
```

### Prueba 6: Monitoreo

```bash
# cAdvisor — métricas de contenedores
curl -s http://localhost:8080/metrics | head -5

# Prometheus — targets de scraping
curl -s 'http://localhost:9090/api/v1/targets' | python3 -m json.tool

# Grafana — login (admin/admin)
http://localhost:3000
```

### Smoke test automatizado

```bash
bash tests/smoke_test.sh
```

### Benchmark de rendimiento

```bash
pip install httpx  # si no está instalado
python3 tests/benchmark.py http://localhost 200 10
```

---

## Documentación

| Documento | Descripción |
|---|---|
| `docs/INFORME-COMPLETO.md` | Informe técnico consolidado con toda la documentación del proyecto |
| `docs/arquitectura.md` | Diagramas C4 (Contexto, Contenedores, Componentes, Código/3PC) |

---

## Despliegue con Ansible (VM remota)

```bash
# 1. Editar inventario con IP real
nano ansible/inventory.ini

# 2. Provisionar VM
ansible-playbook -i ansible/inventory.ini ansible/playbook-provision.yml

# 3. Desplegar clúster
ansible-playbook -i ansible/inventory.ini ansible/playbook-deploy.yml
```

---

## Estructura del Proyecto

```
Cluster-distribuido/
├── ansible/                    # IaC: playbooks de Ansible
├── app/                        # Código de cada nodo
│   ├── api/                    #   Routers FastAPI
│   ├── core/                   #   Config + SQLite
│   ├── domain/                 #   Modelos Pydantic
│   └── services/               #   3PC, Bully, node_client
├── docs/                       # Documentación técnica (INFORME-COMPLETO.md, arquitectura.md)
├── monitoring/                 # Config de Prometheus
├── scripts/                    # Scripts auxiliares (gen-certs.sh)
├── tests/                      # Smoke test + benchmark
├── docker-compose.yml          # 7 servicios
├── Dockerfile                  # python:3.11-slim + curl
├── nginx-location-common.conf  # Proxy settings DRY (incluido por nginx.conf)
├── nginx.conf                  # LB con proxy_next_upstream + HTTPS
└── .gitignore                  # Ignora certs/, docs/archive/
```

---

## Stack Tecnológico

| Componente | Tecnología |
|---|---|
| Lenguaje | Python 3.11 |
| API | FastAPI + Uvicorn |
| Base de datos | SQLite (WAL) |
| Comunicación entre nodos | httpx (AsyncClient) |
| Consenso | 3PC (Three-Phase Commit) |
| Elección de líder | Bully Algorithm |
| Balanceador | nginx:alpine |
| Contenedores | Docker + Docker Compose |
| Monitoreo | cAdvisor + Prometheus + Grafana |
| Orquestación | Ansible |
| Seguridad | API Key + HTTPS (self-signed) |

---

*Proyecto de Sistemas Distribuidos 2026 — Clúster de servicios web con registro de endpoints VoIP.*
