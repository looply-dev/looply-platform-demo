# Architecture

lending has four layers. Dependencies point downward only:

```text
            cli.py / app.py   (composition root, may depend on every layer)
                   │
                   ▼
                  api          HTTP parsing and error mapping
                   │
                   ▼
                services       use cases, Clock
               │        │
               ▼        ▼
            domain ◄── storage
```

## Layer responsibilities

| Layer | Module | Responsibility | May depend on |
| --- | --- | --- | --- |
| domain | `lending.domain` | Models (`Book`, `Member`, `Loan`), business rules, error types. Pure functions: no clock reads, no I/O. | nothing |
| storage | `lending.storage` | SQLite schema and `LibraryRepository`. The only layer that may use `sqlite3`. | domain |
| services | `lending.services` | `LendingService` runs use cases such as borrow and return. `Clock` supplies "today". | domain, storage |
| api | `lending.api` | Routing, JSON encoding and decoding, mapping domain errors to HTTP status codes. | services, domain (errors and models only) |

## Key constraints

1. **api must not depend on storage.** All reads and writes go through `LendingService`, so business rules have a single entry point.
2. **domain stays pure.** Rule functions receive dates as arguments and never call `date.today()`.
3. **Time comes from Clock.** The services layer gets the current date from an injected `Clock`. Tests use `FixedClock`.
4. **Data flow:** HTTP request → `api.server` → `LendingService` → `rules` (decisions) + `LibraryRepository` (reads and writes) → SQLite.

## Error mapping

| Domain error | HTTP status |
| --- | --- |
| `NotFound` | 404 |
| Any other `LendingError` | 409 |
| `ValueError` (invalid request parameters) | 400 |
