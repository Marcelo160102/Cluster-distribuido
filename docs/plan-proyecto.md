# Plan de Proyecto — Clúster Distribuido de Servicios Web

> Documento guía para el desarrollo del proyecto de Sistemas Distribuidos 2026.
> Basado en el enunciado oficial (`docs/enunciado_del_proyecto.md`).
> Puntuación total: **10 pts** (Planificación 2, Instalación 3, Seguridad/HA 2, Pruebas 1, Documentación 1, Presentación 1).

---

## Estructura del Proyecto (después de completar todas las fases)

```
Cluster-distribuido/
├── ansible/
│   ├── inventory.ini
│   ├── playbook-provision.yml
│   ├── playbook-deploy.yml
│   └── vars.yml
├── app/
│   ├── api/
│   │   ├── routes_cluster.py
│   │   └── routes_data.py
│   ├── core/
│   │   ├── config.py
│   │   └── database.py
│   ├── domain/
│   │   └── schemas.py
│   ├── services/
│   │   ├── leader_election.py
│   │   ├── node_client.py
│   │   └── replication.py
│   └── main.py
├── certs/
│   ├── selfsigned.crt
│   └── selfsigned.key
├── docs/
│   ├── apendice-comandos.md      ← F5
│   ├── arquitectura.md           ← F1 (DIAGRAMA C4)
│   ├── checklist-instalacion.md  ← F2
│   ├── enunciado_del_proyecto.md
│   ├── fase-monitoreo.md
│   ├── glosario.md               ← F5
│   ├── informe-final.pdf         ← F5 (generado)
│   ├── manual-operacion.md       ← F5
│   ├── monitoreo.md              ← F3
│   ├── plan-orquestacion.md      ← (plan anterior, reemplazado)
│   ├── plan-proyecto.md          ← ESTE ARCHIVO
│   ├── politicas-seguridad.md    ← F3
│   ├── pruebas-ha.md             ← F3
│   ├── reporte-rendimiento.md    ← F4
│   └── Proyecto_Sistemas_Distribuidos_2026.md
├── monitoring/
│   └── prometheus.yml
├── scripts/
│   ├── gen-certs.sh
│   └── install-tools.sh
├── tests/
│   ├── install-tools.sh
│   ├── run_tests.sh
│   └── smoke_test.sh
├── docker-compose.yml
├── Dockerfile
├── nginx.conf
├── README.md
└── requirements.txt
```

---

## Fase 1: Planificación y Diseño Arquitectónico (2 pts)

**Objetivo:** Documento de arquitectura con diagrama C4 normalizado + justificación completa del tipo de clúster, topología de red y dimensionamiento.

### Entregables

| Archivo | Contenido |
|---|---|
| `docs/arquitectura.md` | Justificación del tipo de clúster, topología de red, dimensionamiento, diagramas C4 (Mermaid): Contexto, Contenedores, Componentes, Código |

### Actividades

| # | Actividad | Detalle |
|---|---|---|
| 1.1 | Definir tipo de clúster | Justificar por qué servicios web (registro distribuido de endpoints VoIP) vs HPC vs Big Data |
| 1.2 | Topología de red | Cliente → nginx LB (puerto 80) → 3 nodos FastAPI en red Docker bridge interna |
| 1.3 | Dimensionamiento | CPU (0.5 por nodo), RAM (512 MB), almacenamiento (~100 MB SQLite WAL), throughput esperado |
| 1.4 | Diagrama C1 Contexto | Mermaid: actor usuario → sistema "Clúster VoIP Distribuido" |
| 1.5 | Diagrama C2 Contenedores | Mermaid: nginx LB, 3× FastAPI+SQLite, Prometheus+cAdvisor+Grafana |
| 1.6 | Diagrama C3 Componentes | Mermaid: dentro de cada nodo: routes_data, routes_cluster, replication (3PC), leader_election (Bully), node_client, database (SQLite WAL) |
| 1.7 | Diagrama C4 Código | Mermaid: flujo detallado del protocolo 3PC (CanCommit → PreCommit → DoCommit) |
| 1.8 | Justificación tecnológica | Tabla Python/FastAPI/SQLite/Docker/3PC/Bully vs alternativas |

### Criterios de éxito
- Diagrama C4 completo con 4 niveles de abstracción.
- Justificación explícita de cada decisión arquitectónica.
- Dimensionamiento con números concretos.

---

## Fase 2: Configuración e Instalación (3 pts)

**Objetivo:** Infraestructura como código reproducible con Ansible + checklist de instalación verificado en 2+ nodos.

### Entregables

| Archivo | Contenido |
|---|---|
| `ansible/inventory.ini` | Inventario con host(s) del clúster |
| `ansible/playbook-provision.yml` | Playbook para instalar Docker, Python, git, curl, UFW |
| `ansible/playbook-deploy.yml` | Playbook para clonar repo, `docker compose up`, healthcheck |
| `ansible/vars.yml` | Variables: repo_url, branch, etc. |
| `docs/checklist-instalacion.md` | Checklist de verificación post-deploy |
| `tests/smoke_test.sh` | Script de smoke test automatizado |

