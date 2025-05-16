#!/usr/bin/env bash
if [ "${FULL_DATA:-0}" = "1" ]; then
  echo "Fetching FULL COCO Train+Val..."
  dvc pull -r storage \
    data/coco/images/train2017 \
    data/coco/images/val2017 \
    data/coco/annotations/instances_train2017.json  \
    data/coco/annotations/instances_val2017.json
else
  echo "Fetching 1K COCO subset..."
  dvc pull -r storage \
    data/coco/subset/images \
    data/coco/subset/annotations/instances_subset.json
fi

