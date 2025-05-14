#!/usr/bin/env python3
"""
utils/make_subset.py

Creates a 1,000‑image COCO “train2017” subset:
 - Filters the JSON annotations
 - Symlinks the corresponding JPEGs
"""

import json
import os
import random

# Number of images in your subset
SUBSET_SIZE = 1000

# Paths (adjust if your layout differs)
COCO_ROOT       = "../../data/coco"
FULL_ANN_JSON   = os.path.join(COCO_ROOT, "annotations", "instances_train2017.json")
FULL_IMG_DIR    = os.path.join(COCO_ROOT, "images",      "train2017")

SUBSET_ROOT     = os.path.join(COCO_ROOT, "subset")
SUBSET_IMG_DIR  = os.path.join(SUBSET_ROOT, "images")
SUBSET_ANN_DIR  = os.path.join(SUBSET_ROOT, "annotations")
SUBSET_ANN_FILE = os.path.join(SUBSET_ANN_DIR, "instances_subset.json")

def main():
    # 1. Load full COCO train2017 annotations
    with open(FULL_ANN_JSON, "r") as f:
        full = json.load(f)

    # 2. Sample SUBSET_SIZE unique image IDs
    all_ids = [img["id"] for img in full["images"]]
    subset_ids = set(random.sample(all_ids, SUBSET_SIZE))
    print(f"Selected {len(subset_ids)} image IDs.")

    # 3. Filter images and annotations
    subset_images = [img for img in full["images"] if img["id"] in subset_ids]
    subset_anns   = [ann for ann in full["annotations"] if ann["image_id"] in subset_ids]
    print(f"  → {len(subset_images)} images, {len(subset_anns)} annotations")

    # 4. Prepare output dirs
    os.makedirs(SUBSET_IMG_DIR,  exist_ok=True)
    os.makedirs(SUBSET_ANN_DIR,  exist_ok=True)

    # 5. Write subset JSON (keep other top‑level fields intact)
    out = {
        **{k: full[k] for k in full if k not in ("images", "annotations")},
        "images":     subset_images,
        "annotations": subset_anns
    }
    with open(SUBSET_ANN_FILE, "w") as f:
        json.dump(out, f)
    print(f"Wrote subset annotations to {SUBSET_ANN_FILE}")

    # 6) Symlink each JPEG into the subset folder
    for img in subset_images:
        src = os.path.join(FULL_IMG_DIR, img["file_name"])
        dst = os.path.join(SUBSET_IMG_DIR, img["file_name"])
        if not os.path.exists(dst):
            os.symlink(os.path.abspath(src), dst)
    print(f"Created symlinks for {len(subset_images)} images in {SUBSET_IMG_DIR}")

if __name__ == "__main__":
    main()
