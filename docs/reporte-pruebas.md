# Reporte Final de Pruebas — Clúster Distribuido VoIP

## Resumen de Pruebas Realizadas

| # | Prueba | Descripción | Estado |
|---|---|---|---|
| 1 | Smoke test | Verifica health, lectura, creación y persistencia vía LB | ✅ |
| 2 | CREATE + replicación 3PC | POST `/data` con verificación del UUID en los 3 nodos | ✅ |
| 3 | UPDATE + replicación 3PC | PUT `/data/{id}` cambia estado, verificado en 3 nodos | ✅ |
| 4 | DELETE + replicación 3PC | DELETE `/data/{id}`, registro desaparece de 3 nodos | ✅ |
| 5 | Fail-over del líder | Detención del líder, elección Bully, nuevo líder asume | ✅ |
| 6 | Continuidad del servicio | Escritura con nuevo líder replica al seguidor vivo | ✅ |
| 7 | Recuperación de nodo caído | Nodo recuperado sincroniza todos los datos del líder | ✅ |
| 8 | Seguridad HTTPS | Sin API Key → 401, key incorrecta → 401, HTTPS funciona | ✅ |
| 9 | Monitoreo Prometheus | Targets UP, métricas `app_is_leader`, `app_records_total` | ✅ |
| 10 | Dashboard Grafana | Datasource Prometheus configurado, paneles creados | ✅ |
| 11 | cAdvisor | Métricas de CPU/memoria/red de contenedores | ✅ |

## Fixes Aplicados Durante las Pruebas

| Fix | Archivo | Descripción |
|---|---|---|
| Replicación 3PC con mismo UUID | `app/core/database.py` | `create()` acepta `item_id` opcional para usar el UUID del líder |
| update() devuelve created_at | `app/core/database.py` | UPDATE ahora retorna todos los campos incluyendo `created_at` |
| nginx proxy_next_upstream | `nginx.conf` | Reintento automático en otro nodo al recibir 503 |
| Endpoint /metrics | `app/main.py` | Instrumentación Prometheus agregada a cada nodo |
| Smoke test con API Key | `tests/smoke_test.sh` | Header `X-API-Key` agregado a todas las requests |

## Arquitectura Final

```
Cliente ── HTTP/HTTPS ──→ nginx LB (:80/:443)
                               │
                ┌──────────────┼──────────────┐
                ▼              ▼              ▼
            nodo1 ── 3PC ──→ nodo2 ── 3PC ──→ nodo3
            (8000)   ←────   (8000)   ←────   (8000)
               │                             │
               └───────── Bully + Heartbeat ──┘

Monitoreo: cAdvisor → Prometheus → Grafana (:3000)
```

## Puertos Expuestos

| Puerto | Servicio |
|---|---|
| 80 | HTTP Load Balancer |
| 443 | HTTPS Load Balancer |
| 3000 | Grafana (admin/admin) |
| 9090 | Prometheus |
| 8080 | cAdvisor |
