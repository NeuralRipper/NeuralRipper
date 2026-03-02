"""
Dataset and DataLoader utilities.
Extracted from all notebook implementations for consistent data handling.
"""

import torch
from torch.utils.data import DataLoader, Subset
from torchvision import datasets, transforms
from datasets import load_dataset
import numpy as np
from typing import Optional, Tuple, Dict, Any


def get_cifar100_transforms(input_size: Tuple[int, int, int] = (3, 32, 32)) -> transforms.Compose:
    """
    Get CIFAR-100 transforms based on input size requirements.
    
    Args:
        input_size: (channels, height, width) - determines if resizing needed
    
    Returns:
        Composed transforms
    """
    _, height, width = input_size
    
    transform_list = []
    
    # Resize if needed (for models like ViT, EfficientNet that need 224x224)
    if height != 32 or width != 32:
        transform_list.extend([
            transforms.Resize((height, width)),
            transforms.RandomHorizontalFlip(),
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1),
        ])
        if height == 224:  # For ViT specifically
            transform_list.append(transforms.RandomResizedCrop(224, scale=(0.8, 1.0)))
    else:
        # Standard CIFAR-100 augmentation
        transform_list.extend([
            transforms.RandomCrop(32, padding=4),
            transforms.RandomHorizontalFlip(0.5),
        ])
    
    # Common transforms
    transform_list.extend([
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
    ])
    
    return transforms.Compose(transform_list)


def get_cifar100_dataset(root: str = "./data", train: bool = True, 
                        input_size: Tuple[int, int, int] = (3, 32, 32),
                        download: bool = True, subset_size: Optional[int] = None):
    """
    Get CIFAR-100 dataset with appropriate transforms.
    
    Args:
        root: Data root directory 
        train: Whether to load training set
        input_size: Required input size for transforms
        download: Whether to download if not exists
        subset_size: Optional subset size for faster training
    
    Returns:
        Dataset (potentially subset)
    """
    transform = get_cifar100_transforms(input_size)
    
    dataset = datasets.CIFAR100(
        root=root,
        train=train,
        download=download,
        transform=transform
    )
    
    if subset_size is not None and subset_size < len(dataset):
        indices = np.random.choice(len(dataset), subset_size, replace=False)
        dataset = Subset(dataset, indices)
    
    return dataset


def get_conversational_data(dataset_name: str = "blended_skill_talk", 
                          max_conversations: int = 1000) -> list:
    """
    Load and prepare conversational dataset for GPT-2 training.
    
    Args:
        dataset_name: Dataset name to load
        max_conversations: Maximum number of conversations to extract
    
    Returns:
        List of formatted conversation strings
    """
    try:
        dataset = load_dataset(dataset_name)
        conversations = []
        
        for item in dataset["train"]:
            # Extract guided and free messages
            guided_messages = item.get("guided_messages", [])
            free_messages = item.get("free_messages", [])
            
            # Process guided messages
            if guided_messages and len(guided_messages) >= 2:
                for i in range(0, len(guided_messages) - 1, 2):
                    if i + 1 < len(guided_messages):
                        user_msg = guided_messages[i].strip()
                        assistant_msg = guided_messages[i + 1].strip()
                        if user_msg and assistant_msg:
                            conversation = f"User: {user_msg}\nAssistant: {assistant_msg}<|endoftext|>"
                            conversations.append(conversation)
            
            # Process free messages
            if free_messages and len(free_messages) >= 2:
                for i in range(0, len(free_messages) - 1, 2):
                    if i + 1 < len(free_messages):
                        user_msg = free_messages[i].strip()
                        assistant_msg = free_messages[i + 1].strip()
                        if user_msg and assistant_msg:
                            conversation = f"User: {user_msg}\nAssistant: {assistant_msg}<|endoftext|>"
                            conversations.append(conversation)
            
            if len(conversations) >= max_conversations:
                break
        
        conversations = conversations[:max_conversations]
        return conversations
        
    except Exception as e:
        print(f"Error loading {dataset_name}: {e}")
        return []


