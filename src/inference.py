#!/usr/bin/env python3
"""
inference.py - Script to test trained ResNet18 model on COCO dataset
"""

import os
import argparse
import json
import torch
from torchvision import transforms
from PIL import Image

from models.resnet18 import MyResNet18
from datasets.coco import ImageDataset


def load_model(checkpoint_path, device):
    """Load trained model from checkpoint and determine num_classes from it"""
    # Load checkpoint first to get model size
    checkpoint = torch.load(checkpoint_path, map_location=device)

    # Determine number of classes from the checkpoint
    fc_weight_shape = checkpoint['model_state_dict']['backbone.fc.weight'].shape
    num_classes = fc_weight_shape[0]
    print(f"Detected {num_classes} classes in the checkpoint")

    # Create model with correct size
    model = MyResNet18(num_classes=num_classes, pretrained=False)
    model.load_state_dict(checkpoint['model_state_dict'])
    model = model.to(device)
    model.eval()
    return model, num_classes


def get_transform():
    """Same transform as used in training, but without augmentations"""
    return transforms.Compose([
        transforms.Resize((480, 480)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
    ])


def load_categories(ann_file):
    """Load category names from COCO annotation file"""
    with open(ann_file, 'r') as f:
        coco = json.load(f)
    return {cat['id']: cat['name'] for cat in coco['categories']}


def main():
    parser = argparse.ArgumentParser(description='Test ResNet18 inference on COCO dataset')
    parser.add_argument('--checkpoint', required=True, help='Path to model checkpoint')
    parser.add_argument('--image', help='Path to a single image for inference')
    parser.add_argument('--val-dir', help='Path to validation images directory')
    parser.add_argument('--ann-file', help='Path to annotation file for validation')
    parser.add_argument('--top-k', type=int, default=5, help='Show top K predictions')
    args = parser.parse_args()

    # Set device
    if torch.backends.mps.is_available():
        device = torch.device("mps")
    elif torch.cuda.is_available():
        device = torch.device("cuda")
    else:
        device = torch.device("cpu")
    print(f"Using device: {device}")

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    # Default paths if not specified
    if not args.ann_file:
        args.ann_file = os.path.join(base_dir, "data", "coco", "annotations", "instances_val2017.json")

    # Load model and get number of classes from the checkpoint
    model, num_classes = load_model(args.checkpoint, device)
    transform = get_transform()

    # Load categories from annotation file
    categories = load_categories(args.ann_file)

    # Create dataset for category mapping if needed
    idx2cat_id = None
    if args.val_dir:
        dataset = ImageDataset(img_dir=args.val_dir, ann_file=args.ann_file)
        idx2cat_id = dataset.idx2cat_id

    # Single image inference
    if args.image:
        img = Image.open(args.image).convert("RGB")
        img_tensor = transform(img).unsqueeze(0).to(device)

        with torch.no_grad():
            outputs = model(img_tensor)
            probabilities = torch.nn.functional.softmax(outputs, dim=1)
            top_probs, top_idxs = torch.topk(probabilities, args.top_k)

        print(f"Top {args.top_k} predictions for {args.image}:")
        for i in range(args.top_k):
            idx = top_idxs[0][i].item()
            prob = top_probs[0][i].item()

            if idx2cat_id:
                cat_id = idx2cat_id[idx]
                cat_name = categories.get(cat_id, f"Category {cat_id}")
            else:
                cat_name = f"Class {idx}"

            print(f"{i + 1}. {cat_name}: {prob:.4f}")

    # Validation set inference
    elif args.val_dir:
        correct = 0
        total = 0

        val_dataset = ImageDataset(img_dir=args.val_dir, ann_file=args.ann_file, transform=transform)
        val_loader = torch.utils.data.DataLoader(val_dataset, batch_size=32, shuffle=False)

        with torch.no_grad():
            for images, targets in val_loader:
                images = images.to(device)
                targets = targets.to(device)

                outputs = model(images)
                _, predicted = torch.max(outputs.data, 1)

                total += targets.size(0)
                correct += (predicted == targets).sum().item()

        accuracy = 100 * correct / total
        print(f"Accuracy on validation set: {accuracy:.2f}%")

    else:
        print("Please specify either --image or --val-dir")


if __name__ == "__main__":
    main()