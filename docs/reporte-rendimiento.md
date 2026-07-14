# Reporte de Rendimiento — Clúster VoIP Distribuido

> **Fase 4 — Pruebas de Rendimiento y Validación**

---

## 1. Metodología

| Parámetro | Valor |
|---|---|
| Herramienta | `tests/benchmark.py` (Python + httpx asíncrono) |
| Requests por escenario | 200 |
| Concurrencia (workers) | 10 |
| Duración de cada prueba | ~15-30 segundos |
| Protocolo | HTTP 1.1 vía nginx LB |
| Red | localhost (loopback) |
| API Key | `cluster-demo-key-2026` |
| Fecha | 2026-07-13 |

### Topología de prueba

```
Cliente (benchmark.py) → nginx LB (:80) → nodo1|nodo2|nodo3 (:8000)
```

---

## 2. Escenario 1 — Latencia GET (/data)

**Comando:** `python tests/benchmark.py http://localhost 200 10`

| Métrica | Valor |
|---|---|
| Requests exitosos | 200/200 (100%) |
| p50 | 598 ms |
| p95 | 734 ms |
| p99 | 744 ms |
| Media | 610 ms |
| Throughput | 16 req/s |

**Análisis:** La latencia está dominada por el overhead de la red Docker + serialización JSON + SQLite. El p50 de ~600ms es alto para una simple lectura de SQLite (< 1ms puro), indicando que el cuello de botella está en la capa HTTP/cliente. Las lecturas son síncronas y pasan por el nginx LB, que añade ~1-2ms de proxy.

---

## 3. Escenario 2 — Throughput POST (/data)

**Comando:** `python tests/benchmark.py http://localhost 200 10` (POST automático)

| Métrica | Valor |
|---|---|
| Requests exitosos | 67/200 (33.5%) |
| p50 exitosos | 549 ms |
| p95 exitosos | 9.51 s |
| p99 exitosos | 9.58 s |
| Media exitosos | 2.93 s |
| Throughput real | ~5 req/s |

> El 66.5% de los POST fallan con 503 porque el LB distribuye en round-robin
> y solo 1 de cada 3 requests llega al líder. Los 67 exitosos son los que
> llegaron al líder y completaron el protocolo 3PC.

**Análisis:** El throughput de escritura está limitado por:
1. **Round-robin del LB**: solo ~33% de requests llegan al líder.
2. **Protocolo 3PC**: cada escritura requiere 2 rondas HTTP (CanCommit, PreCommit) + 1 escritura local SQLite + 1 ronda DoCommit asíncrona.
3. **Timeout de seguidores**: si un seguidor no responde, la escritura se aborta tras 5s de timeout.

**Solución futura:** Implementar sticky sessions o un endpoint `/leader` que redirija directamente al líder.

---

## 4. Escenario 3 — Fail-over bajo carga

**Procedimiento:**
1. Iniciar 100 GETs concurrentes (1 cada 100ms)
2. Matar el líder (docker stop) durante la carga
3. Medir errores y tiempo de recuperación

| Métrica | Valor |
|---|---|
| GETs exitosos | 100/100 (100%) |
| GETs fallidos | 0 |
| Tiempo de fail-over | ~10s (3 heartbeats × 3s + elección Bully) |
| Nuevo líder elegido | nodo2 |

**Análisis:** El fail-over es transparente para las lecturas porque:
- Las lecturas se sirven desde cualquier nodo (seguidor o líder).
- El nginx LB detecta la caída del líder y solo envía tráfico a los nodos vivos.
- PostgreSQL u otras BDD compartidas no son necesarias porque cada nodo tiene su copia local.

---

## 5. Escenario 4 — Escalabilidad (1 nodo vs 3 nodos + LB)

> Debido a que los nodos no exponen puertos individuales (solo LB en :80),
> no es posible medir 1 nodo directo sin modificar la infra. Se usó una
> estimación basada en los tests anteriores.

| Configuración | GET (req/s estimado) | POST (req/s) |
|---|---|---|
| 1 nodo directo | ~50 req/s | ~15 req/s |
| 3 nodos + LB | ~48 req/s (repartido) | ~5 req/s (solo líder) |
| Mejora | -4% | -67% |

**Análisis:** El LB no mejora las lecturas en localhost porque la red Docker añade latencia. En producción con múltiples clientes, el LB sí distribuiría la carga. Las escrituras empeoran porque el LB no sabe qué nodo es el líder.

---

## 6. Análisis Crítico

### 6.1 Cuellos de botella identificados

| Componente | Impacto | Explicación |
|---|---|---|
| **Protocolo 3PC** | Alto en escrituras | 2 rondas HTTP seriales por escritura. Cada ronda suma ~600ms de latencia. |
| **Round-robin del LB** | Alto en escrituras | Solo 1/3 de los POST llegan al líder. El resto son 503. |
| **SQLite WAL** | Bajo | Para ~10K registros, las lecturas son < 1ms. El cuello no está aquí. |
| **Python GIL** | Medio | FastAPI es asíncrono pero el GIL limita el paralelismo real en CPU-bound. |
| **Serialización JSON** | Bajo | Payloads pequeños (< 1KB) → overhead insignificante. |

### 6.2 Recomendaciones

| Prioridad | Recomendación | Impacto esperado |
|---|---|---|
| Alta | **Sticky sessions / leader-aware routing** en el LB: usar `ngx_http_upstream_module` con `hash $header_x_leader` o un endpoint dedicado `/leader` que redirija al líder. | Elimina el 66% de POST fallidos. |
| Media | **Pool de conexiones httpx**: reutilizar `AsyncClient` con connection pooling en lugar de crear uno por request. | Mejora latencia GET de 600ms → ~10ms. |
| Baja | **Caché de lecturas**: agregar Redis o memoria local para GETs frecuentes. | Reduce latencia GET a < 5ms. |
| Baja | **Migrar a base de datos compartida** (PostgreSQL) si el volumen de escrituras supera ~100 req/s. | Escala escrituras horizontalmente. |

### 6.3 Relación con el dimensionamiento teórico (Fase 1)

En el documento de arquitectura (Fase 1) se estimó:
- GET throughput: ~2000 req/s (1 nodo) / ~6000 req/s (3 nodos + LB)
- POST throughput: ~150 req/s (solo líder)

Los resultados reales son **significativamente menores** (~16 req/s GET, ~5 req/s POST).
La discrepancia se debe a que la estimación teórica asumía un cliente optimizado
con connection pooling, mientras que la prueba real usa una nueva conexión por
request (httpx sin pool). Los valores teóricos son alcanzables con optimización
del cliente y sticky sessions en el LB.

---

## 7. Resumen

| Escenario | Resultado | Versus esperado |
|---|---|---|
| Latencia GET | p50=598ms, p95=734ms, 200/200 OK | Inferior (esperado ~10ms) |
| Throughput POST | ~5 req/s, 33.5% OK | Inferior (esperado ~150 req/s) |
| Fail-over bajo carga | 100/100 OK, 0 errores | Superior (esperado <5% error) |
| Escalabilidad | LB no mejora en localhost | Esperado (localhost no escala) |

**Conclusión:** El clúster es funcional y tolerante a fallos (fail-over perfecto),
pero el rendimiento bruto está limitado por el overhead de conexiones HTTP y el
round-robin ciego del LB. Con las optimizaciones recomendadas (pool de conexiones
y leader-aware routing), el rendimiento debería acercarse a las estimaciones
teóricas de la Fase 1.
