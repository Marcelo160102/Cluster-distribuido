# Guion para Video Explicativo — Clúster Distribuido VoIP

**Duración máxima:** 10 minutos

---

## Escena 1: Introducción (1 min)

**Visual:** Diagrama de arquitectura general (Cliente → nginx → 3 nodos → SQLite → Prometheus/Grafana)

**Voz en off:**
"Este proyecto implementa un clúster distribuido de 3 nodos para registro de endpoints VoIP, con replicación 3PC, algoritmo de elección Bully, balanceo nginx, seguridad HTTPS + API Key, y monitoreo con Prometheus y Grafana."

---

## Escena 2: Arquitectura + Despliegue (1 min 30 seg)

**Visual:** Split screen: diagrama C4 + terminal con docker compose up

**Voz en off:**
"Tres nodos FastAPI con SQLite, cada uno con su base local. nginx distribuye en round-robin y reintenta automáticamente en otro nodo si un seguidor rechaza una escritura (proxy_next_upstream http_503). El despliegue es un solo comando: `docker compose up --build -d` levanta los 7 servicios: 3 nodos, nginx, cAdvisor, Prometheus y Grafana."

**Texto en pantalla:** `proxy_next_upstream error timeout http_503`

---

## Escena 3: Smoke Test (30 seg)

**Visual:** Terminal con `bash tests/smoke_test.sh` → salida 4/4

**Voz en off:**
"El smoke test verifica health, lectura, creación y persistencia. 4 pruebas, 4 exitosas."

---

## Escena 4: CRUD + Replicación 3PC (1 min 30 seg)

**Visual:** Terminal: CREATE, verificación en 3 nodos con docker exec, UPDATE, DELETE

**Voz en off:**
"El protocolo 3PC coordina la replicación en 3 fases: CanCommit, PreCommit y DoCommit. El líder asigna un UUID, los seguidores usan ese mismo UUID. CREATE, UPDATE y DELETE se replican a los 3 nodos. Verificamos con docker exec en cada contenedor."

**Texto en pantalla:** "CanCommit → PreCommit → DoCommit"

---

## Escena 5: Fail-over Bully + Recuperación (2 min 30 seg)

**Visual:** Terminal: identificar líder → docker stop → esperar 12s → nuevo líder → docker start → sincronización

**Voz en off:**
"El algoritmo Bully elige al nodo de mayor ID como líder. Al detener el líder, los seguidores detectan la caída tras 3 heartbeats fallidos (9 segundos) e inician una elección. El nodo vivo de mayor ID asume el liderazgo. Al recuperar el nodo caído, el heartbeat loop detecta que está vivo y dispara una sincronización total: descarga el listado del líder, limpia su base e inserta los datos atómicamente."

```bash
docker stop cluster-distribuido-nodo3-1    # líder muere
# esperar 12s
docker exec nodo2 curl /health             # role=leader (nuevo)
docker start cluster-distribuido-nodo3-1   # se recupera
# esperar 10s → sincronización automática
```

---

## Escena 6: Seguridad (30 seg)

**Visual:** Terminal: 401 sin API Key, 401 con key incorrecta, 200 con key correcta + HTTPS

**Voz en off:**
"API Key en header X-API-Key para endpoints /data. HTTPS con certificado self-signed. Sin key → 401, key incorrecta → 401."

---

## Escena 7: Monitoreo (1 min)

**Visual:** Navegador: Prometheus targets UP, Grafana dashboard, cAdvisor

**Voz en off:**
"Prometheus scrapea cada 2 segundos. Cada nodo expone is_leader, records_total, requests_total y latency. Grafana visualiza en dashboard preconfigurado. cAdvisor muestra CPU, memoria y red de cada contenedor."

**Texto en pantalla:**
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090
- cAdvisor: http://localhost:8080

---

## Escena 8: Cierre (30 seg)

**Visual:** Diagrama completo + enlaces

**Voz en off:**
"Clúster distribuido funcional con replicación 3PC, alta disponibilidad por Bully, seguridad por API Key + HTTPS, y monitoreo completo. Desplegable con Docker Compose o Ansible."

**Texto en pantalla:**
- github.com/Marcelo160102/Cluster-distribuido
- Documentación: docs/INFORME-COMPLETO.md

---

## Resumen de tiempos

| Escena | Duración |
|---|---|
| 1. Introducción | 1:00 |
| 2. Arquitectura + Despliegue | 1:30 |
| 3. Smoke Test | 0:30 |
| 4. CRUD + 3PC | 1:30 |
| 5. Fail-over + Recuperación | 2:30 |
| 6. Seguridad | 0:30 |
| 7. Monitoreo | 1:00 |
| 8. Cierre | 0:30 |
| **Total** | **9:00** |

## Recursos visuales

| Escena | Recurso |
|---|---|
| 1, 8 | Diagrama de arquitectura (docs/arquitectura.md) |
| 2 | Diagrama C4 + captura terminal |
| 3-6 | Capturas de terminal |
| 7 | Capturas navegador (Grafana, Prometheus, cAdvisor) |

## Tips de producción

- Zoom en terminales para legibilidad
- Resaltar comandos clave en amarillo
- Mostrar logs en vivo durante fail-over
- En Grafana, crear un registro y mostrar cómo sube el contador en el dashboard
