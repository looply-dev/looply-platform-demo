"""Command-line entry point: `seed` writes sample data, `serve` starts the HTTP API."""

import argparse

from lending.api.server import create_server
from lending.app import build_service


def _seed(db_path: str) -> None:
    """Write a few books and two members so you can try the API by hand."""
    _, repo = build_service(db_path)
    repo.add_book("The Pragmatic Programmer", "Hunt & Thomas", 2)
    repo.add_book("Designing Data-Intensive Applications", "Martin Kleppmann", 1)
    repo.add_book("A Philosophy of Software Design", "John Ousterhout", 3)
    repo.add_member("Alice", "standard")
    repo.add_member("Bob", "premium")
    print(f"seeded {db_path}")


def main() -> None:
    """Parse the subcommand and run it."""
    parser = argparse.ArgumentParser(prog="lending")
    parser.add_argument("--db", default="lending.db", help="path to the SQLite database file")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("seed", help="write sample data")
    serve = sub.add_parser("serve", help="start the HTTP API")
    serve.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    if args.command == "seed":
        _seed(args.db)
    else:
        service, _ = build_service(args.db)
        server = create_server(service, port=args.port)
        print(f"listening on http://127.0.0.1:{args.port}")
        server.serve_forever()


if __name__ == "__main__":
    main()
