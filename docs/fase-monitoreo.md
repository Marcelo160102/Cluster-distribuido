# Fase de Monitoreo — Clúster Distribuido con Replicación de Datos

## Objetivo General

Agregar una interfaz visual que permita observar en tiempo real el estado del clúster: rol de cada nodo (líder/seguidor), cantidad de endpoints VoIP registrados, eventos de elección, caídas y recuperaciones. Esto facilita la comprensión del sistema para el docente y quienes revisen el proyecto.

---

## Opción A: Prometheus + Grafana (Recomendada)

Sistema de monitoreo profesional con stack estándar de la industria.

### Arquitectura

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Nodo 1       │     │    Nodo 2       │     │    Nodo 3       │
│  /metrics       │     │  /metrics       │     │  /metrics       │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                      │                      │
         └──────────────────────┼──────────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │      Prometheus       │
                    │  (scrape cada 5s)     │
                    └───────────┬───────────┘
                                │
                    ┌───────────▼───────────┐
                    │       Grafana         │
                    │  Dashboard visual     │
                    │  Puerto :3000         │
                    └───────────────────────┘
```

### Archivos a crear/modificar

| Archivo | Acción | Propósito |
|---|---|---|
| `app/api/routes_metrics.py` | **Crear** | Endpoint `/metrics` con métricas Prometheus |
| `monitoring/prometheus.yml` | **Crear** | Config de targets (nodo1:8000, nodo2:8000, nodo3:8000) |
| `monitoring/grafana-dashboard.json` | **Crear** | Dashboard precargado con gráficos |
| `docker-compose.yml` | **Modificar** | Agregar servicios `prometheus` y `grafana` |
| `requirements.txt` | **Modificar** | Agregar `prometheus-client` |
| `Dockerfile` | **Sin cambios** | |
| `README.md` | **Actualizar** | Agregar sección de monitoreo |

### Paso a paso

#### 1. Agregar dependencia

En `requirements.txt`:

```
prometheus-client==0.21.0
```

#### 2. Crear endpoint de métricas

Archivo: `app/api/routes_metrics.py`

```python
from prometheus_client import Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import APIRouter, Response

import app.core.config as cfg
from app.core.database import get_all

router = APIRouter()

node_info = Gauge("cluster_node_info", "Información del nodo", ["node_id", "role"])
items_total = Gauge("cluster_items_total", "Cantidad total de items en SQLite")
leader_changes = Gauge("cluster_leader_changes", "Número de cambios de líder")


@router.get("/metrics")
async def metrics():
    role = "leader" if cfg.IS_LEADER else "follower"
    node_info.labels(node_id=cfg.NODE_ID, role=role).set(1)
    items = get_all()
    items_total.set(len(items))
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
```

#### 3. Registrar el router en `app/main.py`

Agregar:

```python
from app.api.routes_metrics import router as metrics_router
app.include_router(metrics_router)
```

#### 4. Crear configuración de Prometheus

Archivo: `monitoring/prometheus.yml`

```yaml
global:
  scrape_interval: 5s

scrape_configs:
  - job_name: "cluster-nodos"
    static_configs:
      - targets:
          - "nodo1:8000"
          - "nodo2:8000"
          - "nodo3:8000"
    metrics_path: "/metrics"
```

#### 5. Agregar servicios al docker-compose.yml

```yaml
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    networks:
      - cluster-net
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_INSTALL_PLUGINS=
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana-dashboard.json:/etc/grafana/provisioning/dashboards/dashboard.json
    networks:
      - cluster-net
    restart: unless-stopped

volumes:
  nodo1_data:
  nodo2_data:
  nodo3_data:
  grafana_data:           # ← agregar
```

#### 6. Crear Dashboard de Grafana (provisionado)

Archivo: `monitoring/grafana-dashboard.json` (contenido básico auto-generado en: `localhost:3000` → Create dashboard → Export JSON)

O simplificado: configurar datasource y dashboard manualmente desde la UI de Grafana en `http://localhost:3000` (admin/admin).

#### 7. Reconstruir y levantar

```bash
docker compose up --build
```

### Verificación

1. `http://localhost:8001/metrics` — métricas crudas del nodo1
2. `http://localhost:9090` — consola de Prometheus (query: `cluster_items_total`)
3. `http://localhost:3000` — Grafana (usuario: admin, pass: admin)
   - Configurar datasource: Prometheus → `http://prometheus:9090`
   - Importar dashboard o crear uno con gráficos de `cluster_node_info`, `cluster_items_total`

---

## Opción B: Dashboard Personalizado (Liviano)

Un 4º contenedor con FastAPI + HTML/CSS/JS que muestra tarjetas visuales con el estado de los 3 nodos en tiempo real.

### Arquitectura

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Nodo 1       │     │    Nodo 2       │     │    Nodo 3       │
│  GET /health    │     │  GET /health    │     │  GET /health    │
│  GET /data      │     │  GET /data      │     │  GET /data      │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                      │                      │
         └──────────────────────┼──────────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │   Dashboard (Web UI)  │
                    │   Puerto :8080        │
                    │   FastAPI + Jinja2    │
                    └───────────────────────┘
