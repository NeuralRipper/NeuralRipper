#!/usr/bin/env python3
"""
download_coco.py - Script to download COCO dataset from Google Cloud Storage
"""

import os
import subprocess
import sys


def download_from_gcs():
    """Download COCO data from GCS based on environment variables"""
    # Get GCS bucket path from environment variable or use default
    gcs_bucket = os.environ.get("GCS_BUCKET", "gs://neural_dive_ml_data")

    # Determine whether to download full dataset or subset
    use_full = os.environ.get("USE_FULL_DATASET", "0").lower() == "1"

    # Base directory for data
    base_dir = os.path.join(os.getcwd(), "data", "coco")
    os.makedirs(base_dir, exist_ok=True)

    print(f"Downloading {'full' if use_full else 'subset'} COCO dataset from {gcs_bucket}")

    # Download paths: (remote, local)
    download_paths = []

    if use_full:
        # Download full dataset
        download_paths.append(("annotations", "annotations"))
        download_paths.append(("images/train2017", "images/train2017"))
        download_paths.append(("images/val2017", "images/val2017"))
    else:
        # Download subset only
        download_paths.append(("subset/images", "subset/images"))
        download_paths.append(("subset/annotations", "subset/annotations"))

    # Perform downloads using gsutil
    for gcs_path, local_path in download_paths:
        src = f"{gcs_bucket}/coco/{gcs_path}"
        dst = os.path.join(base_dir, local_path)

        # Create destination directory
        os.makedirs(os.path.dirname(dst), exist_ok=True)

        print(f"Downloading {src} to {dst}")
        try:
            subprocess.run(
                ["gsutil", "-m", "cp", "-r", src, os.path.dirname(dst)],
                check=True
            )
        except subprocess.CalledProcessError as e:
            print(f"Error downloading {src}: {e}", file=sys.stderr)
            return False
        except FileNotFoundError:
            print("Error: gsutil command not found. Please install Google Cloud SDK.",
                  file=sys.stderr)
            return False

    print("Download completed successfully")
    return True


if __name__ == "__main__":
    success = download_from_gcs()
    sys.exit(0 if success else 1)