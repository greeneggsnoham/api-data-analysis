"""
Unit tests for merge_files.py.
"""
import tempfile
import unittest
from pathlib import Path

from merge_files import list_csv_files, merge_csvs, main


def _write_csv(path: Path, header: str, rows: list[str]) -> None:
    """
    Write a CSV file with a header and rows.

    Parameters:
    path (Path): Output file path.
    header (str): Header line.
    rows (list[str]): Data rows.
    """
    content = "\n".join([header, *rows]) + "\n"
    path.write_text(content, encoding="utf-8")


class MergeFilesTests(unittest.TestCase):
    """Tests covering core CSV merge behavior and edge cases."""

    def test_list_csv_files_non_recursive(self) -> None:
        """Only CSV files in the top-level folder are returned."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            (base / "a.csv").write_text("a,b\n1,2\n", encoding="utf-8")
            (base / "b.txt").write_text("ignore", encoding="utf-8")
            sub = base / "sub"
            sub.mkdir()
            (sub / "c.csv").write_text("a,b\n3,4\n", encoding="utf-8")

            files = list_csv_files(base, "*.csv", recursive=False)
            names = sorted(f.name for f in files)
            self.assertEqual(names, ["a.csv"])

    def test_merge_union_with_source(self) -> None:
        """Union mode includes all columns and adds source_file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            _write_csv(base / "a.csv", "x,y", ["1,2"])
            _write_csv(base / "b.csv", "y,z", ["3,4"])

            merged, exit_code = merge_csvs(
                files=[base / "a.csv", base / "b.csv"],
                delimiter=",",
                encoding="utf-8",
                add_source=True,
                mode="union",
            )

            self.assertEqual(exit_code, 0)
            self.assertIsNotNone(merged)
            self.assertIn("source_file", merged.columns)
            self.assertIn("x", merged.columns)
            self.assertIn("y", merged.columns)
            self.assertIn("z", merged.columns)

    def test_intersection_mode(self) -> None:
        """Intersection mode keeps only shared columns."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            _write_csv(base / "a.csv", "x,y", ["1,2"])
            _write_csv(base / "b.csv", "y,z", ["3,4"])

            merged, exit_code = merge_csvs(
                files=[base / "a.csv", base / "b.csv"],
                delimiter=",",
                encoding="utf-8",
                add_source=False,
                mode="intersection",
            )

            self.assertEqual(exit_code, 0)
            self.assertIsNotNone(merged)
            self.assertEqual(list(merged.columns), ["y"])

    def test_strict_mode_mismatch(self) -> None:
        """Strict mode fails when column sets differ."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            _write_csv(base / "a.csv", "x,y", ["1,2"])
            _write_csv(base / "b.csv", "y,z", ["3,4"])

            merged, exit_code = merge_csvs(
                files=[base / "a.csv", base / "b.csv"],
                delimiter=",",
                encoding="utf-8",
                add_source=False,
                mode="strict",
            )

            self.assertEqual(exit_code, 2)
            self.assertIsNone(merged)

    def test_main_no_files(self) -> None:
        """Main returns 0 when no files match the pattern."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            exit_code = main(["-i", str(base), "-p", "*.csv"])
            self.assertEqual(exit_code, 0)


if __name__ == "__main__":
    unittest.main()
