import unittest

from lending.cli import build_parser


class ServeArgumentsTest(unittest.TestCase):
    def test_serve_listens_on_localhost_by_default(self):
        args = build_parser().parse_args(["serve"])
        self.assertEqual(args.host, "127.0.0.1")
        self.assertEqual(args.port, 8000)

    def test_serve_accepts_a_host(self):
        args = build_parser().parse_args(["serve", "--host", "0.0.0.0", "--port", "9000"])
        self.assertEqual((args.host, args.port), ("0.0.0.0", 9000))


if __name__ == "__main__":
    unittest.main()
