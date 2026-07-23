"""Utility for padding OME-TIFF images to a square canvas without resizing."""

import argparse
import logging
import os
from typing import Tuple

import cv2
import tifffile

logger = logging.getLogger(__name__)


def pad(
    file: str,
    squaresize: int,
    outloc: str,
    pad_color: Tuple[int, int, int] = (0, 0, 0),
) -> str:
    """
    Pad an OME-TIFF image with a solid color so it becomes a square image of
    size `squaresize`. Does not resize — the image must already fit within
    the target size on both dimensions.

    Args:
        file: Path to the input .ome.tif image.
        squaresize: Target width/height (in pixels) of the output square image.
        outloc: Directory to write the output image to. Created if missing.
        pad_color: BGR color used for padding. Defaults to green.

    Returns:
        The path to the written output file.

    Raises:
        FileNotFoundError: If `file` does not exist.
        ValueError: If `squaresize` is not positive, or if the image exceeds
            `squaresize` in either dimension.
    """
    if not os.path.exists(file):
        raise FileNotFoundError(f"Image not found: {file}")
    if squaresize <= 0:
        raise ValueError(f"squaresize must be positive, got {squaresize}")

    os.makedirs(outloc, exist_ok=True)

    img = tifffile.imread(file, is_ome=True)
    img_name = os.path.basename(file).replace(".ome.tif", "")

    h, w = img.shape[:2]
    logger.info("original: h=%d, w=%d, ratio=%.3f", h, w, h / w)

    if h > squaresize or w > squaresize:
        raise ValueError(
            f"image ({h}x{w}) exceeds target size {squaresize}; resize before padding"
        )

    dh, dw = squaresize - h, squaresize - w
    padded_img = cv2.copyMakeBorder(
        img,
        dh // 2, dh - dh // 2,
        dw // 2, dw - dw // 2,
        cv2.BORDER_CONSTANT,
        value=pad_color,
    )

    hh, ww = padded_img.shape[:2]
    logger.info("padded: hh=%d, ww=%d", hh, ww)

    out_path = os.path.join(outloc, f"{img_name}_padded.ome.tif")
    tifffile.imwrite(out_path, padded_img)
    logger.info("wrote %s", out_path)

    return out_path


def _parse_color(value: str) -> Tuple[int, int, int]:
    """Parse an 'R,G,B' string into an (R, G, B) tuple of ints."""
    parts = value.split(",")
    if len(parts) != 3:
        raise argparse.ArgumentTypeError(
            f"pad-color must be 3 comma-separated values, got '{value}'"
        )
    try:
        return tuple(int(p) for p in parts)  # type: ignore[return-value]
    except ValueError:
        raise argparse.ArgumentTypeError(f"pad-color values must be integers, got '{value}'")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pad.py",
        description=(
            "Pad an OME-TIFF image with a solid color so it becomes a square "
            "image of the given size. Does NOT resize -- the image must "
            "already fit within the target size on both dimensions."
        ),
        epilog=(
            "Example:\n"
            "  python pad.py sample.ome.tif 1024 output_dir\n"
            "  python pad.py sample.ome.tif 1024 output_dir --pad-color 0,0,0\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "file",
        help="Path to the input .ome.tif image.",
    )
    parser.add_argument(
        "squaresize",
        type=int,
        help="Target width/height (in pixels) of the output square image.",
    )
    parser.add_argument(
        "outloc",
        help="Directory to write the output image to. Created if missing.",
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
        help="Enable info-level logging (image dimensions before/after padding).",
    )
    return parser


if __name__ == "__main__":
    args = build_parser().parse_args()
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(message)s",
    )
    out_path = pad(args.file, args.squaresize, args.outloc, pad_color=args.pad_color)
    print(f"Wrote: {out_path}")