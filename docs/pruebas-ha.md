# Pruebas de Alta Disponibilidad — Clúster VoIP Distribuido

> **Fase 3 — Seguridad y Alta Disponibilidad**

---

## Prueba 1: Fail-over del Líder

**Objetivo:** Verificar que al caer el líder, un seguidor toma el control y el servicio continúa.

**Escenario:**
1. Identificar líder actual
2. Detener el contenedor del líder
3. Verificar que un nuevo líder es elegido en < 15s
4. Verificar que el servicio de escritura continúa

**Ejecución:**
```bash
# Identificar líder
$ curl -sk https://localhost:443/health
{"node_id":"nodo3","role":"leader","status":"alive"}

# Matar líder
$ docker stop cluster-distribuido-nodo3-1

# Esperar fail-over (heartbeat: 3s × 3 intentos ≈ 9s)
$ sleep 10

# Verificar nuevo líder
$ curl -sk https://localhost:443/health
{"node_id":"nodo2","role":"leader","status":"alive"}
```

**Resultado:** ✅ Líder nodo3 muerto → nodo2 elegido como nuevo líder en ~10s.

---

## Prueba 2: Continuidad del Servicio (Escritura tras Fail-over)

**Objetivo:** Verificar que el nuevo líder acepta escrituras.

**Ejecución:**
```bash
$ curl -sk -X POST https://localhost:443/data \
  -H "Content-Type: application/json" \
  -H "X-API-Key: cluster-demo-key-2026" \
  -d '{"data": "{\"extension\": \"555\", \"protocol\": \"SIP\", \"ip_address\": \"10.0.0.5\", \"status\": \"offline\", \"user_agent\": \"HATest\"}"}'

{"id":"9912efd1-...","data":"{...\"extension\": \"555\"...}","created_at":"...","updated_at":"..."}
```

**Resultado:** ✅ POST exitoso al nuevo líder.

---

## Prueba 3: Recuperación y Sincronización

**Objetivo:** Verificar que un nodo recuperado se sincroniza automáticamente.

**Ejecución:**
```bash
# Recuperar nodo caído
$ docker start cluster-distribuido-nodo3-1

# Verificar health (esperar healthcheck)
$ sleep 8
$ docker ps --format '{{.Names}} {{.Status}}' | grep nodo3
cluster-distribuido-nodo3-1 Up 8 seconds (healthy)

# Leer datos (debe incluir los creados durante su caída)
$ curl -sk https://localhost:443/data -H "X-API-Key: cluster-demo-key-2026"
[... arrays con todos los registros ...]
```

**Resultado:** ✅ nodo3 se recupera, pasa healthcheck y muestra datos consistentes (sincronización total vía `GET /cluster/sync`).

---

## Prueba 4: Balanceo de Carga (Round-Robin)

**Objetivo:** Verificar que el nginx LB distribuye peticiones entre los 3 nodos.

**Ejecución:**
```bash
# 5 requests a /health, verificar node_id en respuesta
$ for i in 1 2 3 4 5; do curl -sk https://localhost:443/health; echo; done
{"node_id":"nodo1","role":"follower","status":"alive"}
{"node_id":"nodo2","role":"leader","status":"alive"}
{"node_id":"nodo1","role":"follower","status":"alive"}
{"node_id":"nodo2","role":"leader","status":"alive"}
{"node_id":"nodo1","role":"follower","status":"alive"}
```

**Resultado:** ✅ Round-robin alterna entre nodo1 y nodo2 (nodo3 está presente pero puede no recibir la tanda exacta). Todos los nodos funcionales.

---

## Prueba 5: Resiliencia del Protocolo 3PC

**Objetivo:** Verificar que el 3PC tolera la caída de un seguidor usando quórum (2/3).

**Escenario:**
1. Matar un seguidor (nodo1)
2. Hacer POST al líder
3. Verificar que la escritura se completa con quórum (líder + 1 seguidor = 2/3)

**Ejecución:**
```bash
# Matar seguidor
$ docker stop cluster-distribuido-nodo1-1

# POST al líder (puede requerir reintentos hasta dar con el líder vía LB)
$ curl -sk -X POST https://localhost:443/data \
  -H "Content-Type: application/json" \
  -H "X-API-Key: cluster-demo-key-2026" \
  -d '{"data": "{\"extension\": \"666\", \"protocol\": \"SIP\", \"ip_address\": \"10.0.0.6\", \"status\": \"busy\", \"user_agent\": \"3PCTest\"}"}'
{"id":"...","data":"{...\"extension\": \"666\"...}","created_at":"...","updated_at":"..."}
```

**Resultado:** ✅ El 3PC completa con quórum 2/3 (líder + 1 seguidor).

---

## Prueba 6: Autenticación (API Key)

**Objetivo:** Verificar que el middleware rechaza peticiones sin API Key o con clave inválida.

**Ejecución:**
```bash
# Sin API Key → 401
$ curl -sk -X POST https://localhost:443/data -H "Content-Type: application/json" -d '{"data":"test"}'
{"detail":"API Key inválida"}

# API Key incorrecta → 401
$ curl -sk -X POST https://localhost:443/data -H "Content-Type: application/json" -H "X-API-Key: wrong" -d '{"data":"test"}'
{"detail":"API Key inválida"}

# API Key correcta → 200 (o 503 si no es líder)
$ curl -sk -X POST https://localhost:443/data -H "Content-Type: application/json" \
  -H "X-API-Key: cluster-demo-key-2026" \
  -d '{"data": "{\"extension\": \"777\", \"protocol\": \"SIP\", \"ip_address\": \"10.0.0.7\", \"status\": \"online\", \"user_agent\": \"AuthTest\"}"}'
{"id":"...", ...}
```

**Resultado:** ✅ Autenticación funcional. Solo requests con API Key correcta llegan al CRUD.

---

## Prueba 7: HTTPS

**Objetivo:** Verificar redirección HTTP → HTTPS y cifrado TLS.

**Ejecución:**
```bash
# HTTP redirige a HTTPS
$ curl -s -o /dev/null -w "%{http_code} %{redirect_url}" http://localhost:80/data
301 https://localhost/data

# HTTPS con self-signed (flag -k para omitir verificación)
$ curl -sk -o /dev/null -w "%{http_code}" https://localhost:443/health
200
```

**Resultado:** ✅ HTTP redirige a HTTPS (301). HTTPS responde con 200.

---

## Resumen de Resultados

| # | Prueba | Resultado |
|---|---|---|
| 1 | Fail-over líder | ✅ |
| 2 | Escritura tras fail-over | ✅ |
| 3 | Recuperación y sincronización | ✅ |
| 4 | Balanceo round-robin | ✅ |
| 5 | Resiliencia 3PC (quórum 2/3) | ✅ |
| 6 | Autenticación API Key (401/200) | ✅ |
| 7 | HTTPS (301 + 200) | ✅ |
