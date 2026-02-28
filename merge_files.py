#!/usr/bin/env python3
# Usage examples (copy/paste):
# py merge_files.py -i SS -o merged.csv
# py merge_files.py -i data -o out.csv -s -m intersection
# py merge_files.py -i data -p "cost_*.csv" -r -d ";" -e "utf-8-sig"
# py merge_files.py -i data -o out.csv --keep-identifying-info
# py merge_files.py -i data --only-projects ELM,PolicyExplorer,AskEdHelp, edhelp-usva
# py merge_files.py -i data --exclude-projects ELM
"""
Merge multiple CSV files into a single output CSV with configurable options.
"""
import argparse
import glob
from pathlib import Path
from typing import Iterable, List, Sequence, Set, Tuple

# pandas provides robust CSV parsing and DataFrame concatenation utilities.
import pandas as pd


# List CSV files in a folder with optional recursion.
def list_csv_files(
    input_dir: Path,
    pattern: str,
    recursive: bool,
) -> List[Path]:
    """
    Return a list of CSV file paths matching a glob pattern.

    Parameters:
    input_dir (Path): Base folder to search.
    pattern (str): Glob pattern to match.
    recursive (bool): Whether to search recursively.

    Returns:
    List[Path]: List of matching file paths.
    """
    # Build a glob pattern like "*.csv" or "**/*.csv"
    glob_pattern = str(input_dir / ("**/" + pattern if recursive else pattern))
    return [Path(p) for p in glob.glob(glob_pattern, recursive=recursive)]


# Parse CLI arguments, optionally from a provided argv.
def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """
    Parse command-line arguments.

    Parameters:
    argv (Sequence[str] | None): Optional argv for testing.

    Returns:
    argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Merge multiple CSV files into a single CSV."
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        default=Path("SS"),
        help='Folder containing CSV files (default: "SS")',
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("merged.csv"),
        help='Output CSV file path (default: "merged.csv")',
    )
    parser.add_argument(
        "-s",
        "--add-source",
        action="store_true",
        help='Add a "source_file" column with the original filename',
    )
    parser.add_argument(
        "-d",
        "--delimiter",
        default=",",
        help='CSV delimiter (default: ","). Use ";" for semicolon, etc.',
    )
    parser.add_argument(
        "-e",
        "--encoding",
        default="utf-8",
        help=(
            'File encoding (default: "utf-8"). Try "utf-8-sig" or '
            '"cp1252" if needed.'
        ),
    )
    parser.add_argument(
        "-m",
        "--mode",
        choices=["union", "intersection", "strict"],
        default="union",
        help=(
            "How to handle differing columns across files:\n"
            "- union (default): include all columns from any file; fill "
            "missing with blank\n"
            "- intersection: only keep columns common to all files\n"
            "- strict: require identical columns across files (error if not)"
        ),
    )
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Search input folder recursively",
    )
    parser.add_argument(
        "-p",
        "--pattern",
        default="*.csv",
        help='Filename pattern to match (default: "*.csv")',
    )
    parser.add_argument(
        "--keep-identifying-info",
        action="store_true",
        help=(
            "Preserve identifying columns such as 'project_name' "
            "(default: remove)."
        ),
    )
    parser.add_argument(
        "--only-projects",
        default="",
        help=(
            "Comma-separated project_name values to keep. Implies "
            "keeping identifying info."
        ),
    )
    parser.add_argument(
        "--exclude-projects",
        default="",
        help=(
            "Comma-separated project_name values to remove. Implies "
            "removing identifying info."
        ),
    )

    return parser.parse_args(argv)


# Remove the output file from the input file list, if present.
def exclude_output_file(files: Iterable[Path], output: Path) -> List[Path]:
    """
    Remove the output file from the list of input files if present.

    Parameters:
    files (Iterable[Path]): Candidate input files.
    output (Path): Output path to exclude.

    Returns:
    List[Path]: Filtered list of input files.
    """
    try:
        out_resolved = output.resolve()
        return [f for f in files if f.resolve() != out_resolved]
    except Exception:
        # If resolve() fails (e.g., path doesn't exist yet), fall back.
        return list(files)


# Read a single CSV into a DataFrame with consistent typing.
def read_csv_file(
    file_path: Path,
    delimiter: str,
    encoding: str,
    add_source: bool,
    remove_identifying_info: bool,
    only_projects: Set[str],
    exclude_projects: Set[str],
) -> pd.DataFrame:
    """
    Read a CSV file into a DataFrame, optionally injecting source filename.

    Parameters:
    file_path (Path): CSV file path.
    delimiter (str): CSV delimiter.
    encoding (str): File encoding.
    add_source (bool): Whether to add a source_file column.
    remove_identifying_info (bool): Whether to drop identifying columns.
    only_projects (Set[str]): Project names to keep.
    exclude_projects (Set[str]): Project names to remove.

    Returns:
    pd.DataFrame: Parsed DataFrame.
    """
    # Read all values as text to avoid type conflicts across files.
    df = pd.read_csv(
        file_path,
        sep=delimiter,
        dtype=str,
        encoding=encoding,
    )

    if add_source:
        # Insert at first column position to keep it visible.
        if "source_file" not in df.columns:
            df.insert(0, "source_file", file_path.name)
        else:
            # If it already exists, still set it so it's correct.
            df["source_file"] = file_path.name

    if only_projects or exclude_projects:
        df = filter_projects(df, only_projects, exclude_projects)

    if remove_identifying_info:
        df = drop_identifying_columns(df)

    df = add_helper_columns(df)

    return df


# Drop identifying columns such as project name.
def drop_identifying_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drop identifying columns from a DataFrame.

    Parameters:
    df (pd.DataFrame): Input DataFrame.

    Returns:
    pd.DataFrame: DataFrame without identifying columns.
    """
    # Edge case: if the column does not exist, leave the DataFrame unchanged.
    identifying_columns = {"project_name"}
    to_drop = [col for col in df.columns if col in identifying_columns]
    if not to_drop:
        return df
    return df.drop(columns=to_drop)