### Bloque A — Corrección de infraestructura actual

| # | Acción | Archivo |
|---|---|---|
| 2A.1 | `git pull origin main` | Repo local |
| 2A.2 | Renombrar `ngix.conf` → `nginx.conf` | `nginx.conf` |
| 2A.3 | Revisar `docker-compose.yml` sin `ports:` en nodos (dejar intencional, solo LB expone 80) | `docker-compose.yml` |
| 2A.4 | Agregar servicios de monitoreo faltantes: Prometheus, cAdvisor, Grafana | `docker-compose.yml` |
| 2A.5 | `docker compose up --build -d` y verificar healthchecks | Terminal |
| 2A.6 | Smoke test: `curl localhost:80/data`, `curl localhost:80/health` | Terminal |

### Bloque B — Ansible

| # | Tarea Ansible | Detalle |
|---|---|---|
| 2B.1 | `playbook-provision.yml` | Instalar Docker, Docker Compose plugin, Python, git, curl, UFW. Habilitar Docker. Configurar UFW (80, 22, 443). |
| 2B.2 | `playbook-deploy.yml` | Clonar repo, `docker compose up --build -d`, esperar healthchecks, smoke test con `curl` |
| 2B.3 | `docs/checklist-instalacion.md` | Checklist con items verificables: `docker ps`, `curl /health`, `curl /data`, Prometheus UI, Grafana login |

### Criterios de éxito
- `ansible-playbook -i inventory.ini playbook-provision.yml` completa sin errores.
- `ansible-playbook -i inventory.ini playbook-deploy.yml` completa y smoke test pasa.
- Checklist marcado al 100%.

---

## Fase 3: Seguridad y Alta Disponibilidad (2 pts)

**Objetivo:** Políticas de seguridad documentadas, autenticación implementada, HA probada y monitoreo funcionando.

### Entregables

| Archivo | Contenido |
|---|---|
| `docs/politicas-seguridad.md` | Autenticación (API Key), cifrado (TLS), firewall (UFW), segregación de redes |
| `docs/pruebas-ha.md` | Evidencias de fail-over, balanceo, resiliencia 3PC |
| `docs/monitoreo.md` | Stack Prometheus/cAdvisor/Grafana: dashboards, alertas, consultas |
| `app/core/config.py` | `API_KEY` agregado |
| `app/main.py` | Middleware de validación de API Key |
| `nginx.conf` | Bloque SSL con certificado self-signed |
| `certs/selfsigned.crt`, `certs/selfsigned.key` | Certificado generado |
| `scripts/gen-certs.sh` | Script de generación de certificados |
| `docker-compose.yml` | Variables de entorno `API_KEY` inyectadas |

### Actividades

| # | Actividad | Detalle |
|---|---|---|
| 3.1 | Documento de políticas | `docs/politicas-seguridad.md` con autenticación, cifrado, firewall, segregación |
| 3.2 | Middleware API Key | Validar `X-API-Key` en `/data` desde `main.py`. Clave configurable vía env `API_KEY` |
| 3.3 | HTTPS en nginx | Generar cert self-signed, agregar server block :443, redirigir :80 → :443 |
| 3.4 | Firewall UFW | Reglas documentadas en `docs/politicas-seguridad.md` |
| 3.5 | Prueba fail-over | `docker stop nodo1`, verificar elección Bully + 3PC completa + servicio continuo. Capturar logs. |
| 3.6 | Prueba balanceo | 10 requests a LB, verificar distribución entre nodos en logs |
| 3.7 | Prueba resiliencia 3PC | Matar seguidor durante escritura, verificar quórum (2/3) |
| 3.8 | Monitoreo | Documentar stack, importar dashboard Grafana, configurar alertas |

### Criterios de éxito
- `curl -X POST localhost:80/data -H "X-API-Key: wrong"` → 401.
- `curl -X POST localhost:80/data -H "X-API-Key: cluster-demo-key-2026"` → 200.
- Fail-over completo en < 15s.
- HTTPS funcional en puerto 443.
- Prometheus scrape targets UP, Grafana accesible.

---

## Fase 4: Pruebas de Rendimiento y Validación (1 pt)

**Objetivo:** Medir latencia, throughput y escalabilidad con herramientas estándar (hey/wrk). Reporte con análisis crítico.

### Entregables

| Archivo | Contenido |
|---|---|
| `docs/reporte-rendimiento.md` | Escenarios, resultados (p50/p95/p99), tabla comparativa, análisis crítico |
| `tests/install-tools.sh` | Script para instalar hey/wrk |
| `tests/run_tests.sh` | Script para ejecutar batería de pruebas |

### Escenarios de prueba

