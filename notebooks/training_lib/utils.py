"""
Training utilities for device selection, optimizers, criterions, and helper functions.
Extracted from all notebook implementations.
"""

import torch
import torch.nn as nn
import torch.optim as optim
import psutil
import platform
import subprocess
import numpy as np
from datetime import datetime


def set_device():
    """
    Set appropriate device for training.
    Priority: MPS (Apple Silicon) -> CUDA -> CPU
    """
    if torch.backends.mps.is_available():
        return torch.device("mps")
    elif torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def get_optimizer(model_parameters, optimizer_name="SGD", learning_rate=5e-3, **kwargs):
    """
    Create optimizer with common configurations found in notebooks.
    
    Args:
        model_parameters: model.parameters()
        optimizer_name: 'SGD' or 'AdamW'
        learning_rate: Learning rate
        **kwargs: Additional optimizer parameters
    
    Returns:
        torch.optim optimizer
    """
    if optimizer_name.upper() == "SGD":
        return optim.SGD(
            model_parameters,
            lr=learning_rate,
            momentum=kwargs.get('momentum', 0.9),
            weight_decay=kwargs.get('weight_decay', 4e-5)
        )
    elif optimizer_name.upper() == "ADAMW":
        return optim.AdamW(
            model_parameters,
            lr=learning_rate,
            weight_decay=kwargs.get('weight_decay', 0.01)
        )
    else:
        raise ValueError(f"Unsupported optimizer: {optimizer_name}")


def get_criterion(criterion_name="CrossEntropyLoss", **kwargs):
    """
    Create loss criterion.
    
    Args:
        criterion_name: Loss function name
        **kwargs: Additional criterion parameters
    
    Returns:
        torch criterion
    """
    if criterion_name == "CrossEntropyLoss":
        ignore_index = kwargs.get('ignore_index', -100)
        if ignore_index != -100:  # For text models like GPT2
            return nn.CrossEntropyLoss(ignore_index=ignore_index)
        return nn.CrossEntropyLoss()
    else:
        raise ValueError(f"Unsupported criterion: {criterion_name}")


def count_parameters(model):
    """
    Count model parameters.
    
    Returns:
        dict: total_params, trainable_params, parameters_millions, model_size_mb
    """
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    
    # Model size calculation
    param_size = sum(p.numel() * p.element_size() for p in model.parameters())
    buffer_size = sum(b.numel() * b.element_size() for b in model.buffers())
    model_size_mb = (param_size + buffer_size) / (1024 ** 2)
    
    return {
        "total_parameters": total_params,
        "trainable_parameters": trainable_params,
        "parameters_millions": round(total_params / 1e6, 2),
        "model_size_mb": round(model_size_mb, 2)
    }


def get_system_info():
    """
    Get system hardware and software information.
    Extracted from all notebooks' system parameter collection.
    """
    gpu_info = {}
    if torch.cuda.is_available():
        props = torch.cuda.get_device_properties(0)
        gpu_info = {
            "gpu_name": torch.cuda.get_device_name(0),
            "gpu_memory_gb": round(props.total_memory / (1024**3), 2),
            "cuda_version": torch.version.cuda,
            "num_gpus": torch.cuda.device_count(),
        }
    elif torch.backends.mps.is_available():
        gpu_info = {
            "gpu_name": "Apple Silicon MPS",
            "device_type": "mps"
        }

    return {
        "cpu_count": psutil.cpu_count(),
        "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "pytorch_version": torch.__version__,
        **gpu_info
    }


def get_environment_info():
    """
    Get environment and reproducibility information.
    """
    git_info = {}
    try:
        commit = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip()
        branch = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD']).decode().strip()
        git_info = {
            "git_commit": commit[:8],
            "git_branch": branch,
        }
    except:
        git_info = {"git_commit": "unknown", "git_branch": "unknown"}

    return {
        "timestamp": datetime.now().isoformat(),
        **git_info
    }


def get_gpu_metrics():
    """
    Get real-time GPU metrics for CUDA.
    """
    if not torch.cuda.is_available():
        return {}

    try:
        allocated = torch.cuda.memory_allocated()
        reserved = torch.cuda.memory_reserved()
        max_allocated = torch.cuda.max_memory_allocated()
        total = torch.cuda.get_device_properties(0).total_memory

        return {
            "gpu_memory_allocated_mb": round(allocated / (1024**2), 2),
            "gpu_memory_reserved_mb": round(reserved / (1024**2), 2),
            "gpu_memory_max_allocated_mb": round(max_allocated / (1024**2), 2),
            "gpu_memory_allocated_gb": round(allocated / (1024**3), 2),
            "gpu_memory_reserved_gb": round(reserved / (1024**3), 2),
            "gpu_memory_allocated_percent": round((allocated / total) * 100, 2),
            "gpu_memory_reserved_percent": round((reserved / total) * 100, 2),
        }
    except:
        return {}


def get_system_metrics():
    """
    Get real-time system resource utilization.
    """
    try:
        cpu_percent = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory()

        return {
            "cpu_percent": round(cpu_percent, 1),
            "memory_used_percent": round(memory.percent, 1),
            "memory_used_gb": round(memory.used / (1024**3), 2),
            "memory_available_gb": round(memory.available / (1024**3), 2),
        }
    except:
        return {}


def format_time(seconds):
    """Format seconds into human readable time."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}min"
    else:
        return f"{seconds/3600:.1f}h"


def calculate_eta(epoch_times, current_epoch, total_epochs):
    """Calculate estimated time to completion."""
    if not epoch_times or current_epoch >= total_epochs - 1:
        return 0
    
    avg_time = np.mean(epoch_times)
    remaining_epochs = total_epochs - current_epoch - 1
    return avg_time * remaining_epochs