# lending — Looply demo repository

A tiny library lending service (Python 3.11+, no third-party dependencies). It exists to demo what [Looply](https://github.com/looply-dev) can do:

- **Baseline**: the repository has a clear layered architecture (see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)), so you can generate and confirm an architecture Baseline.
- **PR review**: the open pull request demos change analysis, findings, architecture comparison, and Human Decision.
- **Fix and re-review**: fix selected findings, then review the new commit again.

## Features

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/health` | Health check |
| `GET` | `/members/{id}/loans` | All loans of a member |
| `POST` | `/loans` | Borrow a book. Body: `{"member_id": 1, "book_id": 1}` |
| `POST` | `/loans/{id}/return` | Return a book. Returns the late fee in cents |
| `POST` | `/loans/{id}/renew` | Renew a loan. The new loan period starts today |
| `GET` | `/reports/overdue?member=<name>` | Report of overdue loans. `member` is optional |

Business rules (`src/lending/domain/rules.py`):

- The loan period is 14 days.
- Active loan limit: 3 books for standard members, 5 books for premium members.
- The late fee is 50 cents per day, capped at 2000 cents.
- A loan can be renewed at most 2 times.

## Run locally

```bash
# Run the tests
PYTHONPATH=src python3 -m unittest discover -s tests -t .

# Seed sample data and start the API
PYTHONPATH=src python3 -m lending.cli --db lending.db seed
PYTHONPATH=src python3 -m lending.cli --db lending.db serve --port 8000

curl -X POST localhost:8000/loans -d '{"member_id": 1, "book_id": 1}'
```

## Layout

```text
src/lending/
  domain/      Domain models, business rules, error types (pure Python, no I/O)
  storage/     SQLite connection and repository
  services/    Use-case orchestration (LendingService) and the Clock abstraction
  api/         HTTP API (standard library http.server)
  app.py       Composition root: wires storage and services together
  cli.py       Command-line entry point
tests/         unittest tests
docs/          Architecture notes
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for development conventions.
