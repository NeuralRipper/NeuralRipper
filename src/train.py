#!/usr/bin/env python3
"""
train.py - Script to train ResNet18 on COCO dataset
"""

import logging
import os
from datetime import datetime

import aim
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.metrics import roc_curve, auc, average_precision_score
from torch.utils.data import DataLoader

from datasets.coco import ImageDataset
from models.resnet18 import MyResNet18
from utils.transform import transform

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_dataset_paths():
    """
    Get appropriate data paths based on environment variable.

    Returns:
        tuple: (image_directory_path, annotation_file_path)
    """
    use_full = os.environ.get("USE_FULL_DATASET", "0").lower() in ("1", "true", "yes")
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    if use_full:
        img_dir = os.path.join(base_dir, "data", "coco", "images", "train2017")
        ann_file = os.path.join(base_dir, "data", "coco", "annotations", "instances_train2017.json")
    else:
        img_dir = os.path.join(base_dir, "data", "coco", "subset", "images")
        ann_file = os.path.join(base_dir, "data", "coco", "subset", "annotations", "instances_subset.json")

    return img_dir, ann_file


def select_device():
    """
    Select the appropriate device for training.

    Returns:
        torch.device: The device to use for training
    """
    if torch.backends.mps.is_available():
        device = torch.device("mps")
    elif torch.cuda.is_available():
        device = torch.device("cuda")
    else:
        device = torch.device("cpu")

    logger.info(f"Using device: {device}")
    return device


def setup_aim_run(batch_size, learning_rate, num_epochs, device):
    """
    Set up and configure the AIM run for experiment tracking.

    Args:
        batch_size (int): Training batch size
        learning_rate (float): Learning rate
        num_epochs (int): Number of training epochs
        device (torch.device): Training device

    Returns:
        aim.Run: Configured AIM run object
    """
    aim_run = aim.Run(experiment="ResNet18_COCO")
    aim_run["hparams"] = {
        "batch_size": batch_size,
        "learning_rate": learning_rate,
        "epochs": num_epochs,
        "model": "ResNet18",
        "device": device.type
    }
    return aim_run