# Filter rows based on project_name values.
def filter_projects(
    df: pd.DataFrame,
    only_projects: Set[str],
    exclude_projects: Set[str],
) -> pd.DataFrame:
    """
    Filter rows using the project_name column.

    Parameters:
    df (pd.DataFrame): Input DataFrame.
    only_projects (Set[str]): Project names to keep.
    exclude_projects (Set[str]): Project names to remove.

    Returns:
    pd.DataFrame: Filtered DataFrame.
    """
    if not only_projects and not exclude_projects:
        return df

    if "project_name" not in df.columns:
        print("Skipping project filter; missing column: project_name")
        return df

    if only_projects:
        return df[df["project_name"].isin(only_projects)].copy()

    return df[~df["project_name"].isin(exclude_projects)].copy()


# Align columns across frames based on the selected mode.
def apply_column_mode(
    frames: List[pd.DataFrame],
    cols_sets: List[Set[str]],
    mode: str,
) -> Tuple[List[pd.DataFrame], int]:
    """
    Align columns across dataframes according to the chosen mode.

    Parameters:
    frames (List[pd.DataFrame]): DataFrames to align.
    cols_sets (List[Set[str]]): Column sets for each DataFrame.
    mode (str): One of "union", "intersection", "strict".

    Returns:
    Tuple[List[pd.DataFrame], int]: (Adjusted frames, exit code).
    """
    if mode == "intersection":
        common_cols = set.intersection(*cols_sets) if cols_sets else set()
        # Keep order of the first dataframe for consistency.
        ordered_common = [c for c in frames[0].columns if c in common_cols]
        return [df[ordered_common] for df in frames], 0

    if mode == "strict":
        first_cols = frames[0].columns.tolist()
        for df in frames[1:]:
            if df.columns.tolist() != first_cols:
                print(
                    "ERROR: Files have different columns. Use --mode union or "
                    "intersection instead."
                )
                return frames, 2

    return frames, 0


# Parse comma-separated project names into a set.
def parse_project_list(value: str) -> Set[str]:
    """
    Parse a comma-separated list of project names.

    Parameters:
    value (str): Comma-separated project names.

    Returns:
    Set[str]: Cleaned set of project names.
    """
    if not value:
        return set()
    items = [item.strip() for item in value.split(",")]
    return {item for item in items if item}


