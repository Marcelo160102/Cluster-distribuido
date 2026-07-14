# Apéndice de Comandos — Clúster VoIP Distribuido

> **Fase 5 — Documentación Técnica**

---

## 1. Docker

```bash
# Construir imágenes
docker compose build

# Levantar todos los servicios
docker compose up -d

# Ver estado de los contenedores
docker ps --format 'table {{.Names}}\t{{.Status}}'

# Ver logs de todos los servicios
docker compose logs -f

# Ver logs de un servicio específico
docker compose logs -f nodo1

# Detener servicios
docker compose down

# Detener y eliminar volúmenes (pierde datos)
docker compose down -v

# Reconstruir y reiniciar
docker compose up --build -d

# Ejecutar comando dentro de un contenedor
docker compose exec nodo1 cat /app/data/data.db

# Copiar archivo desde un contenedor
docker compose cp nodo1:/app/data/data.db ./backup.db
```

---

## 2. curl (Pruebas de API)

```bash
# Health
curl -s http://localhost:80/health

# Health vía HTTPS (omitir verificación de cert self-signed)
curl -sk https://localhost:443/health

# Listar datos
curl -s http://localhost:80/data -H "X-API-Key: cluster-demo-key-2026"

# Crear endpoint VoIP
curl -s -X POST http://localhost:80/data \
  -H "Content-Type: application/json" \
  -H "X-API-Key: cluster-demo-key-2026" \
  -d '{"data": "{\"extension\": \"101\", \"protocol\": \"SIP\", \"ip_address\": \"10.0.0.1\", \"status\": \"online\", \"user_agent\": \"Test\"}"}'

# Actualizar
curl -s -X PUT http://localhost:80/data/<UUID> \
  -H "Content-Type: application/json" \
  -H "X-API-Key: cluster-demo-key-2026" \
  -d '{"data": "{\"extension\": \"101\", \"protocol\": \"SIP\", \"ip_address\": \"10.0.0.1\", \"status\": \"busy\", \"user_agent\": \"Test\"}"}'

# Eliminar
curl -s -X DELETE http://localhost:80/data/<UUID> \
  -H "X-API-Key: cluster-demo-key-2026"

# Forzar error 401 (sin API Key)
curl -s http://localhost:80/data
```

---

## 3. Git

```bash
# Clonar repositorio
git clone git@github.com:Marcelo160102/Cluster-distribuido.git

# Ver estado
git status

# Ver cambios
git diff

# Agregar archivos
git add -A

# Commit
git commit -m "Mensaje descriptivo"

# Push
git push origin main

# Ver historial
git log --oneline --graph -10

# Crear rama
git checkout -b feature/mi-rama

# Cambiar de rama
git checkout main
```

---

## 4. Benchmark (rendimiento)

```bash
# Benchmark completo (200 GETs + 200 POSTs, 10 workers)
python3 tests/benchmark.py http://localhost 200 10

# Benchmark solo GET (100 requests, 5 workers)
python3 tests/benchmark.py http://localhost 100 5

# Smoke test
bash tests/smoke_test.sh

# Smoke test contra URL personalizada
bash tests/smoke_test.sh https://localhost:443
```

---

## 5. Monitoreo

```bash
# cAdvisor — verificar que expone métricas
curl -sf http://localhost:8080/metrics | head -5

# Prometheus — listar targets
curl -sf 'http://localhost:9090/api/v1/targets' | python3 -m json.tool | grep '"health"'

# Prometheus — consulta simple (nodos UP)
curl -sf 'http://localhost:9090/api/v1/query?query=up{job="cluster-nodes-app"}' | python3 -m json.tool

# Grafana — verificar login
curl -sf -o /dev/null -w "%{http_code}" http://localhost:3000

# Logs del clúster
docker compose logs --tail=50 -f
```

---

## 6. Seguridad

```bash
# Generar certificado SSL
bash scripts/gen-certs.sh

# Verificar certificado
openssl x509 -in certs/selfsigned.crt -text -noout | head -10

# Firewall UFW (en VM)
sudo ufw status verbose
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp
sudo ufw --force enable

# Verificar puertos abiertos
ss -tlnp | grep -E "80|443|9090|3000|8080"
```

---

## 7. Ansible (despliegue en VM remota)

```bash
# 1. Editar inventario con IP real
nano ansible/inventory.ini

# 2. Provisionar VM
ansible-playbook -i ansible/inventory.ini ansible/playbook-provision.yml

# 3. Desplegar clúster
ansible-playbook -i ansible/inventory.ini ansible/playbook-deploy.yml

# 4. Verificar desde la VM
ssh ubuntu@<IP> "docker ps && curl localhost:80/health"
```

---

## 8. Fail-over (prueba manual)

```bash
# 1. Identificar líder
curl -s http://localhost:80/health

# 2. Matar líder
docker stop cluster-distribuido-nodo3-1

# 3. Esperar fail-over (~10s)
sleep 12

# 4. Verificar nuevo líder
curl -s http://localhost:80/health

# 5. Probar escritura
curl -s -X POST http://localhost:80/data \
  -H "Content-Type: application/json" \
  -H "X-API-Key: cluster-demo-key-2026" \
  -d '{"data": "{\"extension\": \"999\", \"protocol\": \"SIP\", \"ip_address\": \"10.0.0.9\", \"status\": \"online\", \"user_agent\": \"Failover\"}"}'

# 6. Recuperar nodo
docker start cluster-distribuido-nodo3-1

# 7. Verificar que se sincronizó
sleep 8
curl -s http://localhost:80/data -H "X-API-Key: cluster-demo-key-2026" | python3 -m json.tool
```
