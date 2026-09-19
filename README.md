# ReelNest

ReelNest is an Online Cinema backend built with FastAPI.

The project provides user authentication, movie catalog management, movie interactions, shopping cart, orders and Stripe payments.

## Features

- User registration and authentication
- JWT access and refresh tokens
- Email account activation
- Movie catalog
- Movie search, filtering, sorting and pagination
- Favorites
- Likes
- Movie ratings
- Shopping cart
- Orders
- Order status management
- Stripe Checkout payments
- Stripe webhook processing
- PostgreSQL database
- Alembic migrations
- Docker and Docker Compose
- Automated tests
- Test coverage
- GitHub Actions CI
- Swagger / OpenAPI documentation

## Tech Stack

- Python 3.11
- FastAPI
- SQLAlchemy
- PostgreSQL
- Alembic
- Pydantic
- JWT
- Stripe
- Poetry
- Docker
- Docker Compose
- Pytest
- pytest-cov
- GitHub Actions

## Project Structure

```text
reelnest/
├── alembic/
│   ├── versions/
│   └── env.py
├── src/
│   ├── api/
│   │   └── v1/
│   ├── core/
│   ├── db/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   └── main.py
├── tests/
├── .github/
│   └── workflows/
│       └── ci.yml
├── .dockerignore
├── .env.example
├── .gitignore
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── poetry.lock
├── pyproject.toml
└── README.md
