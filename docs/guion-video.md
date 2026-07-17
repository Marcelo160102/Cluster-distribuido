# Guion para Video Explicativo — Clúster Distribuido VoIP

**Duración máxima:** 5 minutos

---

## Escena 1: Introducción + Arquitectura (1 min)

**Visual:** Diagrama C2 (Cliente → nginx → 3 nodos → SQLite → Prometheus/Grafana)

**Voz en off:**
"Clúster distribuido de 3 nodos para registro VoIP con replicación 3PC, algoritmo Bully, balanceo nginx, seguridad HTTPS + API Key y monitoreo Prometheus y Grafana. Se despliega con un solo comando: `docker compose up --build -d`."

**Texto en pantalla:** `docker compose up --build -d`

---

## Escena 2: CRUD + Replicación 3PC (1 min 30 seg)

**Visual:** Terminal: POST crear endpoint, luego mostrar datos en los 3 nodos (docker exec)

**Voz en off:**
"Solo el líder acepta escrituras. El protocolo 3PC replica en 3 fases: CanCommit, PreCommit y DoCommit. Creamos un endpoint VoIP y verificamos que aparezca en los 3 nodos."

```bash
curl -s -X POST http://localhost:80/data \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: cluster-demo-key-2026' \
  -d '{"data": "{\"extension\":\"101\",\"protocol\":\"SIP\",\"ip_address\":\"192.168.1.50\",\"status\":\"online\",\"user_agent\":\"Yealink T48S\"}"}'

docker exec cluster-distribuido-nodo1-1 sqlite3 /app/data/data.db "SELECT * FROM items"
docker exec cluster-distribuido-nodo2-1 sqlite3 /app/data/data.db "SELECT * FROM items"
```

**Texto en pantalla:** "CanCommit → PreCommit → DoCommit"

---

## Escena 3: Fail-over Bully + Recuperación (1 min 30 seg)

**Visual:** Terminal: identificar líder → docker stop → nuevo líder → docker start → sincronización

**Voz en off:**
"Al detener el líder, los seguidores detectan la caída tras 3 heartbeats (9s) e inician una elección Bully. El nodo vivo de mayor ID asume el liderazgo. Al recuperar el nodo caído, se sincroniza automáticamente descargando el estado completo del líder."

```bash
docker stop cluster-distribuido-nodo3-1
sleep 12
docker exec cluster-distribuido-nodo2-1 curl -s /health
docker start cluster-distribuido-nodo3-1
```

---

## Escena 4: Seguridad + Monitoreo (30 seg)

**Visual:** Split: terminal con 401/200 + navegador con Grafana dashboard

**Voz en off:**
"API Key en header X-API-Key para /data. Sin key → 401. Prometheus scrapea métricas cada 2s y Grafana las visualiza en dashboard."

**Texto en pantalla:**
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090

---

## Escena 5: Cierre (30 seg)

**Visual:** Diagrama completo + enlaces

**Voz en off:**
"Clúster funcional con replicación 3PC, alta disponibilidad, seguridad y monitoreo. Desplegable con Docker Compose o Ansible."

**Texto en pantalla:**
- github.com/Marcelo160102/Cluster-distribuido
- docs/INFORME-COMPLETO.md

---

## Resumen de tiempos

| Escena | Duración |
|---|---|
| 1. Introducción + Arquitectura | 1:00 |
| 2. CRUD + 3PC | 1:30 |
| 3. Fail-over + Recuperación | 1:30 |
| 4. Seguridad + Monitoreo | 0:30 |
| 5. Cierre | 0:30 |
| **Total** | **5:00** |
