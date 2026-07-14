# Monitoreo del Clúster — Prometheus + cAdvisor + Grafana

> **Fase 3 — Seguridad y Alta Disponibilidad**

---

## 1. Stack de Monitoreo

| Componente | Imagen | Puerto | Función |
|---|---|---|---|
| **cAdvisor** | `gcr.io/cadvisor/cadvisor:latest` | `:8080` | Expone métricas de uso de contenedores (CPU, RAM, red, disco) |
| **Prometheus** | `prom/prometheus:latest` | `:9090` | Almacena y consulta métricas scrapeadas de cAdvisor y nodos |
| **Grafana** | `grafana/grafana:latest` | `:3000` | Dashboards visuales con Prometheus como datasource |

---

## 2. Flujo de Datos

```
Nodos (nodo1:8000/health) ──► Prometheus (:9090) ◄── Grafana (:3000)
cAdvisor (:8080/metrics)  ──► Prometheus (:9090)
```

Prometheus scrapea cada 2 segundos:
- `cadvisor:8080` — métricas de todos los contenedores
- `nodo1:8000`, `nodo2:8000`, `nodo3:8000` — endpoint `/health` de cada nodo

---

## 3. Configuración de Prometheus

Archivo: `monitoring/prometheus.yml`

```yaml
global:
  scrape_interval: 2s

scrape_configs:
  - job_name: 'cluster-containers'
    static_configs:
      - targets: ['cadvisor:8080']
  - job_name: 'cluster-nodes-app'
    static_configs:
      - targets: ['nodo1:8000', 'nodo2:8000', 'nodo3:8000']
```

---

## 4. Consultas PromQL Útiles

| Consulta | Descripción |
|---|---|
| `sum(rate(container_cpu_usage_seconds_total[1m]))` | CPU total del clúster |
| `sum(container_memory_usage_bytes) / 1e6` | Memoria total usada (MB) |
| `rate(container_network_receive_bytes_total[1m])` | Tráfico de red entrante |
| `up{job="cluster-nodes-app"}` | Estado UP/DOWN de cada nodo |

---

## 5. Dashboards de Grafana

### 5.1 Importar dashboard

1. Abrir `http://localhost:3000` (admin/admin)
2. Agregar Prometheus como datasource: `http://prometheus:9090`
3. Importar dashboard ID `893` (node-exporter) o crear uno nuevo con:

**Panel: Estado de nodos**
- Métrica: `up{job="cluster-nodes-app"}`
- Tipo: Stat
- Umbral: 0=red, 1=green

**Panel: CPU por nodo**
- Métrica: `sum(rate(container_cpu_usage_seconds_total{name=~"cluster.*"}[1m])) by (name)`
- Tipo: Bar gauge

**Panel: Memoria por nodo**
- Métrica: `sum(container_memory_usage_bytes{name=~"cluster.*"}) by (name) / 1e6`
- Tipo: Bar gauge

### 5.2 Alertas sugeridas

| Alerta | Condición | Severidad |
|---|---|---|
| Nodo caído | `up{job="cluster-nodes-app"} < 3` | Critical |
| CPU > 80% | `container_cpu_usage_seconds_total > 0.8` | Warning |
| Memoria > 80% | `container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.8` | Warning |

---

## 6. Verificación

```bash
# cAdvisor expone métricas
curl -sf http://localhost:8080/metrics | head -5

# Prometheus targets
curl -sf 'http://localhost:9090/api/v1/targets' | python3 -m json.tool | grep '"health"'

# Grafana login page
curl -sf -o /dev/null -w "%{http_code}" http://localhost:3000
# → 302 (OK, redirige a login)
```

---

## 7. Logs del Clúster

```bash
# Todos los servicios
docker compose logs -f

# Solo un nodo específico
docker compose logs -f nodo1

# Filtrar por 3PC
docker compose logs --tail=100 nodo1 | grep "\[3PC\]"

# Filtrar por elecciones
docker compose logs --tail=100 nodo2 | grep "\[ELECCIÓN\]"
```