```

### Archivos a crear

| Archivo | Propósito |
|---|---|
| `dashboard/main.py` | Servidor FastAPI que consulta los 3 nodos y sirve HTML |
| `dashboard/templates/index.html` | Página visual con tarjetas de estado |
| `dashboard/static/style.css` | Estilos CSS |
| `dashboard/requirements.txt` | Dependencias (fastapi, uvicorn, httpx) |
| `dashboard/Dockerfile` | Imagen para el contenedor dashboard |
| `docker-compose.yml` | Agregar servicio `dashboard` |

### Paso a paso

#### 1. Crear estructura

```
dashboard/
├── main.py
├── requirements.txt
├── Dockerfile
├── static/
│   └── style.css
└── templates/
    └── index.html
```

#### 2. `dashboard/main.py`

```python
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

NODOS = [
    {"id": "nodo1", "url": "http://nodo1:8000"},
    {"id": "nodo2", "url": "http://nodo2:8000"},
    {"id": "nodo3", "url": "http://nodo3:8000"},
]


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    estados = []
    for nodo in NODOS:
        try:
            async with httpx.AsyncClient(timeout=2) as c:
                h = await c.get(f"{nodo['url']}/health")
                health = h.json()
                d = await c.get(f"{nodo['url']}/data")
                data = d.json()
                estados.append({
                    "id": nodo["id"],
                    "alive": True,
                    "role": health.get("role", "unknown"),
                    "leader": health.get("leader"),
                    "items": len(data),
                })
        except Exception:
            estados.append({
                "id": nodo["id"],
                "alive": False,
                "role": "dead",
                "leader": None,
                "items": 0,
            })
    return templates.TemplateResponse("index.html", {"request": request, "nodos": estados})
```

#### 3. `dashboard/templates/index.html`

```html
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - Clúster Distribuido</title>
    <link rel="stylesheet" href="/static/style.css">
    <meta http-equiv="refresh" content="5">
</head>
<body>
    <h1>📊 Clúster Distribuido — Estado en Tiempo Real</h1>
    <div class="grid">
        {% for nodo in nodos %}
        <div class="card {{ 'alive' if nodo.alive else 'dead' }}">
            <h2>{{ nodo.id }}</h2>
            <p><strong>Estado:</strong> {{ '🟢 Vivo' if nodo.alive else '🔴 Caído' }}</p>
            <p><strong>Rol:</strong> {{ nodo.role }}</p>
            <p><strong>Líder:</strong> {{ nodo.leader if nodo.leader else '🎯 Este nodo' }}</p>
            <p><strong>Endpoints:</strong> {{ nodo.items }}</p>
        </div>
        {% endfor %}
    </div>
</body>
</html>
```

#### 4. `dashboard/static/style.css`

```css
body { font-family: system-ui, sans-serif; background: #0f172a; color: #e2e8f0; padding: 2rem; }
h1 { text-align: center; margin-bottom: 2rem; }
.grid { display: flex; gap: 2rem; justify-content: center; flex-wrap: wrap; }
.card { background: #1e293b; border-radius: 1rem; padding: 2rem; width: 250px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
.card.alive { border-left: 4px solid #22c55e; }
.card.dead { border-left: 4px solid #ef4444; opacity: 0.6; }
.card h2 { margin: 0 0 1rem; }
.card p { margin: 0.5rem 0; }
```

#### 5. `dashboard/requirements.txt`

```
fastapi==0.115.0
uvicorn[standard]==0.30.0
httpx==0.27.0
jinja2==3.1.4
```

#### 6. `dashboard/Dockerfile`

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

#### 7. Agregar servicio al `docker-compose.yml`

```yaml
  dashboard:
    build: ./dashboard
    ports:
      - "8080:8080"
    networks:
      - cluster-net
    depends_on:
      - nodo1
      - nodo2
      - nodo3
```

### Verificación

Abrir `http://localhost:8080` en el navegador. Se ven 3 tarjetas que se actualizan cada 5 segundos con el estado, rol, líder y cantidad de endpoints registrados.

---

## Comparación entre Opciones

| Aspecto | Opción A (Prometheus + Grafana) | Opción B (Dashboard propio) |
|---|---|---|
| **Peso** | ~500 MB extra | ~150 MB extra |
| **Instalación** | 7 pasos | 7 pasos |
| **Profesionalismo** | Alto (estándar industria) | Medio (solución casera) |
| **Visualización** | Gráficos históricos, timelines, alertas | Tarjetas en tiempo real |
| **Configuración** | Requiere provisionar dashboard en Grafana | Auto-contenido, abre y funciona |
| **Valor curricular** | Alto (Prometheus/Grafana skills) | Bajo |
| **Tiempo estimado** | 2-3 horas | 1-2 horas |

---

## Recomendación

Comenzar con la **Opción B** por su simplicidad y porque el objetivo es que el docente vea el estado del clúster de forma clara. Si sobra tiempo o se quiere agregar más valor profesional, migrar o complementar con la **Opción A**.

Ambas opciones son compatibles entre sí — se pueden tener las dos ejecutándose al mismo tiempo.

---

## Actualización del README

Al finalizar cualquiera de las dos opciones, agregar al `README.md` una sección:

### Monitoreo (al final de la tabla de contenido)

```
## Monitoreo

### Dashboard Visual (Opción B)
`http://localhost:8080` — Interfaz web con tarjetas de estado de los 3 nodos.

### Prometheus + Grafana (Opción A)
- `http://localhost:9090` — Consola de Prometheus
- `http://localhost:3000` — Grafana (admin/admin)
```

Además, agregar en **Requisitos Previos** que no se requieren herramientas adicionales para el monitoreo (todo corre dentro de Docker).
