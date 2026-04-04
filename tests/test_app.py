import unittest

from app import run_app
from BackEnd.core.paths import prepare_data_dirs, DATA_DIR


class TestApp(unittest.TestCase):

    def test_paths_integrity(self):
        """Ensure system paths are initialized correctly."""
        prepare_data_dirs()
        self.assertTrue(DATA_DIR.exists())
        self.assertTrue((DATA_DIR / "cache").exists())

    def test_bootstrap(self):
        """Check if main entry point is callable."""
        self.assertTrue(callable(run_app))


if __name__ == "__main__":
    unittest.main()
