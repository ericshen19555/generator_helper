# -*- coding: utf-8 -*-
"""
testutils.py

Provides utilities for reading and writing test cases to files.
"""
from pathlib import Path
from typing import Iterable
import warnings


# Default filename patterns
DEFAULT_IN_PATTERN = "{index}.in"
DEFAULT_OUT_PATTERN = "{index}.out"


def write_testcases(
    *,
    folder: Path,
    testcases: Iterable[tuple[str, str]],
    in_pattern: str = DEFAULT_IN_PATTERN,
    out_pattern: str = DEFAULT_OUT_PATTERN
) -> None:
    """
    Write input/output test cases to files in the specified folder.

    Each test case is written as two files, with names generated
    from the given patterns using str.format:

        <folder>/<in_pattern>    -> input data
        <folder>/<out_pattern>   -> expected output

    Args:
        folder: Path to the directory where test case files will be saved.
        testcases: An iterable of (input_str, output_str) pairs.
        in_pattern: A pattern for naming input files (must include '{index}').
        out_pattern: A pattern for naming output files (must include '{index}').

    Notes:
        If patterns are invalid or collide, warns and falls back to default patterns:
            in: DEFAULT_IN_PATTERN ('{index}.in'), out: DEFAULT_OUT_PATTERN ('{index}.out')
    """
    # Validate placeholder presence
    if "{index}" not in in_pattern or "{index}" not in out_pattern:
        warnings.warn(
            f"Filename patterns must include '{{index}}'. "
            f"Falling back to defaults: '{DEFAULT_IN_PATTERN}', '{DEFAULT_OUT_PATTERN}'."
        )
        in_pattern, out_pattern = DEFAULT_IN_PATTERN, DEFAULT_OUT_PATTERN
    # Validate distinct patterns
    elif in_pattern == out_pattern:
        warnings.warn(
            f"Input and output patterns are identical ('{in_pattern}'). "
            f"Falling back to defaults: '{DEFAULT_IN_PATTERN}', '{DEFAULT_OUT_PATTERN}'."
        )
        in_pattern, out_pattern = DEFAULT_IN_PATTERN, DEFAULT_OUT_PATTERN

    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)

    for idx, (input_data, expected) in enumerate(testcases, start=1):
        # Generate filenames
        in_name = in_pattern.format(index=idx)
        out_name = out_pattern.format(index=idx)

        # Resolve full paths
        in_path = folder / in_name
        out_path = folder / out_name

        # Write contents
        in_path.write_text(input_data, encoding="utf-8")
        out_path.write_text(expected, encoding="utf-8")
