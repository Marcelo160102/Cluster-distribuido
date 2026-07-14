# Políticas de Seguridad — Clúster VoIP Distribuido

> **Fase 3 — Seguridad y Alta Disponibilidad**

---

## 1. Autenticación

### 1.1 API Key en endpoints `/data`

Todos los endpoints públicos de escritura/lectura (`/data`) requieren una API Key
válida en el header `X-API-Key`.

**Configuración:**
- Variable de entorno: `API_KEY` (valor por defecto: `cluster-demo-key-2026`)
- Implementación: middleware en `app/main.py` que intercepta cualquier request a `/data`
- Respuesta ante fallo: `401 Unauthorized` con `{"detail": "API Key inválida"}`
- Los endpoints internos del clúster (`/health`, `/cluster/*`, `/election`, `/leader-announce`)
  **NO** requieren API Key (solo accesibles desde la red Docker interna)

### 1.2 Cambio de clave

```bash
# En producción, usar una clave diferente
export API_KEY=mi-clave-segura-2026
docker compose up -d
```

---

## 2. Cifrado (TLS)

### 2.1 HTTPS en el balanceador

El nginx Load Balancer termina TLS en el puerto 443:

| Componente | Puertos | Protocolo |
|---|---|---|
| nginx LB | 80 → redirige a 443 | HTTP → HTTPS |
| nginx LB | 443 (SSL) | HTTPS con TLSv1.2/TLSv1.3 |
| Nodos internos | 8000 | HTTP plano (red Docker interna aislada) |

### 2.2 Certificado

Se utiliza un certificado **self-signed** generado localmente:

```bash
bash scripts/gen-certs.sh
# Genera: certs/selfsigned.crt, certs/selfsigned.key
```

**Para producción:** reemplazar por certificado de Let's Encrypt:

```bash
sudo apt install certbot
sudo certbot certonly --standalone -d micluster.ejemplo.com
cp /etc/letsencrypt/live/micluster.ejemplo.com/fullchain.pem certs/
cp /etc/letsencrypt/live/micluster.ejemplo.com/privkey.pem certs/
```

### 2.3 Cifrado fuerte

```
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers HIGH:!aNULL:!MD5;
```

---

## 3. Firewall

### 3.1 Reglas UFW (en VM remota)

| Puerto | Protocolo | Propósito | Restricción |
|---|---|---|---|
| 22 | TCP | SSH | Solo IPs del equipo |
| 80 | TCP | HTTP → redirige a HTTPS | Público |
| 443 | TCP | HTTPS | Público |
| 9090 | TCP | Prometheus (opcional) | Solo administrador |
| 3000 | TCP | Grafana (opcional) | Solo administrador |

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable
```

---

## 4. Segregación de Redes

| Red | Componentes | Acceso externo |
|---|---|---|
| `cluster-net` (Docker bridge) | nodo1, nodo2, nodo3, LB, cAdvisor, Prometheus, Grafana | ❌ No (solo Docker interna) |
| Host | Solo LB expone puertos 80 y 443 | ✅ Sí |

El tráfico entre nodos (3PC, Bully, heartbeats, replicación, sync) viaja en HTTP
plano dentro de la red Docker bridge. Esto es aceptable porque la red es interna
y aislada del host y de internet.

---

## 5. Hardening de Contenedores

| Medida | Implementación |
|---|---|
| Usuario no-root | `USER appuser` en Dockerfile |
| Permisos de datos | `chown appuser:appuser /app/data` |
| Límites de recursos | CPU 0.5, RAM 512M por nodo |
| Sistema de archivos read-only | Solo volúmenes de datos son write |
| Contenedor sin privilegios | Sin `privileged: true` (excepto cAdvisor) |

---

## 6. Monitoreo de Seguridad

- **Logs de API Key inválida:** revisar `docker compose logs nodo1 | grep "401"`
- **Alertas de firewall:** configurar UFW logging: `sudo ufw logging on`
- **Logs de Docker:** `docker compose logs -f` para detectar actividad anómala

---

## 7. Checklist de Seguridad

| # | Medida | Estado |
|---|---|---|
| 1 | API Key configurada y diferente en producción | ☐ |
| 2 | HTTPS funcionando (puerto 443) | ☐ |
| 3 | HTTP redirige a HTTPS (puerto 80) | ☐ |
| 4 | Firewall UFW activo (solo puertos necesarios) | ☐ |
| 5 | Contenedores sin root | ☐ |
| 6 | Límites de recursos por nodo | ☐ |
| 7 | Red Docker interna sin exposición | ☐ |
| 8 | Certificado SSL válido | ☐ |
| 9 | Logs de autenticación monitorizados | ☐ |
