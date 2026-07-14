# Manual de Operación — Clúster VoIP Distribuido

> **Fase 5 — Documentación Técnica**

---

## 1. Instalación

### 1.1 Requisitos mínimos

| Recurso | Mínimo | Recomendado |
|---|---|---|
| Docker Engine | 24+ | 27+ |
| Docker Compose Plugin | 2.0+ | 2.27+ |
| RAM | 2 GB | 4 GB |
| Disco | 1 GB libre | 10 GB |
| Git | 2.0+ | 2.45+ |
| Python (solo para benchmarks) | 3.11+ | 3.12+ |

### 1.2 Instalación paso a paso

```bash
# 1. Clonar el repositorio
git clone git@github.com:Marcelo160102/Cluster-distribuido.git
cd Cluster-distribuido

# 2. Generar certificado SSL (para HTTPS)
bash scripts/gen-certs.sh

# 3. (Opcional) Configurar API Key personalizada
export API_KEY=mi-clave-segura-2026

# 4. Construir y levantar el clúster
docker compose up --build -d

# 5. Verificar que todos los servicios están UP
docker ps --format 'table {{.Names}}\t{{.Status}}'

# 6. Smoke test
bash tests/smoke_test.sh
```

### 1.3 Servicios esperados

| Contenedor | Propósito | Puerto |
|---|---|---|
| `cluster-distribuido-nodo1-1` | Nodo 1 del clúster | 8000 (interno) |
| `cluster-distribuido-nodo2-1` | Nodo 2 del clúster | 8000 (interno) |
| `cluster-distribuido-nodo3-1` | Nodo 3 del clúster | 8000 (interno) |
| `cluster-distribuido-loadbalancer-1` | nginx load balancer | 80, 443 |
| `cluster-distribuido-cadvisor-1` | Métricas de contenedores | 8080 |
| `cluster-distribuido-prometheus-1` | Almacenamiento de métricas | 9090 |
| `cluster-distribuido-grafana-1` | Dashboards de monitoreo | 3000 |

---

## 2. Operación

### 2.1 CRUD de endpoints VoIP

Todos los endpoints `/data` requieren header `X-API-Key`.

**Crear un endpoint:**
```bash
curl -s -X POST http://localhost:80/data \
  -H "Content-Type: application/json" \
  -H "X-API-Key: cluster-demo-key-2026" \
  -d '{"data": "{\"extension\": \"101\", \"protocol\": \"SIP\", \"ip_address\": \"192.168.1.10\", \"status\": \"online\", \"user_agent\": \"Yealink T48S\"}"}'
```

**Listar todos:**
```bash
curl -s http://localhost:80/data -H "X-API-Key: cluster-demo-key-2026"
```

**Obtener por ID:**
```bash
curl -s http://localhost:80/data/<UUID> -H "X-API-Key: cluster-demo-key-2026"
```

**Actualizar:**
```bash
curl -s -X PUT http://localhost:80/data/<UUID> \
  -H "Content-Type: application/json" \
  -H "X-API-Key: cluster-demo-key-2026" \
  -d '{"data": "{\"extension\": \"101\", \"protocol\": \"SIP\", \"ip_address\": \"192.168.1.10\", \"status\": \"busy\", \"user_agent\": \"Yealink T48S\"}"}'
```

**Eliminar:**
```bash
curl -s -X DELETE http://localhost:80/data/<UUID> \
  -H "X-API-Key: cluster-demo-key-2026"
```

### 2.2 Endpoints públicos vs internos

| Endpoint | Público | Requiere API Key | Descripción |
|---|---|---|---|
| `GET /` | Sí | No | Info del nodo |
| `GET /health` | Sí | No | Health check |
| `GET /data` | Sí | Sí | Listar endpoints VoIP |
| `GET /data/{id}` | Sí | Sí | Obtener endpoint VoIP |
| `POST /data` | Sí | Sí | Crear endpoint VoIP |
| `PUT /data/{id}` | Sí | Sí | Actualizar endpoint VoIP |
| `DELETE /data/{id}` | Sí | Sí | Eliminar endpoint VoIP |
| `GET /cluster/sync` | No | No | Sincronización total (entre nodos) |
| `POST /cluster/3pc/*` | No | No | Protocolo 3PC (entre nodos) |
| `POST /election` | No | No | Elección Bully (entre nodos) |
| `POST /leader-announce` | No | No | Anuncio de líder (entre nodos) |

