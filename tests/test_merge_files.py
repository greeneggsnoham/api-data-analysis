"""
Unit tests for merge_files.py.
"""
import tempfile
import unittest
from pathlib import Path

# pandas is used to build DataFrames for unit tests.
import pandas as pd

from merge_files import (
    drop_duplicate_rows,
    drop_identifying_columns,
    list_csv_files,
    merge_csvs,
    main,
)


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
                remove_identifying_info=False,
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
                remove_identifying_info=False,
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
                remove_identifying_info=False,
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

    def test_drop_identifying_columns(self) -> None:
        """Project name column is removed when requested."""
        df = pd.DataFrame({"project_name": ["a"], "x": ["1"]})
        cleaned = drop_identifying_columns(df)
        self.assertNotIn("project_name", cleaned.columns)
        self.assertIn("x", cleaned.columns)

    def test_merge_removes_project_name(self) -> None:
        """Merge removes project_name when remove_identifying_info is True."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            _write_csv(base / "a.csv", "project_name,x", ["proj,1"])

            merged, exit_code = merge_csvs(
                files=[base / "a.csv"],
                delimiter=",",
                encoding="utf-8",
                add_source=False,
                remove_identifying_info=True,
                mode="union",
            )

            self.assertEqual(exit_code, 0)
            self.assertIsNotNone(merged)
            self.assertNotIn("project_name", merged.columns)

    def test_drop_duplicate_rows_removes_matches(self) -> None:
        """Duplicate rows across identifying columns are removed."""
        df = pd.DataFrame(
            [
                {
                    "start_time": "1",
                    "end_time": "2",
                    "start_time_iso": "1",
                    "end_time_iso": "2",
                    "amount_value": "10",
                    "amount_currency": "USD",
                    "line_item": "a",
                    "project_id": "p1",
                    "organization_id": "o1",
                    "extra": "x",
                },
                {
                    "start_time": "1",
                    "end_time": "2",
                    "start_time_iso": "1",
                    "end_time_iso": "2",
                    "amount_value": "10",
                    "amount_currency": "USD",
                    "line_item": "a",
                    "project_id": "p1",
                    "organization_id": "o1",
                    "extra": "y",
                },
            ]
        )
        deduped, removed = drop_duplicate_rows(df)
        self.assertEqual(removed, 1)
        self.assertEqual(len(deduped), 1)


if __name__ == "__main__":
    unittest.main()