| # | Escenario | Comando | Métricas |
|---|---|---|---|
| 4.1 | Latencia GET | `hey -n 1000 -c 10 localhost:80/data` | p50, p95, p99, req/s |
| 4.2 | Throughput POST | `hey -n 500 -c 10 -m POST -D payload.json localhost:80/data` | req/s, tasa error |
| 4.3 | Fail-over bajo carga | `hey` continuo + `docker stop nodo1` simultáneo | % errores durante ventana |
| 4.4 | Escalabilidad | 1 nodo directo vs 3 nodos+LB | Comparativa req/s y latencia |

### Análisis crítico
- Identificar cuellos de botella (SQLite WAL en escrituras, GIL de Python, serialización JSON).
- Recomendaciones de mejora (PostgreSQL, Particionamiento, Caching).

### Criterios de éxito
- Todos los escenarios ejecutados y documentados.
- Tabla comparativa con números concretos.
- Análisis crítico con al menos 3 observaciones y 2 recomendaciones.

---

## Fase 5: Documentación Técnica (1 pt)

**Objetivo:** Manual PDF en formato APA/IEEE con instalación, operación, mantenimiento, glosario y apéndice.

### Entregables

| Archivo | Contenido |
|---|---|
| `docs/manual-operacion.md` | Instalación paso a paso, operación diaria, mantenimiento, solución de problemas |
| `docs/glosario.md` | Definiciones de términos técnicos (3PC, Bully, Quórum, WAL, Split-brain, etc.) |
| `docs/apendice-comandos.md` | Comandos útiles por categoría (Docker, Ansible, hey, curl, UFW, Git) |
| `docs/informe-final.pdf` | PDF generado con pandoc + wkhtmltopdf en formato APA/IEEE |

### Actividades

| # | Actividad | Detalle |
|---|---|---|
| 5.1 | Manual de instalación | Desde clonar repo hasta clúster funcionando, con capturas |
| 5.2 | Manual de operación | CRUD de endpoints VoIP, monitoreo, logs |
| 5.3 | Manual de mantenimiento | Backup, restore, actualización, solución de problemas |
| 5.4 | Glosario | 15+ términos técnicos definidos |
| 5.5 | Apéndice de comandos | Comandos agrupados con ejemplos |
| 5.6 | Generar PDF | `pandoc` con todos los `.md` → `informe-final.pdf` |

### Criterios de éxito
- PDF generado automáticamente con `pandoc`.
- Formato APA/IEEE (portada, índice, referencias).
- Glosario con 15+ términos.

---

## Presentación (1 pt)

**Objetivo:** Diapositivas concisas (explicación breve de puntos puntuales).

| # | Actividad | Detalle |
|---|---|---|
| P.1 | Diapositiva 1 | Portada: nombre del proyecto, integrantes, materia |
| P.2 | Diapositiva 2 | Tipo de clúster y justificación (servicios web VoIP) |
| P.3 | Diapositiva 3 | Arquitectura: diagrama C2 Contenedores |
| P.4 | Diapositiva 4 | Demo rápida: crear dato, fail-over, recuperación |
| P.5 | Diapositiva 5 | Métricas de rendimiento: tabla comparativa |
| P.6 | Diapositiva 6 | Conclusiones y lecciones aprendidas |

---

## Cronograma

| Fase | Días estimados | Pts | Depende de |
|---|---|---|---|
| F1: Planificación y diseño | 1 | 2 | — |
| F2: Instalación (Ansible + fix infra) | 2 | 3 | F1 |
| F3: Seguridad y HA | 2 | 2 | F2 |
| F4: Pruebas de rendimiento | 1 | 1 | F2 |
| F5: Documentación técnica | 1 | 1 | F1-F4 |
| Presentación | 1 | 1 | F5 |
| **Total** | **8** | **10** | |

---

## Notas Técnicas

### Bugs conocidos (documentados, no blocking)

1. **Orden de escritura en 3PC**: `routes_data.py` hace `create()` local antes de `replicate_to_followers()`. Si 3PC falla tras escritura local, el líder queda inconsistente. Trade-off aceptado para este alcance.

2. **`tx_buffer` sin expiración**: Transacciones en buffer no tienen TTL. Se solucionará con cleanup asíncrono en F3.

3. **DoCommit asíncrono**: `replication.py` lanza DoCommit en background y retorna `True` inmediatamente. Consistencia eventual, no 3PC estricto. Documentado en reporte de rendimiento.

4. **cAdvisor**: Requiere `privileged: true` o montar `/` del host. Consideración de seguridad.

### Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Ansible no disponible en Windows nativo | Usar WSL2 o ejecutar desde la VM directamente |
| `hey` no instalado en el host | `tests/install-tools.sh` con `go install` o binario precompilado |
| Puertos 80/443 ocupados | Usar puertos alternativos (8080/8443) en docker-compose |
| Certificado self-signed bloqueado por navegador | Documentar `-k` en curl o agregar excepción |

---

*Plan generado el 2026-07-13. Actualizar según avance del proyecto.*