def create_conversational_dataloader(conversations: list, tokenizer, 
                                   batch_size: int = 16, max_length: int = 512,
                                   shuffle: bool = True, num_workers: int = 0):
    """
    Create DataLoader for conversational data with tokenization.
    
    Args:
        conversations: List of conversation strings
        tokenizer: Tokenizer (e.g., GPT2Tokenizer)
        batch_size: Batch size
        max_length: Maximum sequence length
        shuffle: Whether to shuffle data
        num_workers: Number of worker processes
    
    Returns:
        DataLoader
    """
    def collate_fn(batch):
        # Tokenize all conversations in batch
        encoded = tokenizer(
            batch,
            truncation=True,
            padding=True,
            max_length=max_length,
            return_tensors='pt'
        )
        
        # For GPT-2, input_ids serve as both input and labels
        input_ids = encoded['input_ids']
        attention_mask = encoded['attention_mask']
        
        return {
            'input_ids': input_ids,
            'attention_mask': attention_mask,
            'labels': input_ids.clone()
        }
    
    return DataLoader(
        conversations,
        batch_size=batch_size,
        shuffle=shuffle,
        collate_fn=collate_fn,
        num_workers=num_workers
    )


def get_data_loader(dataset_type: str, batch_size: int = 128, 
                   shuffle: bool = True, num_workers: int = 0,
                   input_size: Tuple[int, int, int] = (3, 32, 32),
                   subset_size: Optional[int] = None, 
                   pin_memory: bool = False, **kwargs) -> DataLoader:
    """
    Universal data loader factory for different dataset types.
    
    Args:
        dataset_type: 'cifar100' currently supported
        batch_size: Batch size
        shuffle: Whether to shuffle
        num_workers: Number of workers (0 for MPS compatibility)
        input_size: Input size requirement
        subset_size: Optional subset size
        pin_memory: Whether to pin memory (False for MPS)
        **kwargs: Additional dataset arguments
    
    Returns:
        DataLoader
    """
    if dataset_type.lower() == "cifar100":
        dataset = get_cifar100_dataset(
            input_size=input_size,
            subset_size=subset_size,
            **kwargs
        )
        
        return DataLoader(
            dataset,
            batch_size=batch_size,
            shuffle=shuffle,
            num_workers=num_workers,
            pin_memory=pin_memory
        )
    else:
        raise ValueError(f"Unsupported dataset type: {dataset_type}")


def visualize_samples(dataset, num_samples: int = 16):
    """
    Visualize a sample of images from the dataset.
    
    Args:
        dataset: Dataset to visualize
        num_samples: Number of samples to show
    """
    import matplotlib.pyplot as plt
    
    # Handle both regular dataset and Subset
    dataset_len = len(dataset.dataset) if hasattr(dataset, 'dataset') else len(dataset)
    sample_indices = np.random.choice(dataset_len, num_samples, replace=False)
    
    fig, axes = plt.subplots(4, 4, figsize=(12, 12))
    axes = axes.ravel()
    
    for i, idx in enumerate(sample_indices):
        img_tensor, class_idx = dataset[idx]
        
        # Denormalize image for display
        img = img_tensor.permute(1, 2, 0)
        img = img * torch.tensor([0.229, 0.224, 0.225]) + torch.tensor([0.485, 0.456, 0.406])
        img = torch.clamp(img, 0, 1)
        
        axes[i].imshow(img)
        
        # Get class name
        if hasattr(dataset, 'classes'):
            class_name = dataset.classes[class_idx]
        elif hasattr(dataset, 'dataset') and hasattr(dataset.dataset, 'classes'):
            class_name = dataset.dataset.classes[class_idx]
        else:
            class_name = f"Class {class_idx}"
            
        axes[i].set_title(f"Class: {class_name}")
        axes[i].axis('off')
    
    plt.tight_layout()
    plt.show()


def get_dataset_info(dataset) -> Dict[str, Any]:
    """
    Get comprehensive dataset information.
    
    Args:
        dataset: Dataset to analyze
    
    Returns:
        Dictionary with dataset information
    """
    info = {
        "size": len(dataset),
        "type": type(dataset).__name__
    }
    
    # Handle Subset
    if hasattr(dataset, 'dataset'):
        original_dataset = dataset.dataset
        info["original_size"] = len(original_dataset)
        info["subset_indices"] = len(dataset.indices) if hasattr(dataset, 'indices') else None
        
        # Get classes from original dataset
        if hasattr(original_dataset, 'classes'):
            info["num_classes"] = len(original_dataset.classes)
            info["class_names"] = original_dataset.classes[:10]  # First 10 classes
    else:
        # Regular dataset
        if hasattr(dataset, 'classes'):
            info["num_classes"] = len(dataset.classes)
            info["class_names"] = dataset.classes[:10]  # First 10 classes
    
    return info