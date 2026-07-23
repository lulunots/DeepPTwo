"""Batch driver for pad.py.

Processes every .ome.tif file in a folder using a multiprocessing Pool,
so cv2/tifffile are imported once per worker instead of once per file,
and all requested CPUs are actually used.
"""

import argparse
import logging
import os
import time
from functools import partial
from multiprocessing import Pool
from pathlib import Path
from typing import Tuple

from pad import _parse_color, pad

logger = logging.getLogger(__name__)


def _process_one(
    file: str,
    squaresize: int,
    outloc: str,
    pad_color: Tuple[int, int, int],
) -> Tuple[str, bool, str]:
    """Wrapper so we can catch/report per-file errors without killing the pool."""
    try:
        pad(file, squaresize, outloc, pad_color=pad_color)
        return file, True, ""
    except Exception as exc:  # noqa: BLE001 - want to keep going on single-file failures
        return file, False, str(exc)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="batch_pad.py",
        description=(
            "Pad every .ome.tif file in a folder to a square canvas (no "
            "resizing), in parallel, within a single Python process."
        ),
        epilog=(
            "Example:\n"
            "  python batch_pad.py /path/to/input_folder 214 /path/to/outloc --processes 2\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("input_folder", help="Directory containing .ome.tif files.")
    parser.add_argument("squaresize", type=int, help="Target width/height in pixels.")
    parser.add_argument("outloc", help="Directory to write output images to.")
    parser.add_argument(
        "--processes",
        type=int,
        default=os.cpu_count() or 1,
        help="Number of worker processes (match this to ncpus in your PBS job). Default: all detected cores.",
    )
    parser.add_argument(
        "--pad-color",
        type=_parse_color,
        default=(0, 0, 0),
        metavar="R,G,B",
        help="RGB color used for padding, as comma-separated ints. Default: 0,0,0 (black).",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable info-level logging.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(message)s",
    )

    files = sorted(str(p) for p in Path(args.input_folder).glob("*.ome.tif"))
    if not files:
        print(f"No .ome.tif files found in {args.input_folder}")
        return

    print(f"Found {len(files)} files. Processing with {args.processes} worker process(es)...")

    worker = partial(
        _process_one,
        squaresize=args.squaresize,
        outloc=args.outloc,
        pad_color=args.pad_color,
    )

    start = time.time()
    failures = []
    done = 0

    with Pool(processes=args.processes) as pool:
        for file, ok, err in pool.imap_unordered(worker, files):
            done += 1
            if not ok:
                failures.append((file, err))
                logger.warning("FAILED: %s (%s)", file, err)
            if done % 100 == 0 or done == len(files):
                elapsed = time.time() - start
                print(f"  {done}/{len(files)} done ({elapsed:.1f}s elapsed)")

    elapsed = time.time() - start
    print(f"\nDone: {len(files) - len(failures)}/{len(files)} succeeded in {elapsed:.1f}s")

    if failures:
        print(f"\n{len(failures)} file(s) failed:")
        for file, err in failures:
            print(f"  {file}: {err}")


if __name__ == "__main__":
    main()