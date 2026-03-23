# DevSecOps Playground

> Proyecto de aprendizaje autodidáctico. Construido para entender microservicios, FastAPI, Docker y DevSecOps desde cero — no pensado para producción.

Sistema de detección de eventos sospechosos basado en microservicios.

## Arquitectura

Tres servicios independientes comunicados por HTTP via push:

```
[Cliente] → auth-service → event-service → alert-service
```

- **auth-service** (8000) — login, tokens, bloqueo por intentos fallidos, tres tablas en postgres:15
- **event-service** (8001) — registro de eventos con timestamp
- **alert-service** (8002) — detección de patrones, alerta ante 3 fallos en 60 segundos

## Stack

- Python 3.11 + FastAPI
- Docker + docker-compose + postgres:15
- Autenticación entre servicios via API key en header `X-Api-Key`

## Correr el sistema

```bash
docker-compose up --build
```

Los tres servicios quedan disponibles en:
- `http://localhost:8000/docs` — auth
- `http://localhost:8001/docs` — events
- `http://localhost:8002/docs` — alerts

## Variables de entorno

Cada servicio lee sus keys desde variables de entorno. Crear un archivo `.env` en la raíz con las keys correspondientes (ver `docker-compose.yml`).

## Endpoints principales

### auth-service
- `POST /login` — body: `{"user": "...", "password": "..."}`
- `GET /validate?token=...` — valida token activo
- `GET /health`

### event-service
- `POST /event` — body: `{"type": "...", "user": "..."}` + header `X-Api-Key`
- `GET /events` + header `X-Api-Key`
- `GET /health`

### alert-service
- `POST /alert` — body: `{"type": "...", "user": "...", "time": "..."}` + header `X-Api-Key`
- `GET /alerts` + header `X-Api-Key`
- `GET /health`
