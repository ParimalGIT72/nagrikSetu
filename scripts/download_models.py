#!/usr/bin/env python3
"""
scripts/download_models.py

Standalone CLI utility to download and verify pre-trained models required
by Nagrik Setu (such as FastText Language Identification: lid.176.ftz).

Usage:
    python scripts/download_models.py [--force]
"""

import argparse
import hashlib
import os
import sys
import urllib.request
from pathlib import Path

FASTTEXT_MODEL_URL = "https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.ftz"
DEFAULT_TARGET_DIR = Path(__file__).resolve().parent.parent / "ml" / "models" / "fasttext"
DEFAULT_TARGET_FILE = DEFAULT_TARGET_DIR / "lid.176.ftz"
EXPECTED_MIN_SIZE_BYTES = 900_000  # ~917 KB


def download_with_progress(url: str, dest_path: Path):
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = dest_path.with_suffix(".tmp")

    print(f"Downloading from {url} ...")
    
    def reporthook(count, block_size, total_size):
        downloaded = count * block_size
        if total_size > 0:
            percent = min(100.0, downloaded * 100.0 / total_size)
            sys.stdout.write(f"\rProgress: {percent:5.1f}% [{downloaded:,} / {total_size:,} bytes]")
        else:
            sys.stdout.write(f"\rDownloaded: {downloaded:,} bytes")
        sys.stdout.flush()

    try:
        urllib.request.urlretrieve(url, temp_path, reporthook=reporthook)
        sys.stdout.write("\n")
        
        # Verify file size
        file_size = temp_path.stat().st_size
        if file_size < EXPECTED_MIN_SIZE_BYTES:
            temp_path.unlink(missing_ok=True)
            raise ValueError(f"Downloaded file size ({file_size} bytes) is smaller than expected ({EXPECTED_MIN_SIZE_BYTES} bytes).")
            
        temp_path.replace(dest_path)
        print(f"Successfully saved to: {dest_path} ({file_size:,} bytes)")
    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        raise RuntimeError(f"Download failed: {e}") from e


def main():
    parser = argparse.ArgumentParser(description="Download pre-trained models for Nagrik Setu.")
    parser.add_argument("--force", action="store_true", help="Force re-download even if model already exists.")
    args = parser.parse_args()

    print("=== Nagrik Setu Model Downloader ===")
    if DEFAULT_TARGET_FILE.exists() and not args.force:
        size = DEFAULT_TARGET_FILE.stat().st_size
        print(f"FastText model already exists at {DEFAULT_TARGET_FILE} ({size:,} bytes). Use --force to re-download.")
        return

    download_with_progress(FASTTEXT_MODEL_URL, DEFAULT_TARGET_FILE)
    print("All models ready.")


if __name__ == "__main__":
    main()
