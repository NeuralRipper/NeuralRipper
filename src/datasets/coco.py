import os, json
from PIL import Image
import torch
from torch.utils.data import Dataset

class ImageDataset(Dataset):
    """
    COCO→classification dataset.
    Returns (image_tensor, class_index)   # single-label mode
            or (image_tensor, one_hot)    # multi-label mode
    """

    def __init__(self,
                 img_dir: str,
                 ann_file: str,
                 transform=None,
                 single_label: bool = True):
        self.img_dir      = img_dir
        self.transform    = transform
        self.single_label = single_label

        # --- parse COCO json --------------------------------------------------
        with open(ann_file, "r") as f:
            coco = json.load(f)

        cat_ids           = sorted({c["id"] for c in coco["categories"]})
        self.cat_id2idx   = {cid: i for i, cid in enumerate(cat_ids)}
        self.idx2cat_id   = {i: cid for cid, i in self.cat_id2idx.items()}
        self.num_classes  = len(cat_ids)

        anns_by_img = {}
        for ann in coco["annotations"]:
            anns_by_img.setdefault(ann["image_id"], []).append(ann["category_id"])

        # keep only images that actually have annotations
        self.samples = [
            (img["file_name"], anns_by_img[img["id"]])
            for img in coco["images"]
            if img["id"] in anns_by_img
        ]
        if not self.samples:
            raise RuntimeError("No annotated images found!")

    # -------------------------------------------------------------------------
    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        fname, cats = self.samples[idx]
        img_path    = os.path.join(self.img_dir, fname)
        img         = Image.open(img_path).convert("RGB")
        if self.transform:
            img = self.transform(img)

        if self.single_label:
            # pick the first category (or majority) → integer class index
            target = torch.tensor(self.cat_id2idx[cats[0]], dtype=torch.long)
        else:
            # multi-label one-hot vector
            target = torch.zeros(self.num_classes, dtype=torch.float32)
            for cid in cats:
                target[self.cat_id2idx[cid]] = 1.0
        return img, target