# Remove duplicate rows based on specific identifying fields.
def drop_duplicate_rows(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """
    Drop duplicate rows based on the identifying column set.

    Parameters:
    df (pd.DataFrame): Input DataFrame.

    Returns:
    Tuple[pd.DataFrame, int]: (Deduplicated DataFrame, removed row count).
    """
    # Edge case: if any columns are missing, skip de-duplication.
    dedupe_cols = [
        "start_time",
        "end_time",
        "start_time_iso",
        "end_time_iso",
        "amount_value",
        "amount_currency",
        "line_item",
        "project_id",
        "organization_id",
    ]
    missing = [col for col in dedupe_cols if col not in df.columns]
    if missing:
        print(
            "Skipping duplicate removal; missing columns: "
            + ", ".join(missing)
        )
        return df, 0

    before = len(df)
    deduped = df.drop_duplicates(subset=dedupe_cols, keep="first")
    removed = before - len(deduped)
    return deduped, removed


# Add helper month columns derived from ISO timestamps.
def add_helper_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add helper columns derived from timestamp fields.

    Parameters:
    df (pd.DataFrame): Input DataFrame.

    Returns:
    pd.DataFrame: DataFrame with helper columns added.
    """
    # Edge case: if required columns are missing, leave unchanged.
    required = ["start_time_iso", "end_time_iso"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        print(
            "Skipping helper columns; missing columns: "
            + ", ".join(missing)
        )
        return df

    start_dt = pd.to_datetime(df["start_time_iso"], errors="coerce", utc=True)
    end_dt = pd.to_datetime(df["end_time_iso"], errors="coerce", utc=True)
    df["start_month"] = start_dt.dt.strftime("%Y-%m %B")
    df["end_month"] = end_dt.dt.strftime("%Y-%m %B")
    return df


# Merge multiple CSV files into a single DataFrame.
def merge_csvs(
    files: Sequence[Path],
    delimiter: str,
    encoding: str,
    add_source: bool,
    remove_identifying_info: bool,
    only_projects: Set[str],
    exclude_projects: Set[str],
    mode: str,
) -> Tuple[pd.DataFrame | None, int]:
    """
    Read and merge CSV files into a single DataFrame.

    Parameters:
    files (Sequence[Path]): CSV files to merge.
    delimiter (str): CSV delimiter.
    encoding (str): File encoding.
    add_source (bool): Whether to add a source_file column.
    remove_identifying_info (bool): Whether to drop identifying columns.
    only_projects (Set[str]): Project names to keep.
    exclude_projects (Set[str]): Project names to remove.
    mode (str): Column handling mode.

    Returns:
    Tuple[pd.DataFrame | None, int]: (Merged frame or None, exit code).
    """
    # Approach: read all files as text, align columns per mode, then concat.
    frames: List[pd.DataFrame] = []
    cols_sets: List[Set[str]] = []

    print(f"Found {len(files)} files. Reading...")
    for file_path in files:
        print(f"- {file_path}")
        try:
            df = read_csv_file(
                file_path=file_path,
                delimiter=delimiter,
                encoding=encoding,
                add_source=add_source,
                remove_identifying_info=remove_identifying_info,
                only_projects=only_projects,
                exclude_projects=exclude_projects,
            )
        except Exception as ex:
            print(f"ERROR: Could not read {file_path}: {ex}")
            return None, 1

        frames.append(df)
        cols_sets.append(set(df.columns))

    frames, exit_code = apply_column_mode(frames, cols_sets, mode)
    if exit_code != 0:
        return None, exit_code

    merged = pd.concat(frames, ignore_index=True, sort=False)
    merged, removed = drop_duplicate_rows(merged)
    if removed > 0:
        print(f"Removed {removed} duplicate rows.")
    else:
        print("Removed 0 duplicate rows.")
    return merged, 0


# Persist the merged DataFrame to disk.
def write_output(merged: pd.DataFrame, output: Path, encoding: str) -> int:
    """
    Write the merged DataFrame to disk.

    Parameters:
    merged (pd.DataFrame): Data to write.
    output (Path): Output CSV path.
    encoding (str): File encoding.

    Returns:
    int: Exit code.
    """
    # Ensure output folder exists.
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        merged.to_csv(output, index=False, encoding=encoding)
    except Exception as ex:
        print(f"ERROR writing {output}: {ex}")
        return 3
    return 0


# CLI entry point with optional argv for tests.
def main(argv: Sequence[str] | None = None) -> int:
    """
    Entry point for CLI usage.

    Parameters:
    argv (Sequence[str] | None): Optional argv for testing.

    Returns:
    int: Exit code.
    """
    args = parse_args(argv)

    only_projects = parse_project_list(args.only_projects)
    exclude_projects = parse_project_list(args.exclude_projects)
    if only_projects and exclude_projects:
        print("ERROR: Use only one of --only-projects or --exclude-projects.")
        return 2

    remove_identifying_info = not args.keep_identifying_info
    if only_projects:
        remove_identifying_info = False
    elif exclude_projects:
        remove_identifying_info = True

    files = sorted(list_csv_files(args.input, args.pattern, args.recursive))
    files = exclude_output_file(files, args.output)

    # Edge case: no matches should exit cleanly with code 0.
    if not files:
        print(
            f"No CSV files found in {args.input} matching {args.pattern}. "
            "Nothing to do."
        )
        return 0

    merged, exit_code = merge_csvs(
        files=files,
        delimiter=args.delimiter,
        encoding=args.encoding,
        add_source=args.add_source,
        remove_identifying_info=remove_identifying_info,
        only_projects=only_projects,
        exclude_projects=exclude_projects,
        mode=args.mode,
    )
    if exit_code != 0 or merged is None:
        return exit_code

    exit_code = write_output(merged, args.output, args.encoding)
    if exit_code != 0:
        return exit_code

    print(
        f"Done. Wrote {len(merged)} rows and {len(merged.columns)} columns "
        f"to {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
