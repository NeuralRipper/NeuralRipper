"""
Model factory for creating different architectures.
Extracted from all notebook implementations.
"""

import torch
import torch.nn as nn
from torchvision.models import (
    resnet18, ResNet18_Weights,
    efficientnet_b0, EfficientNet_B0_Weights,
    vit_b_16, ViT_B_16_Weights,
    MobileNet_V2_Weights
)
import torchvision
from transformers import GPT2LMHeadModel, GPT2Tokenizer
from typing import Tuple, Optional, Dict, Any


def create_resnet18(num_classes: int = 100, pretrained: bool = True) -> nn.Module:
    """
    Create ResNet18 model adapted for classification.
    
    Args:
        num_classes: Number of output classes
        pretrained: Whether to use pretrained weights
    
    Returns:
        ResNet18 model
    """
    if pretrained:
        model = resnet18(weights=ResNet18_Weights.DEFAULT)
    else:
        model = resnet18(weights=None)
    
    # Adapt final layer for num_classes
    model.fc = nn.Linear(model.fc.in_features, num_classes)
    
    return model


def create_efficientnet_b0(num_classes: int = 100, pretrained: bool = True) -> nn.Module:
    """
    Create EfficientNet-B0 model adapted for classification.
    
    Args:
        num_classes: Number of output classes
        pretrained: Whether to use pretrained weights
    
    Returns:
        EfficientNet-B0 model
    """
    if pretrained:
        model = efficientnet_b0(weights=EfficientNet_B0_Weights.DEFAULT)
    else:
        model = efficientnet_b0(weights=None)
    
    # Adapt classifier for num_classes
    num_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(num_features, num_classes)
    
    return model


def create_vit_base16(num_classes: int = 100, pretrained: bool = True) -> nn.Module:
    """
    Create Vision Transformer Base16 model adapted for classification.
    
    Args:
        num_classes: Number of output classes
        pretrained: Whether to use pretrained weights
    
    Returns:
        ViT-Base16 model
    """
    if pretrained:
        model = vit_b_16(weights=ViT_B_16_Weights.DEFAULT)
    else:
        model = vit_b_16(weights=None)
    
    # Adapt head for num_classes
    num_features = model.heads.head.in_features
    model.heads.head = nn.Linear(num_features, num_classes)
    
    return model


def create_mobilenet_v2(num_classes: int = 100, pretrained: bool = True) -> nn.Module:
    """
    Create MobileNetV2 model adapted for classification.
    
    Args:
        num_classes: Number of output classes  
        pretrained: Whether to use pretrained weights
    
    Returns:
        MobileNetV2 model
    """
    if pretrained:
        model = torchvision.models.mobilenet_v2(weights=MobileNet_V2_Weights.DEFAULT)
    else:
        model = torchvision.models.mobilenet_v2(weights=None)
    
    # Adapt classifier for num_classes
    model.classifier[1] = nn.Linear(1280, num_classes)
    
    return model


def create_gpt2(model_name: str = 'gpt2', pretrained: bool = True) -> Tuple[nn.Module, Any]:
    """
    Create GPT-2 model and tokenizer for language modeling.
    
    Args:
        model_name: GPT-2 variant ('gpt2', 'gpt2-medium', etc.)
        pretrained: Whether to use pretrained weights
    
    Returns:
        Tuple of (model, tokenizer)
    """
    if pretrained:
        model = GPT2LMHeadModel.from_pretrained(model_name)
        tokenizer = GPT2Tokenizer.from_pretrained(model_name)
    else:
        from transformers import GPT2Config
        config = GPT2Config()
        model = GPT2LMHeadModel(config)
        tokenizer = GPT2Tokenizer.from_pretrained('gpt2')  # Always use pretrained tokenizer
    
    # GPT-2 doesn't have a pad token
    tokenizer.pad_token = tokenizer.eos_token
    
    return model, tokenizer


def get_model_input_size(model_name: str) -> Tuple[int, int, int]:
    """
    Get the required input size for different models.
    
    Args:
        model_name: Model name
    
    Returns:
        (channels, height, width)
    """
    input_sizes = {
        'resnet18': (3, 32, 32),
        'mobilenet_v2': (3, 32, 32), 
        'efficientnet_b0': (3, 224, 224),
        'vit_base16': (3, 224, 224),
        'gpt2': 'variable'  # Text model
    }
    
    return input_sizes.get(model_name.lower(), (3, 32, 32))


