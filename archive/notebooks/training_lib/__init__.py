"""
Neural Ripper Training Library

A comprehensive training library for deep learning experiments.
Extracted and refactored from notebook implementations to eliminate code duplication.
"""

# Core training components
from .trainer import UniversalTrainer
from .mlflow_monitor import MLflowMonitor

# Model creation
from .models import (
    create_model,
    create_resnet18,
    create_efficientnet_b0,
    create_vit_base16,
    create_mobilenet_v2,
    create_gpt2,
    get_model_input_size,
    get_model_optimizer_defaults,
    get_model_info,
    print_model_summary
)

# Data utilities
from .data import (
    get_data_loader,
    get_cifar100_dataset,
    get_cifar100_transforms,
    get_conversational_data,
    create_conversational_dataloader,
    visualize_samples,
    get_dataset_info
)

# Utilities
from .utils import (
    set_device,
    get_optimizer,
    get_criterion,
    count_parameters,
    get_system_info,
    get_environment_info,
    get_gpu_metrics,
    get_system_metrics,
    format_time,
    calculate_eta
)

# Logging
from .logger import (
    get_logger,
    get_experiment_logger,
    log_training_progress,
    log_epoch_summary,
    log_system_info,
    log_mlflow_info,
    log_training_summary
)

# AWS utilities
from .aws_utils import (
    get_neuralripper_secrets,
    get_mlflow_credentials,
    build_mlflow_uri
)

# Version
__version__ = "1.0.0"
__author__ = "Neural Ripper"

# Main exports for easy notebook usage
__all__ = [
    # Core training
    "UniversalTrainer",
    "MLflowMonitor",
    
    # Model creation
    "create_model",
    "create_resnet18", 
    "create_efficientnet_b0",
    "create_vit_base16",
    "create_mobilenet_v2",
    "create_gpt2",
    "get_model_input_size",
    "get_model_optimizer_defaults",
    "get_model_info",
    "print_model_summary",
    
    # Data utilities  
    "get_data_loader",
    "get_cifar100_dataset",
    "get_cifar100_transforms",
    "get_conversational_data",
    "create_conversational_dataloader",
    "visualize_samples",
    "get_dataset_info",
    
    # Utilities
    "set_device",
    "get_optimizer", 
    "get_criterion",
    "count_parameters",
    "get_system_info",
    "get_environment_info",
    "get_gpu_metrics",
    "get_system_metrics",
    "format_time",
    "calculate_eta",
    
    # Logging
    "get_logger",
    "get_experiment_logger",
    "log_training_progress",
    "log_epoch_summary", 
    "log_system_info",
    "log_mlflow_info",
    "log_training_summary",
    
    # AWS utilities
    "get_neuralripper_secrets",
    "get_mlflow_credentials", 
    "build_mlflow_uri"
]


def quick_train(model_name: str, dataset_name: str = "cifar100", 
                epochs: int = 10, batch_size: int = 128, 
                learning_rate: float = None, use_mlflow: bool = True,
                subset_size: int = None, **kwargs):
    """
    Quick training function for rapid experimentation.
    
    Args:
        model_name: Model name ('resnet18', 'efficientnet_b0', etc.)
        dataset_name: Dataset name ('cifar100' currently supported)
        epochs: Number of epochs
        batch_size: Batch size
        learning_rate: Learning rate (auto-selected if None)
        use_mlflow: Enable MLflow tracking
        subset_size: Optional dataset subset size
        **kwargs: Additional parameters
    
    Returns:
        Training summary
    
    Example:
        >>> from training_lib import quick_train
        >>> summary = quick_train('resnet18', epochs=20, batch_size=256)
    """
    # Auto-select learning rate if not provided
    if learning_rate is None:
        defaults = get_model_optimizer_defaults(model_name)
        learning_rate = defaults['learning_rate']
    
    # Create model
    if model_name.lower() == 'gpt2':
        model, tokenizer = create_model(model_name)
    else:
        model = create_model(model_name)
        tokenizer = None
    
    # Get input size for data loading
    input_size = get_model_input_size(model_name)
    
    # Create data loader
    if model_name.lower() == 'gpt2':
        conversations = get_conversational_data()
        train_loader = create_conversational_dataloader(
            conversations, tokenizer, batch_size=batch_size
        )
    else:
        train_loader = get_data_loader(
            dataset_name, batch_size=batch_size, 
            input_size=input_size, subset_size=subset_size
        )
    
    # Create trainer
    trainer = UniversalTrainer(
        model=model,
        model_name=model_name,
        dataset_name=dataset_name,
        epochs=epochs,
        batch_size=batch_size,
        learning_rate=learning_rate,
        use_mlflow=use_mlflow,
        tokenizer=tokenizer,
        input_size=input_size,
        **kwargs
    )
    
    # Train
    summary = trainer.train(train_loader)
    
    return summary


# Library info
def info():
    """Print library information."""
    print("=" * 60)
    print("NEURAL RIPPER TRAINING LIBRARY")
    print("=" * 60)
    print(f"Version: {__version__}")
    print(f"Author: {__author__}")
    print()
    print("Supported Models:")
    print("  - ResNet18")
    print("  - EfficientNet-B0") 
    print("  - ViT-Base16")
    print("  - MobileNetV2")
    print("  - GPT-2")
    print()
    print("Supported Datasets:")
    print("  - CIFAR-100")
    print("  - Conversational (for GPT-2)")
    print()
    print("Key Features:")
    print("MLflow integration with AWS Secrets Manager")
    print("Structured logging")
    print("Universal trainer")
    print("Model factories") 
    print("Data utilities")
    print("AWS credentials management")
    print()
    print("Security:")
    print("  MLflow credentials from AWS Secrets Manager")
    print("  Secret name: 'neuralripper'")
    print("  Auto-builds https://username:password@domain/mlflow/")
    print("=" * 60)