### 2.3 Logs

```bash
# Todos los servicios en tiempo real
docker compose logs -f

# Solo un nodo
docker compose logs -f nodo1

# Filtrar por 3PC
docker compose logs nodo2 | grep "\[3PC\]"

# Filtrar por elecciones
docker compose logs nodo3 | grep "\[ELECCIÓN\]"

# Últimas 50 líneas
docker compose logs --tail=50 nodo1
```

### 2.4 Monitoreo

```bash
# cAdvisor (métricas Docker)
http://localhost:8080

# Prometheus (consulta de métricas)
http://localhost:9090

# Grafana (dashboards) — admin/admin
http://localhost:3000
```

---

## 3. Mantenimiento

### 3.1 Backup de datos

```bash
# Backup de la base de datos de un nodo
docker compose exec -T nodo1 cat /app/data/data.db > backup-$(date +%F).db

# Backup de todos los nodos
for n in nodo1 nodo2 nodo3; do
  docker compose exec -T $n cat /app/data/data.db > backup-${n}-$(date +%F).db
done
```

### 3.2 Restore

```bash
# Detener el clúster
docker compose down

# Copiar backup al volumen (los volúmenes están en /var/lib/docker/volumes/)
# Opción más simple: levantar un contenedor temporal
docker run --rm -v cluster-distribuido_nodo1_data:/data -v $(pwd):/backup alpine \
  cp /backup/backup-2026-07-13.db /data/data.db

# Reiniciar
docker compose up -d
```

### 3.3 Actualización

```bash
git pull origin main
docker compose up --build -d
```

### 3.4 Reinicio completo (estado limpio)

```bash
# Detener y eliminar volúmenes (pierde datos)
docker compose down -v

# Reconstruir y levantar
docker compose up --build -d
```

### 3.5 Solución de problemas

| Problema | Causa posible | Solución |
|---|---|---|
| `docker compose up` falla | Puerto 80/443 ocupado | `sudo lsof -i :80`, detener el proceso |
| Nodo unhealthy | Error de importación de Python | `docker compose logs nodo1` |
| POST devuelve 503 | Request llegó a un seguidor | Reintentar (round-robin) o enviar directo al líder |
| POST devuelve 401 | Falta API Key o incorrecta | Agregar header `X-API-Key` |
| HTTPS no funciona | Certificado no generado | `bash scripts/gen-certs.sh` |
| Split-brain (2 líderes) | Elección inconsistente | `docker compose down && docker compose up -d` |
| Grafana no arranca | Puerto 3000 ocupado | Cambiar puerto en docker-compose.yml |

---

## 4. Arquitectura del sistema

Ver `docs/arquitectura.md` para diagramas C4 detallados (Contexto, Contenedores, Componentes, Código/3PC).

### Flujo de una escritura (3PC)

```
Cliente → POST /data (LB) → Líder
  1. CanCommit: líder pregunta a seguidores si pueden procesar
  2. PreCommit: seguidores preparan buffer
  3. DoCommit: líder escribe local + seguidores consolidan
  4. Respuesta 200 al cliente
```

### Flujo de fail-over

```
Líder muere → Seguidores detectan por heartbeat (~9s)
→ Nodo con mayor ID inicia elección Bully
→ Nuevo líder se autodeclara y anuncia a todos
→ Nuevo líder acepta escrituras (~10s total)
```

---

## 5. Referencias

- FastAPI: https://fastapi.tiangolo.com
- 3PC Protocol: https://en.wikipedia.org/wiki/Three-phase_commit
- Bully Algorithm: https://en.wikipedia.org/wiki/Bully_algorithm
- Docker Compose: https://docs.docker.com/compose
- Prometheus: https://prometheus.io
- Grafana: https://grafana.com
