# auto-crawler

**auto-crawler** is an asynchronous Python-based service for collecting user car reviews from [auto.ria.com](https://auto.ria.com/uk/reviews/). It distributes crawling tasks across multiple workers, stores data in a PostgreSQL database via SQLAlchemy, and supports incremental parsing with retry logic and configurable page selection.

---

## Features

- Async web crawling with `aiohttp` and `tenacity`
- HTML parsing via `BeautifulSoup`
- Structured data persistence with `SQLAlchemy` and Alembic
- Modular repository layer: supports DB or file storage
- Worker distribution with page tracking to prevent re-parsing
- Dockerized setup with dev/test environments
- In-progress visual analytics service with `seaborn` and `matplotlib`

---

## Tech Stack

- Python 3.12
- aiohttp & BeautifulSoup
- SQLAlchemy & Alembic
- Tenacity (retry logic)
- Docker + Docker Compose
- Bandit, Flake8, isort, mypy, yamllint (for quality checks)
- pandas, seaborn, matplotlib (for plotting, WIP)

---

## Quick Start

### 1. Clone and build

```bash
git clone https://github.com/yakhoruzhenko/auto-crawler.git
cd auto-crawler
make up
```
