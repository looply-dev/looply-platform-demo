# Contributing

- **Store money as integer cents.** Never use `float` for money. Name money fields with a `_cents` suffix.
- **Parameterize all SQL.** Write SQL only in `lending.storage` and use `?` placeholders. Never build SQL with string formatting.
- **Do not read the system clock directly.** Business code gets the date from `Clock`, so tests can control it.
- **Schema changes need a migration.** `CREATE TABLE IF NOT EXISTS` does not change existing tables. When you add a column, also upgrade existing database files.
- **Respect the layers.** See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the allowed dependency directions.
- **New behavior needs tests.** Cover failure paths, not only the happy path.
- Test command: `PYTHONPATH=src python3 -m unittest discover -s tests -t .`
