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

import aim
from aim.pytorch import track_gradients_dists, track_params_dists
from sklearn.metrics import roc_curve, auc, precision_recall_curve, average_precision_score


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
    num_epochs = 15
    learning_rate = 0.001

    # Initialize AIM run, tracking training progress
    aim_run = aim.Run(experiment="ResNet18_COCO")
    aim_run["hparams"] = {
        "batch_size": batch_size,
        "learning_rate": learning_rate,
        "epochs": num_epochs,
        "model": "ResNet18",
        "device": device.type
    }

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

    # Track model architecture
    try:
        aim_run.track_model_graph(model, input_shape=(1, 3, 480, 480))
    except Exception as e:
        print(f"Couldn't track model graph: {e}")

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
        total = 0
        correct = 0

        # At the beginning of each epoch, collect predictions
        all_targets = []
        all_predictions = []

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

            # Calculate accuracy
            _, predicted = torch.max(outputs.data, 1)
            total += targets.size(0)
            batch_correct = (predicted == targets).sum().item()
            correct += batch_correct
            batch_accuracy = batch_correct / targets.size(0)

            # Statistics
            running_loss += loss.item()

            # Log metrics to AIM
            aim_run.track(loss.item(), name="loss", epoch=epoch, context={"subset": "train"})
            aim_run.track(batch_accuracy, name="batch_accuracy", epoch=epoch, step=i, context={"subset": "train"})

            if i % 10 == 9:  # Print every 10 mini-batches
                avg_loss = running_loss / 10
                running_accuracy = correct / total

                print(f'Epoch: {epoch + 1}, Batch: {i + 1}, Loss: {avg_loss:.4f}, Accuracy: {running_accuracy:.4f}')

                # Track metrics every 10 batches
                aim_run.track(avg_loss, name="avg_loss", epoch=epoch, step=i // 10, context={"subset": "train"})
                aim_run.track(running_accuracy, name="running_accuracy", epoch=epoch, step=i // 10,
                              context={"subset": "train"})

                running_loss = 0.0

            all_targets.extend(targets.cpu().numpy())
            all_predictions.extend(outputs.softmax(dim=1).detach().cpu().numpy())

        # Track distributions of gradients and parameters periodically (every 2 epochs to avoid overhead)
        if epoch % 2 == 0:
            try:
                track_gradients_dists(aim_run, model)
                track_params_dists(aim_run, model)
            except Exception as e:
                print(f"Couldn't track distributions: {e}")

        # Track learning rate
        current_lr = optimizer.param_groups[0]['lr']
        aim_run.track(current_lr, name="learning_rate", epoch=epoch, context={"subset": "train"})

        # Calculate epoch accuracy
        epoch_accuracy = correct / total
        aim_run.track(epoch_accuracy, name="epoch_accuracy", epoch=epoch, context={"subset": "train"})
        print(f'Epoch: {epoch + 1} completed, Accuracy: {epoch_accuracy:.4f}')

        # After the epoch, calculate and track metrics
        if epoch % 1 == 0:  # Calculate every epoch or less frequently
            # For binary classification or per-class metrics in multiclass
            for cls in range(train_dataset.num_classes):
                # ROC and AUC
                fpr, tpr, _ = roc_curve(
                    [1 if t == cls else 0 for t in all_targets],
                    [p[cls] for p in all_predictions]
                )
                roc_auc = auc(fpr, tpr)
                aim_run.track(roc_auc, name=f"roc_auc_class_{cls}", epoch=epoch)

                # PR Curve
                precision, recall, _ = precision_recall_curve(
                    [1 if t == cls else 0 for t in all_targets],
                    [p[cls] for p in all_predictions]
                )
                ap = average_precision_score(
                    [1 if t == cls else 0 for t in all_targets],
                    [p[cls] for p in all_predictions]
                )
                aim_run.track(ap, name=f"avg_precision_class_{cls}", epoch=epoch)


        # Save checkpoint after each epoch
        checkpoint_path = os.path.join(save_dir, f"resnet18_epoch_{epoch + 1}.pth")
        torch.save({
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'accuracy': epoch_accuracy
        }, checkpoint_path)
        print(f"Checkpoint saved to {checkpoint_path}")


if __name__ == "__main__":
    main()