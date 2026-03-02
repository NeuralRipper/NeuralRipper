"""
Structured logging utilities for training notebooks.
Replaces print statements with formatted, timestamped logging.
"""

import logging
import sys
import time
from datetime import datetime
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Colored formatter for better readability in notebooks."""
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[92m',      # Green
        'WARNING': '\033[93m',   # Yellow  
        'ERROR': '\033[91m',     # Red
        'CRITICAL': '\033[95m',  # Magenta
        'SUCCESS': '\033[92m',   # Green
        'ENDC': '\033[0m'        # End color
    }
    
    def format(self, record):
        # Add color
        log_color = self.COLORS.get(record.levelname, self.COLORS['ENDC'])
        record.levelname = f"{log_color}{record.levelname}{self.COLORS['ENDC']}"
        return super().format(record)


def get_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    Get a formatted logger with colors and structure.
    
    Args:
        name: Logger name (e.g., "ResNet18-Experiment")
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
    
    Returns:
        Configured logger instance
    """
    # Create unique logger name with timestamp to avoid conflicts
    unique_name = f"{name}_{int(time.time())}"
    logger = logging.getLogger(unique_name)
    logger.setLevel(getattr(logging, level.upper()))
    logger.propagate = False

    # Clear any existing handlers
    logger.handlers.clear()

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, level.upper()))

    # Create formatter
    formatter = ColoredFormatter(
        '%(asctime)s - %(levelname)s - %(name)s - PID:%(process)d - TID:%(thread)d - %(message)s'
    )
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)

    # Add custom methods
    logger.success = lambda msg, *args, **kwargs: logger.info(f"{msg}", *args, **kwargs)
    logger.epoch_start = lambda epoch, total: logger.info(f"Starting Epoch {epoch}/{total}")
    logger.epoch_complete = lambda epoch, loss, acc: logger.info(f"Epoch {epoch} completed - Loss: {loss:.4f}, Acc: {acc:.4f}")
    logger.training_start = lambda model, epochs: logger.info(f"Starting {model} training for {epochs} epochs")
    logger.training_complete = lambda: logger.info("Training completed successfully!")
    logger.model_checkpoint = lambda acc: logger.info(f"New best model saved - Accuracy: {acc:.4f}")

    return logger


def get_experiment_logger(model_name: str, dataset_name: str) -> logging.Logger:
    """
    Get a logger specifically for experiment tracking.
    
    Args:
        model_name: Model name (e.g., "ResNet18")
        dataset_name: Dataset name (e.g., "CIFAR-100")
    
    Returns:
        Configured experiment logger
    """
    experiment_name = f"{model_name}-{dataset_name}"
    logger = get_logger(experiment_name)
    
    # Add experiment-specific methods
    logger.experiment_start = lambda: logger.info(f"Starting {experiment_name} experiment")
    logger.experiment_config = lambda config: logger.info(f"Configuration: {config}")
    logger.data_loaded = lambda size: logger.info(f"Data loaded - {size:,} samples")
    logger.model_created = lambda params: logger.info(f"Model created - {params:,} parameters")
    logger.device_info = lambda device: logger.info(f"Using device: {device}")
    
    return logger


def log_training_progress(logger: logging.Logger, epoch: int, batch_idx: int, 
                         total_batches: int, loss: float, acc: float, 
                         log_interval: int = 10):
    """
    Log training progress at specified intervals.
    
    Args:
        logger: Logger instance
        epoch: Current epoch
        batch_idx: Current batch index
        total_batches: Total number of batches
        loss: Current loss
        acc: Current accuracy
        log_interval: Log every N batches
    """
    if batch_idx % log_interval == (log_interval - 1):
        logger.info(f"Epoch {epoch} | Batch {batch_idx + 1}/{total_batches} | "
                   f"Loss: {loss:.4f} | Acc: {acc:.4f}")


def log_epoch_summary(logger: logging.Logger, epoch: int, total_epochs: int,
                     epoch_loss: float, epoch_acc: float, epoch_time: float, 
                     eta: float = None, lr: float = None):
    """
    Log comprehensive epoch summary.
    
    Args:
        logger: Logger instance
        epoch: Current epoch
        total_epochs: Total epochs
        epoch_loss: Epoch loss
        epoch_acc: Epoch accuracy
        epoch_time: Time taken for epoch
        eta: Estimated time to completion
        lr: Current learning rate
    """
    summary = f"Epoch {epoch + 1}/{total_epochs} | Loss: {epoch_loss:.4f} | " \
              f"Acc: {epoch_acc:.4f} | Time: {epoch_time:.1f}s"
    
    if eta is not None:
        summary += f" | ETA: {eta/60:.1f}min"
    if lr is not None:
        summary += f" | LR: {lr:.2e}"
    
    logger.info(summary)


def log_system_info(logger: logging.Logger, device: str, total_params: int, 
                   batch_size: int, learning_rate: float):
    """
    Log system and training configuration.
    
    Args:
        logger: Logger instance
        device: Training device
        total_params: Total model parameters
        batch_size: Batch size
        learning_rate: Learning rate
    """
    logger.info("="*60)
    logger.info("TRAINING CONFIGURATION")
    logger.info("="*60)
    logger.device_info(device)
    logger.info(f"Parameters: {total_params:,}")
    logger.info(f"Batch size: {batch_size}")
    logger.info(f"Learning rate: {learning_rate:.2e}")
    logger.info("="*60)


def log_mlflow_info(logger: logging.Logger, mlflow_uri: str, experiment_name: str, 
                   tracking_enabled: bool = True):
    """
    Log MLflow tracking information.
    
    Args:
        logger: Logger instance
        mlflow_uri: MLflow tracking URI
        experiment_name: Experiment name
        tracking_enabled: Whether MLflow tracking is enabled
    """
    if tracking_enabled:
        # Mask credentials in URI for security
        display_uri = mlflow_uri
        if '@' in mlflow_uri:
            # Extract domain part after credentials
            domain_part = mlflow_uri.split('@')[1]
            display_uri = f"https://***:***@{domain_part}"
        
        logger.info(f"MLflow tracking: {display_uri}")
        logger.info(f"Experiment: {experiment_name}")
        logger.info(f"Credentials: {'Successfully Loaded from AWS' if '@' in mlflow_uri else 'Not found'}")
    else:
        logger.warning("MLflow tracking disabled")


def log_training_summary(logger: logging.Logger, total_time: float, 
                        best_accuracy: float, epochs_completed: int):
    """
    Log final training summary.
    
    Args:
        logger: Logger instance
        total_time: Total training time in minutes
        best_accuracy: Best accuracy achieved
        epochs_completed: Number of epochs completed
    """
    logger.info("="*60)
    logger.info("TRAINING SUMMARY")
    logger.info("="*60)
    logger.info(f"Total time: {total_time:.1f} minutes")
    logger.info(f"Best accuracy: {best_accuracy:.4f}")
    logger.info(f"Epochs completed: {epochs_completed}")
    logger.info("="*60)
    logger.training_complete()