def create_checkpoint_dir():
    """
    Create directory for saving model checkpoints.

    Returns:
        str: Path to checkpoint directory
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_dir = os.path.join(os.path.dirname(__file__), "..", "output", "checkpoints", timestamp)
    os.makedirs(save_dir, exist_ok=True)
    logger.info(f"Checkpoints will be saved to: {save_dir}")
    return save_dir


def save_checkpoint(model, optimizer, epoch, accuracy, save_dir):
    """
    Save model checkpoint.

    Args:
        model (nn.Module): The model to save
        optimizer (torch.optim.Optimizer): The optimizer to save
        epoch (int): Current epoch number
        accuracy (float): Current accuracy
        save_dir (str): Directory to save checkpoint

    Returns:
        str: Path to saved checkpoint
    """
    checkpoint_path = os.path.join(save_dir, f"resnet18_epoch_{epoch + 1}.pth")
    torch.save({
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'accuracy': accuracy
    }, checkpoint_path)
    logger.info(f"Checkpoint saved to {checkpoint_path}")
    return checkpoint_path


def track_metrics(aim_run, metrics_dict, epoch, step=None, context=None):
    """
    Track multiple metrics in AIM.

    Args:
        aim_run (aim.Run): AIM run object
        metrics_dict (dict): Dictionary of metrics to track
        epoch (int): Current epoch
        step (int, optional): Current step within the epoch
        context (dict, optional): Additional context for the metrics
    """
    context = context or {"subset": "train"}

    for name, value in metrics_dict.items():
        try:
            if step is not None:
                aim_run.track(value, name=name, epoch=epoch, step=step, context=context)
            else:
                aim_run.track(value, name=name, epoch=epoch, context=context)
        except Exception as e:
            pass


def calculate_metrics(all_targets, all_predictions, num_classes):
    """
    Calculate performance metrics for the model.

    Args:
        all_targets (list): Ground truth labels
        all_predictions (list): Model predictions (probabilities)
        num_classes (int): Number of classes

    Returns:
        dict: Dictionary containing model metrics
    """
    metrics = {}

    # Convert to numpy arrays
    all_targets = np.array(all_targets)
    all_predictions = np.array(all_predictions)

    # Handle average precision calculation with care to avoid warnings
    try:
        # One-hot encode targets
        y_true_one_hot = np.zeros((len(all_targets), num_classes))
        for i, target in enumerate(all_targets):
            y_true_one_hot[i, target] = 1

        # Use samples averaging which works better with multi-class data
        ap = average_precision_score(y_true_one_hot, all_predictions, average='samples')
        metrics["avg_precision"] = ap
    except Exception as e:
        logger.warning(f"Error calculating average precision: {e}")
        metrics["avg_precision"] = 0.0

    # Calculate macro-average ROC AUC across all classes
    try:
        # One-hot encode targets for multi-class ROC AUC
        y_true_one_hot = np.zeros((len(all_targets), num_classes))
        for i, target in enumerate(all_targets):
            y_true_one_hot[i, target] = 1

        # Calculate ROC AUC for each class and average them
        roc_auc_sum = 0
        valid_classes = 0

        for cls in range(num_classes):
            # Skip classes with no positive or all positive samples
            binary_targets = y_true_one_hot[:, cls]
            if np.sum(binary_targets) == 0 or np.sum(binary_targets) == len(binary_targets):
                continue

            class_probs = all_predictions[:, cls]
            try:
                fpr, tpr, _ = roc_curve(binary_targets, class_probs)
                class_auc = auc(fpr, tpr)
                roc_auc_sum += class_auc
                valid_classes += 1
            except Exception:
                continue

        # Calculate macro average only if we have valid classes
        if valid_classes > 0:
            metrics["roc_auc"] = roc_auc_sum / valid_classes
        else:
            metrics["roc_auc"] = 0.0

    except Exception as e:
        logger.warning(f"Error calculating ROC AUC: {e}")
        metrics["roc_auc"] = 0.0

    return metrics


def train_epoch(model, train_loader, optimizer, criterion, device, aim_run, epoch):
    """
    Train the model for one epoch.

    Args:
        model (nn.Module): The model to train
        train_loader (DataLoader): DataLoader for training data
        optimizer (torch.optim.Optimizer): The optimizer
        criterion (nn.Module): Loss function
        device (torch.device): Device to use for training
        aim_run (aim.Run): AIM run object for tracking
        epoch (int): Current epoch number

    Returns:
        tuple: (epoch_accuracy, all_targets, all_predictions)
    """
    model.train()
    running_loss = 0.0
    total = 0
    correct = 0
    log_interval = 10  # Log every 10 batches

    # Collect predictions for metrics calculation
    all_targets = []
    all_predictions = []

    for i, (images, targets) in enumerate(train_loader):
        # Move inputs and targets to device
        images = images.to(device)
        targets = targets.to(device)

        # Forward + backward + optimize
        optimizer.zero_grad()
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

        # Update statistics
        running_loss += loss.item()

        # Track basic metrics for every batch
        metrics = {
            "loss": loss.item(),
            "batch_accuracy": batch_accuracy
        }
        track_metrics(aim_run, metrics, epoch, step=i)

        # Periodic logging
        if i % log_interval == log_interval - 1:
            avg_loss = running_loss / log_interval
            running_accuracy = correct / total

            logger.info(f'Epoch: {epoch + 1}, Batch: {i + 1}, Loss: {avg_loss:.4f}, Accuracy: {running_accuracy:.4f}')

            # Track aggregated metrics
            periodic_metrics = {
                "avg_loss": avg_loss,
                "running_accuracy": running_accuracy
            }
            track_metrics(aim_run, periodic_metrics, epoch, step=i // log_interval)

            running_loss = 0.0

        # Store targets and predictions for later metric calculation
        all_targets.extend(targets.cpu().numpy())
        all_predictions.extend(outputs.softmax(dim=1).detach().cpu().numpy())

    # Calculate epoch accuracy
    epoch_accuracy = correct / total
    return epoch_accuracy, all_targets, all_predictions


def main():
    # Set hyperparameters
    batch_size = 32
    num_epochs = 5
    learning_rate = 0.001

    # Setup device, AIM tracking, and checkpoint directory
    device = select_device()
    aim_run = setup_aim_run(batch_size, learning_rate, num_epochs, device)
    save_dir = create_checkpoint_dir()

    # Get dataset paths and setup data
    img_dir, ann_file = get_dataset_paths()
    logger.info(f"Training with data from: {img_dir}")
    logger.info(f"Using annotations from: {ann_file}")

    # Create datasets and dataloaders - disable pin_memory on MPS
    train_dataset = ImageDataset(img_dir=img_dir, ann_file=ann_file, transform=transform)

    # Disable pin_memory explicitly on MPS to avoid warnings
    pin_memory = device.type != "mps"
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=4,
        pin_memory=pin_memory  # Disable for MPS
    )

    # Initialize the model with weights=None instead of pretrained=False
    model = MyResNet18(num_classes=train_dataset.num_classes, weights=None)
    model = model.to(device)

    # Define loss function and optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)

    # Training loop
    for epoch in range(num_epochs):
        # Train for one epoch
        epoch_accuracy, all_targets, all_predictions = train_epoch(
            model, train_loader, optimizer, criterion, device, aim_run, epoch
        )

        # Track epoch-level metrics
        aim_run.track(epoch_accuracy, name="epoch_accuracy", epoch=epoch, context={"subset": "train"})
        logger.info(f'Epoch: {epoch + 1} completed, Accuracy: {epoch_accuracy:.4f}')

        # Track learning rate
        current_lr = optimizer.param_groups[0]['lr']
        aim_run.track(current_lr, name="learning_rate", epoch=epoch)

        # Calculate and track model metrics
        metrics = calculate_metrics(
            all_targets, all_predictions, train_dataset.num_classes
        )

        # Track overall average precision
        aim_run.track(
            metrics["avg_precision"],
            name="avg_precision",
            epoch=epoch,
            context={"subset": "train"}
        )

        # Track overall ROC AUC (macro-average across classes)
        aim_run.track(
            metrics["roc_auc"],
            name="roc_auc",
            epoch=epoch,
            context={"subset": "train"}
        )

        # Save checkpoint after each epoch
        save_checkpoint(model, optimizer, epoch, epoch_accuracy, save_dir)


if __name__ == "__main__":
    main()