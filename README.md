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

Run the application:

```bash
uvicorn app.main:app --reload
```

Apply database migrations:

```bash
.\aplicar-migraciones.ps1
```

## API Documentation

After starting the server:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

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
- Add authentication and authorization for sensitive routes.
- Configure CORS by environment.
- Add Docker for development and deployment.
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
