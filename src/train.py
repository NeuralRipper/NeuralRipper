#!/usr/bin/env python3
"""
train.py - Script to train ResNet18 on COCO dataset
"""

import os
from datetime import datetime

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader

from datasets.coco import ImageDataset
from models.resnet18 import MyResNet18
from utils.transform import transform


def get_dataset_paths():
    """Get appropriate data paths based on environment variable"""
    use_full = os.environ.get("USE_FULL_DATASET", "0").lower() in ("1", "true", "yes")
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    if use_full:
        img_dir = os.path.join(base_dir, "data", "coco", "images", "train2017")
        ann_file = os.path.join(base_dir, "data", "coco", "annotations", "instances_train2017.json")
    else:
        img_dir = os.path.join(base_dir, "data", "coco", "subset", "images")
        ann_file = os.path.join(base_dir, "data", "coco", "subset", "annotations", "instances_subset.json")

    return img_dir, ann_file


def main():
    # Set device
    if torch.backends.mps.is_available():
        device = torch.device("mps")
    elif torch.cuda.is_available():
        device = torch.device("cuda")
    else:
        device = torch.device("cpu")
    print(f"Using device: {device}")

    # Set hyperparameters
    batch_size = 32
    num_epochs = 10
    learning_rate = 0.001

    # Get appropriate data paths
    img_dir, ann_file = get_dataset_paths()
    print(f"Training with data from: {img_dir}")
    print(f"Using annotations from: {ann_file}")

    # Create datasets and dataloaders
    train_dataset = ImageDataset(img_dir=img_dir, ann_file=ann_file, transform=transform)
    train_loader = DataLoader(train_dataset, batch_size=batch_size,
                              shuffle=True, num_workers=4, pin_memory=True)

    # Initialize the model
    model = MyResNet18(num_classes=train_dataset.num_classes, pretrained=False)
    model = model.to(device)

    # Define loss function and optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)

    # Training loop
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_dir = os.path.join(os.path.dirname(__file__), "..", "output", "checkpoints", timestamp)
    os.makedirs(save_dir, exist_ok=True)

    for epoch in range(num_epochs):
        model.train()
        running_loss = 0.0

        for i, (images, targets) in enumerate(train_loader):
            # Move inputs and targets to device
            images = images.to(device)
            targets = targets.to(device)

            # Zero the parameter gradients
            optimizer.zero_grad()

            # Forward + backward + optimize
            outputs = model(images)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()

            # Statistics
            running_loss += loss.item()

            if i % 10 == 9:  # Print every 10 mini-batches
                print(f'Epoch: {epoch + 1}, Batch: {i + 1}, Loss: {running_loss / 10:.4f}')
                running_loss = 0.0

        # Save checkpoint after each epoch
        checkpoint_path = os.path.join(save_dir, f"resnet18_epoch_{epoch + 1}.pth")
        torch.save({
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
        }, checkpoint_path)
        print(f"Checkpoint saved to {checkpoint_path}")


if __name__ == "__main__":
    main()