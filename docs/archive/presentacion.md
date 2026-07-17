---
title: "Clúster Distribuido VoIP"
subtitle: "Sistemas Distribuidos 2026"
author: "Integrantes del equipo"
date: "2026-07-13"
---

# Slide 1: Portada

**Clúster Distribuido de Servicios Web**  
Registro de Endpoints VoIP con Alta Disponibilidad  

Sistemas Distribuidos — 2026

---

# Slide 2: Tipo de Clúster

## Servicios Web (no HPC ni Big Data)

- **Carga:** operaciones CRUD concurrentes
- **Latencia requerida:** < 100 ms
- **Protocolo de consenso:** 3PC (Three-Phase Commit)
- **Elección de líder:** Bully Algorithm
- **Stack:** FastAPI + SQLite WAL + Docker + nginx

---

# Slide 3: Arquitectura (C2 Contenedores)

```
Cliente → nginx LB (:80/:443) → nodo1 | nodo2 | nodo3
                                      ↘ ↙
                                  3PC + Bully + Heartbeat

Monitoreo: cAdvisor → Prometheus → Grafana
```

Diagrama completo C4 en `docs/arquitectura.md`

---

# Slide 4: Demo

## Escenarios en vivo

1. **Crear endpoint VoIP** → replicación 3PC a seguidores
2. **Fail-over** → matar líder, nuevo líder elegido en ~10s
3. **Recuperación** → nodo caído se sincroniza automáticamente
4. **HTTPS + API Key** → seguridad funcional

---

# Slide 5: Métricas de Rendimiento

| Escenario | Resultado |
|---|---|
| GET /data | p50=598ms, 16 req/s |
| POST /data | 5 req/s efectivos |
| Fail-over bajo carga | 100% OK, 0 errores |

**Cuello de botella:** round-robin ciego del LB para escrituras  
**Recomendación:** sticky sessions / leader-aware routing

---

# Slide 6: Conclusiones

- Clúster funcional con **tolerancia a fallos**
- **3PC** implementado como protocolo de consenso
- **Fail-over** transparente para lecturas
- **Seguridad**: HTTPS + API Key + firewall
- **Monitoreo**: Prometheus + Grafana
- **Infraestructura como código**: Docker Compose + Ansible

### Lecciones aprendidas
- 3PC es viable para 3 nodos pero añade latencia
- El LB necesita ser leader-aware para escrituras
- Las pruebas de rendimiento revelaron cuellos que el diseño teórico no anticipó
