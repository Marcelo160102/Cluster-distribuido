# Checklist de Instalación — Clúster VoIP Distribuido

> Marcar cada item al completar la verificación en el entorno destino.

---

## 1. Requisitos del Sistema

| # | Item | Verificación | Estado |
|---|---|---|---|
| 1.1 | Docker Engine 24+ | `docker --version` | ☐ |
| 1.2 | Docker Compose Plugin | `docker compose version` | ☐ |
| 1.3 | Git | `git --version` | ☐ |
| 1.4 | Curl | `curl --version` | ☐ |
| 1.5 | Python 3.11+ | `python3 --version` | ☐ |
| 1.6 | RAM ≥ 2 GB | `free -h` | ☐ |
| 1.7 | Espacio en disco ≥ 1 GB | `df -h /` | ☐ |

---

## 2. Despliegue con Docker Compose

| # | Item | Comando | Estado |
|---|---|---|---|
| 2.1 | Clonar repositorio | `git clone <repo> && cd Cluster-distribuido` | ☐ |
| 2.2 | Construir imágenes | `docker compose build` | ☐ |
| 2.3 | Levantar servicios | `docker compose up -d` | ☐ |
| 2.4 | Todos los contenedores UP | `docker ps --format '{{.Names}} {{.Status}}'` | ☐ |

### Contenedores esperados (7)

```
nodo1           Up (healthy)
nodo2           Up (healthy)
nodo3           Up (healthy)
loadbalancer    Up (healthy)
cadvisor        Up
prometheus      Up
grafana         Up
```

---

## 3. Smoke Tests

| # | Item | Comando | Resultado esperado | Estado |
|---|---|---|---|---|
| 3.1 | Health LB | `curl -sf localhost:80/health` | JSON con `"status":"alive"` | ☐ |
| 3.2 | Listar datos (vacío) | `curl -sf localhost:80/data` | `[]` | ☐ |
| 3.3 | Crear endpoint VoIP | `curl -sf -X POST localhost:80/data -H 'Content-Type: application/json' -d '{"data":"{\\"extension\\":\\"101\\",\\"protocol\\":\\"SIP\\",\\"ip_address\\":\\"10.0.0.1\\",\\"status\\":\\"online\\",\\"user_agent\\":\\"Test\\"}"}'` | JSON con `id` y `data` | ☐ |
| 3.4 | Ver datos replicados | `curl -sf localhost:80/data` | Array con 1 elemento | ☐ |
| 3.5 | Smoke script automatizado | `bash tests/smoke_test.sh` | Exit code 0 | ☐ |

---

## 4. Monitoreo

| # | Item | Comando | Resultado esperado | Estado |
|---|---|---|---|---|
| 4.1 | cAdvisor UI | `curl -sf localhost:8080` | HTML con dashboard | ☐ |
| 4.2 | Prometheus UI | `curl -sf localhost:9090` | HTML con "Prometheus" | ☐ |
| 4.3 | Prometheus targets UP | `curl -sf 'localhost:9090/api/v1/targets' | jq '.data.activeTargets[].health'` | `"up"` para todos | ☐ |
| 4.4 | Grafana login | `curl -sf localhost:3000` | HTML con "Grafana" | ☐ |

---

## 5. Despliegue con Ansible (opcional — VM remota)

| # | Item | Comando | Estado |
|---|---|---|---|
| 5.1 | Editar `ansible/inventory.ini` con IP real | `nano ansible/inventory.ini` | ☐ |
| 5.2 | Provisionar VM | `ansible-playbook -i ansible/inventory.ini ansible/playbook-provision.yml` | ☐ |
| 5.3 | Desplegar clúster | `ansible-playbook -i ansible/inventory.ini ansible/playbook-deploy.yml` | ☐ |
| 5.4 | Verificar desde la VM | `ssh ubuntu@<IP> "docker ps && curl localhost:80/health"` | ☐ |

---

## 6. Resumen

| Categoría | Items totales | Items pasados |
|---|---|---|
| Requisitos del sistema | 7 | ☐ / 7 |
| Docker Compose | 4 | ☐ / 4 |
| Smoke tests | 5 | ☐ / 5 |
| Monitoreo | 4 | ☐ / 4 |
| Ansible | 4 | ☐ / 4 |
| **Total** | **24** | **☐ / 24** |
