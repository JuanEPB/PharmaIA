# Pharma Neural Assistant V2

> Intelligent pharmaceutical inventory platform powered by Artificial Intelligence, FastAPI, PyTorch and MySQL.

## Overview

Pharma Neural Assistant V2 is an intelligent backend designed to simplify pharmaceutical inventory management through Natural Language Processing (NLP), predictive analytics and assisted operational workflows.

Instead of using traditional filters or SQL queries, users interact with the system using natural language.

Example:

> "Which medicines are about to expire?"

The assistant analyzes the request, identifies the user's intent using an AI model developed with PyTorch, retrieves information from a MySQL database and returns a structured response through FastAPI.

## Features

- AI-powered pharmaceutical assistant
- Medicine inventory management
- Low stock detection
- Out-of-stock detection
- Expired medicines
- Medicines about to expire
- Inventory summary
- Medicine search
- Category management
- Supplier management
- Inventory analytics
- REST API with FastAPI
- Intent recognition using PyTorch
- MySQL integration
- Interactive Swagger documentation
- Conversational memory
- Conversational actions with confirmation
- Inventory movements
- Predictive dashboard
- Depletion prediction
- Purchase planner
- Recommendation engine
- Anomaly detection
- AI reports
- Voice assistant endpoints
- Vision label analysis
- User feedback learning
- Automated tests

## Technology Stack

| Technology | Purpose |
|------------|---------|
| Python | Backend |
| FastAPI | REST API |
| PyTorch | Intent classification |
| MySQL | Database |
| Pydantic | Validation |
| Uvicorn | ASGI server |
| Pytest | Automated tests |

## Project Structure

```text
app/
├── ai/
├── api/
├── config/
├── core/
├── database/
├── middleware/
├── models/
├── repositories/
├── services/
├── utils/
└── main.py

migrations/
model/
tests/
training/
docs/
```

## Installation

Clone the repository:

```bash
git clone https://github.com/JuanEPB/PharmaIA.git
cd PharmaIA
```

Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure environment variables:

```bash
copy .env.example .env
```

For production-like environments, set:

```env
ENVIRONMENT=production
CORS_ALLOW_ORIGINS=https://your-frontend-domain.com
API_KEYS=replace-with-a-secure-key
```

When `ENVIRONMENT=production` or `API_KEYS` has at least one value, protected
API routes require this header:

```http
X-API-Key: replace-with-a-secure-key
```

Run the application:

```bash
uvicorn app.main:app --reload
```

Apply database migrations:

```bash
.\aplicar-migraciones.ps1
```

## Docker

Docker was added so the project can run in the same way on different computers.
It packages the API and MySQL with the expected versions, environment variables
and ports. This reduces setup errors and makes development or deployment easier
to repeat.

Use Docker when you want to start the backend and database together without
manually installing or configuring MySQL.

Requirements:

- Docker Desktop installed and running.
- Port `8000` available for the API.
- Port `3306` available for MySQL, or change it in `docker-compose.yml`.

Run the API and MySQL locally:

```bash
docker compose up --build
```

The API will be available at:

```text
http://localhost:8000
```

Swagger documentation:

```text
http://localhost:8000/docs
```

The development API key configured in `docker-compose.yml` is:

```text
dev-api-key
```

Example request to a protected route:

```bash
curl -H "X-API-Key: dev-api-key" http://localhost:8000/inventario/resumen
```

Stop the containers:

```bash
docker compose down
```

Stop the containers and remove the MySQL volume:

```bash
docker compose down -v
```

Use `down -v` only when you want to delete the local database data created by
Docker.

## API Documentation

After starting the server:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- App/AI profile: `http://localhost:8000/perfil`
- AI capabilities for the app: `http://localhost:8000/ia/capacidades`
- Sale ticket PDF: `http://localhost:8000/ventas/{venta_id}/ticket.pdf`
- Low stock PDF: `http://localhost:8000/inventario/alertas/reporte-bajo-stock.pdf`

## AI In The App

The mobile or web app can call `/ia/capacidades` to know what the AI can do,
what is still pending and which actions are enabled for the current role.

Recommended headers for app requests:

```http
X-API-Key: dev-api-key
X-User-Id: 1
X-User-Role: encargado
```

Current roles:

- `admin`: full access.
- `supervisor`: operational and review access.
- `encargado`: inventory, reports and executable AI actions.
- `vendedor`: read-only inventory and AI consultation.

The app should use this endpoint to decide which buttons or screens to show:

- Show chat, recommendations and predictions for users with `ai:read`.
- Show purchase confirmation and autonomous execution only with `ai:execute`.
- Show inventory movements only with `inventory:write`.
- Show feedback review only with `learning:review`.

## Example Requests

Low stock:

```json
{
  "mensaje": "Which medicines have low stock?"
}
```

Expired medicines:

```json
{
  "mensaje": "Which medicines are expired?"
}
```

Medicines expiring this month:

```json
{
  "mensaje": "Which medicines expire this month?"
}
```

Inventory summary:

```json
{
  "mensaje": "Give me an inventory summary."
}
```

## Version 2 Roadmap

- Keep documentation aligned with the current codebase.
- Move historical backup files out of the active code tree.
- Extend API key authentication into login, users and roles.
- Configure CORS by environment.
- Harden Docker for production deployment.
- Prepare cloud deployment.
- Connect a frontend dashboard.
- Add report export workflows.
- Add a formal SQL migration runner.
- Replace console prints with production logging.

## Version 2 Notes

The API now reports version `2.0.0`.

See [`docs/VERSION_2.md`](docs/VERSION_2.md) for the Version 2 scope, priorities and next steps.

## Authors

Areli De Jesus Flores  
Software Developer

Juan Eduardo Pina Bibiano  
Software Developer

## License

This project is distributed under the MIT License.