def get_model_optimizer_defaults(model_name: str) -> Dict[str, Any]:
    """
    Get default optimizer settings for different models based on notebook implementations.
    
    Args:
        model_name: Model name
    
    Returns:
        Dictionary with optimizer defaults
    """
    defaults = {
        'resnet18': {
            'optimizer': 'SGD',
            'learning_rate': 5e-3,
            'momentum': 0.9,
            'weight_decay': 4e-5
        },
        'efficientnet_b0': {
            'optimizer': 'SGD', 
            'learning_rate': 3e-3,
            'momentum': 0.9,
            'weight_decay': 4e-5
        },
        'vit_base16': {
            'optimizer': 'SGD',
            'learning_rate': 5e-3, 
            'momentum': 0.9,
            'weight_decay': 4e-5
        },
        'mobilenet_v2': {
            'optimizer': 'SGD',
            'learning_rate': 3e-3,
            'momentum': 0.9,
            'weight_decay': 4e-5
        },
        'gpt2': {
            'optimizer': 'AdamW',
            'learning_rate': 5e-5,
            'weight_decay': 0.01
        }
    }
    
    return defaults.get(model_name.lower(), defaults['resnet18'])


def create_model(model_name: str, num_classes: int = 100, 
                pretrained: bool = True, **kwargs) -> nn.Module:
    """
    Universal model factory.
    
    Args:
        model_name: Model architecture name
        num_classes: Number of classes (ignored for text models)
        pretrained: Whether to use pretrained weights
        **kwargs: Additional model arguments
    
    Returns:
        Model instance (and tokenizer for text models)
    """
    model_name = model_name.lower()
    
    if model_name == 'resnet18':
        return create_resnet18(num_classes, pretrained)
    elif model_name == 'efficientnet_b0' or model_name == 'efficientnet-b0':
        return create_efficientnet_b0(num_classes, pretrained)
    elif model_name == 'vit_base16' or model_name == 'vit-base16':
        return create_vit_base16(num_classes, pretrained)
    elif model_name == 'mobilenet_v2' or model_name == 'mobilenetv2':
        return create_mobilenet_v2(num_classes, pretrained)
    elif model_name == 'gpt2':
        return create_gpt2(kwargs.get('model_variant', 'gpt2'), pretrained)
    else:
        raise ValueError(f"Unsupported model: {model_name}")


def get_model_info(model: nn.Module, model_name: str) -> Dict[str, Any]:
    """
    Get comprehensive model information.
    
    Args:
        model: Model instance
        model_name: Model name
    
    Returns:
        Dictionary with model information
    """
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    
    # Model size calculation
    param_size = sum(p.numel() * p.element_size() for p in model.parameters())
    buffer_size = sum(b.numel() * b.element_size() for b in model.buffers())
    model_size_mb = (param_size + buffer_size) / (1024 ** 2)
    
    info = {
        "model_name": model_name,
        "architecture": model.__class__.__name__,
        "total_parameters": total_params,
        "trainable_parameters": trainable_params,
        "parameters_millions": round(total_params / 1e6, 2),
        "model_size_mb": round(model_size_mb, 2),
        "input_size": get_model_input_size(model_name),
        "optimizer_defaults": get_model_optimizer_defaults(model_name)
    }
    
    # Add model-specific info
    if hasattr(model, 'config') and model_name == 'gpt2':
        info.update({
            "vocab_size": model.config.vocab_size,
            "n_positions": model.config.n_positions,
            "n_ctx": model.config.n_ctx,
            "n_embd": model.config.n_embd,
            "n_layer": model.config.n_layer,
            "n_head": model.config.n_head,
        })
    
    return info


def print_model_summary(model: nn.Module, model_name: str):
    """
    Print a comprehensive model summary.
    
    Args:
        model: Model instance
        model_name: Model name
    """
    info = get_model_info(model, model_name)
    
    print("=" * 60)
    print(f"MODEL SUMMARY: {info['model_name'].upper()}")
    print("=" * 60)
    print(f"Architecture: {info['architecture']}")
    print(f"Total Parameters: {info['total_parameters']:,}")
    print(f"Trainable Parameters: {info['trainable_parameters']:,}")
    print(f"Parameters (M): {info['parameters_millions']}")
    print(f"Model Size: {info['model_size_mb']:.2f} MB")
    print(f"Input Size: {info['input_size']}")
    
    # Print optimizer defaults
    defaults = info['optimizer_defaults']
    print(f"Default Optimizer: {defaults['optimizer']}")
    print(f"Default LR: {defaults['learning_rate']}")
    
    # Model-specific info for GPT-2
    if 'vocab_size' in info:
        print(f"Vocabulary Size: {info['vocab_size']:,}")
        print(f"Context Length: {info['n_ctx']}")
        print(f"Embedding Dim: {info['n_embd']}")
        print(f"Layers: {info['n_layer']}")
        print(f"Attention Heads: {info['n_head']}")
    
    print("=" * 60)