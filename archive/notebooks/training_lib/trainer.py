"""
Universal trainer for both image and text models.
Extracted and unified training logic from all notebook implementations.
"""

import torch
import torch.nn as nn
import time
from typing import Dict, Any, Tuple
from .mlflow_monitor import MLflowMonitor
from .utils import set_device, get_optimizer, get_criterion, calculate_eta
from .logger import get_experiment_logger, log_training_progress, log_epoch_summary, log_system_info, log_mlflow_info


class UniversalTrainer:
    """
    Universal trainer that handles both image classification and text generation models.
    """
    
    def __init__(self, model: nn.Module, model_name: str, dataset_name: str,
                 epochs: int = 100, batch_size: int = 128, learning_rate: float = 5e-3,
                 optimizer_name: str = "SGD", use_mlflow: bool = True,
                 tokenizer=None, **kwargs):
        """
        Initialize universal trainer.
        
        Args:
            model: PyTorch model
            model_name: Model name (e.g., 'ResNet18', 'GPT2')
            dataset_name: Dataset name (e.g., 'CIFAR-100', 'Conversational')
            epochs: Number of training epochs
            batch_size: Batch size
            learning_rate: Learning rate
            optimizer_name: Optimizer name ('SGD' or 'AdamW')
            use_mlflow: Whether to enable MLflow tracking
            tokenizer: Tokenizer for text models
            **kwargs: Additional parameters
        """
        self.model = model
        self.model_name = model_name
        self.dataset_name = dataset_name
        self.epochs = epochs
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.optimizer_name = optimizer_name
        self.use_mlflow = use_mlflow
        self.tokenizer = tokenizer
        
        # Set device and move model
        self.device = set_device()
        self.model.to(self.device)
        
        # Create optimizer and criterion
        self.optimizer = get_optimizer(
            self.model.parameters(), 
            optimizer_name, 
            learning_rate, 
            **kwargs
        )
        
        # Set criterion based on model type
        if self.tokenizer is not None:  # Text model
            self.criterion = get_criterion("CrossEntropyLoss", ignore_index=self.tokenizer.pad_token_id)
        else:  # Image model
            self.criterion = get_criterion("CrossEntropyLoss")
        
        # Initialize logger
        self.logger = get_experiment_logger(model_name, dataset_name)
        
        # Initialize MLflow monitor
        if self.use_mlflow:
            self.mlflow_monitor = MLflowMonitor(
                model=self.model,
                optimizer=self.optimizer,
                criterion=self.criterion,
                device=self.device,
                model_name=model_name,
                dataset_name=dataset_name,
                batch_size=batch_size,
                epochs=epochs,
                learning_rate=learning_rate,
                input_size=kwargs.get('input_size', (3, 32, 32)),
                use_pretrained=kwargs.get('use_pretrained', True),
                train_size=kwargs.get('train_size', 50000),
                val_size=kwargs.get('val_size', 10000),
                num_workers=kwargs.get('num_workers', 0)
            )
        else:
            self.mlflow_monitor = None
        
        # Training state
        self.epoch_times = []
        self.best_accuracy = 0.0
        self.best_loss = float('inf')
        self.start_time = None
        
        # Model info
        self.total_params = sum(p.numel() for p in self.model.parameters())
        
        self.logger.experiment_start()
        self.logger.model_created(self.total_params)
        self.logger.device_info(str(self.device))
    
    def train_epoch_image(self, data_loader, epoch_idx: int) -> Tuple[float, float]:
        """
        Train one epoch for image classification models.
        
        Args:
            data_loader: Training data loader
            epoch_idx: Current epoch index
        
        Returns:
            (epoch_loss, epoch_accuracy)
        """
        self.logger.epoch_start(epoch_idx + 1, self.epochs)
        
        self.model.train()
        epoch_total_loss = 0.0
        running_loss = 0.0
        running_correct = 0
        running_total = 0
        batch_count = len(data_loader)
        
        for idx, (images, targets) in enumerate(data_loader):
            images = images.to(self.device)
            targets = targets.to(self.device)
            
            self.optimizer.zero_grad()
            logits = self.model(images)
            loss = self.criterion(logits, targets)
            loss.backward()
            self.optimizer.step()
            
            predictions = logits.argmax(dim=1)
            running_correct += (predictions == targets).sum().item()
            running_total += targets.size(0)
            running_loss += loss.item()
            epoch_total_loss += loss.item()
            
            # Log progress
            if idx % 10 == 9:
                avg_loss = running_loss / 10
                acc_sofar = running_correct / running_total
                log_training_progress(
                    self.logger, epoch_idx + 1, idx, batch_count, 
                    avg_loss, acc_sofar
                )
                running_loss = 0.0
        
        epoch_loss = epoch_total_loss / batch_count
        epoch_acc = running_correct / running_total
        
        self.logger.epoch_complete(epoch_idx + 1, epoch_loss, epoch_acc)
        return epoch_loss, epoch_acc
    
    def train_epoch_text(self, data_loader, epoch_idx: int) -> Tuple[float, float, float, float]:
        """
        Train one epoch for text generation models.
        
        Args:
            data_loader: Training data loader
            epoch_idx: Current epoch index
        
        Returns:
            (epoch_loss, epoch_perplexity, epoch_token_accuracy, epoch_top5_accuracy)
        """
        self.logger.epoch_start(epoch_idx + 1, self.epochs)
        
        self.model.train()
        epoch_total_loss = 0.0
        running_loss = 0.0
        running_correct = 0
        running_top5_correct = 0
        running_total = 0
        batch_count = len(data_loader)
        
        for idx, batch in enumerate(data_loader):
            input_ids = batch['input_ids'].to(self.device)
            attention_mask = batch['attention_mask'].to(self.device)
            labels = batch['labels'].to(self.device)
            
            self.optimizer.zero_grad()
            
            outputs = self.model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels
            )
            loss = outputs.loss
            logits = outputs.logits
            
            loss.backward()
            self.optimizer.step()
            
            # Calculate token-level accuracy
            predictions = logits.argmax(dim=-1)
            mask = (labels != self.tokenizer.pad_token_id)
            correct_predictions = ((predictions == labels) & mask).sum().item()
            total_tokens = mask.sum().item()
            
            # Calculate top-5 accuracy
            top5_preds = torch.topk(logits, 5, dim=-1)[1]
            top5_correct = 0
            for k in range(5):
                top5_correct += ((top5_preds[:, :, k] == labels) & mask).sum().item()
            
            running_correct += correct_predictions
            running_top5_correct += top5_correct
            running_total += total_tokens
            running_loss += loss.item()
            epoch_total_loss += loss.item()
            
            # Log progress
            if idx % 10 == 9:
                avg_loss = running_loss / 10
                perplexity = torch.exp(torch.tensor(avg_loss)).item()
                token_accuracy = running_correct / running_total if running_total > 0 else 0
                top5_accuracy = running_top5_correct / running_total if running_total > 0 else 0
                
                self.logger.info(f"Epoch {epoch_idx + 1} | Batch {idx + 1} | "
                               f"Loss: {avg_loss:.4f} | Perplexity: {perplexity:.2f} | "
                               f"Token Acc: {token_accuracy:.4f} | Top5 Acc: {top5_accuracy:.4f}")
                running_loss = 0.0
        
        epoch_loss = epoch_total_loss / batch_count
        epoch_perplexity = torch.exp(torch.tensor(epoch_loss)).item()
        epoch_token_accuracy = running_correct / running_total if running_total > 0 else 0
        epoch_top5_accuracy = running_top5_correct / running_total if running_total > 0 else 0
        
        self.logger.info(f"Epoch {epoch_idx + 1} completed - Loss: {epoch_loss:.4f}, "
                        f"Perplexity: {epoch_perplexity:.2f}, Token Accuracy: {epoch_token_accuracy:.4f}, "
                        f"Top5 Accuracy: {epoch_top5_accuracy:.4f}")
        
        return epoch_loss, epoch_perplexity, epoch_token_accuracy, epoch_top5_accuracy
    
    def train(self, train_loader) -> Dict[str, Any]:
        """
        Main training loop that handles both image and text models.
        
        Args:
            train_loader: Training data loader
        
        Returns:
            Training summary dictionary
        """
        # Initialize MLflow if enabled
        if self.mlflow_monitor:
            self.mlflow_monitor.initialize()
            log_mlflow_info(
                self.logger, 
                self.mlflow_monitor.mlflow_uri, 
                f"{self.model_name}-{self.dataset_name}",
                self.use_mlflow
            )
        
        # Log system info
        log_system_info(
            self.logger, str(self.device), self.total_params,
            self.batch_size, self.learning_rate
        )
        
        self.logger.training_start(self.model_name, self.epochs)
        self.start_time = time.time()
        
        try:
            for epoch in range(self.epochs):
                epoch_start = time.time()
                
                # Train epoch based on model type
                if self.tokenizer is not None:  # Text model
                    epoch_loss, epoch_perplexity, epoch_token_accuracy, epoch_top5_accuracy = \
                        self.train_epoch_text(train_loader, epoch)
                    
                    primary_metric = epoch_token_accuracy
                    
                    # Log to MLflow
                    if self.mlflow_monitor:
                        self.mlflow_monitor.add_epoch_time(time.time() - epoch_start)
                        metrics = self.mlflow_monitor.log_epoch_metrics(
                            epoch, epoch_loss, 
                            epoch_token_accuracy=epoch_token_accuracy,
                            epoch_perplexity=epoch_perplexity,
                            epoch_top5_accuracy=epoch_top5_accuracy,
                            batch_count=len(train_loader)
                        )
                    
                else:  # Image model
                    epoch_loss, epoch_acc = self.train_epoch_image(train_loader, epoch)
                    
                    primary_metric = epoch_acc
                    
                    # Log to MLflow
                    if self.mlflow_monitor:
                        self.mlflow_monitor.add_epoch_time(time.time() - epoch_start)
                        metrics = self.mlflow_monitor.log_epoch_metrics(
                            epoch, epoch_loss, epoch_acc=epoch_acc,
                            batch_count=len(train_loader)
                        )
                
                # Track timing
                epoch_time = time.time() - epoch_start
                self.epoch_times.append(epoch_time)
                
                # Update best metrics
                if primary_metric > self.best_accuracy:
                    self.best_accuracy = primary_metric
                    self.logger.model_checkpoint(primary_metric)
                
                if epoch_loss < self.best_loss:
                    self.best_loss = epoch_loss
                
                # Calculate ETA
                eta = calculate_eta(self.epoch_times, epoch, self.epochs)
                
                # Log epoch summary
                log_epoch_summary(
                    self.logger, epoch, self.epochs, epoch_loss, 
                    primary_metric, epoch_time, eta, self.learning_rate
                )
                
                # Enhanced progress display
                if self.tokenizer is not None:  # Text model
                    print(f"Epoch {epoch+1}/{self.epochs}: "
                          f"Loss: {epoch_loss:.4f} | Perplexity: {epoch_perplexity:.2f} | "
                          f"Token Acc: {epoch_token_accuracy:.4f} | Top5 Acc: {epoch_top5_accuracy:.4f} | "
                          f"Time: {epoch_time:.1f}s | ETA: {eta/60:.1f}min")
                else:  # Image model
                    print(f"Epoch {epoch+1}/{self.epochs}: "
                          f"Loss: {epoch_loss:.4f} | Acc: {epoch_acc:.4f} | "
                          f"Time: {epoch_time:.1f}s | ETA: {eta/60:.1f}min")
        
        except KeyboardInterrupt:
            self.logger.warning("Training interrupted by user")
            return self._end_training("KILLED")
        except Exception as e:
            self.logger.error(f"Training failed with error: {e}")
            return self._end_training("FAILED")
        
        # Training completed successfully
        return self._end_training("FINISHED")
    
    def _end_training(self, status: str) -> Dict[str, Any]:
        """End training and return summary."""
        total_time = time.time() - self.start_time if self.start_time else 0
        
        # Create summary
        summary = {
            "status": status,
            "total_time_minutes": round(total_time / 60, 2),
            "best_accuracy": self.best_accuracy,
            "best_loss": self.best_loss,
            "epochs_completed": len(self.epoch_times),
            "model_name": self.model_name,
            "dataset_name": self.dataset_name
        }
        
        # End MLflow run
        if self.mlflow_monitor:
            mlflow_summary = self.mlflow_monitor.end_run(status)
            summary.update(mlflow_summary)
        
        # Log final summary
        if status == "FINISHED":
            self.logger.training_complete()
        
        from .logger import log_training_summary
        log_training_summary(
            self.logger, 
            summary["total_time_minutes"], 
            summary["best_accuracy"], 
            summary["epochs_completed"]
        )
        
        return summary
    
    def save_model(self, filepath: str):
        """Save model checkpoint."""
        try:
            torch.save({
                'model_state_dict': self.model.state_dict(),
                'optimizer_state_dict': self.optimizer.state_dict(),
                'best_accuracy': self.best_accuracy,
                'best_loss': self.best_loss,
                'epochs_completed': len(self.epoch_times)
            }, filepath)
            self.logger.info(f"Model saved to {filepath}")
        except Exception as e:
            self.logger.error(f"Failed to save model: {e}")
    
    def load_model(self, filepath: str):
        """Load model checkpoint."""
        try:
            checkpoint = torch.load(filepath, map_location=self.device)
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
            self.best_accuracy = checkpoint.get('best_accuracy', 0.0)
            self.best_loss = checkpoint.get('best_loss', float('inf'))
            self.logger.info(f"Model loaded from {filepath}")
        except Exception as e:
            self.logger.error(f"Failed to load model: {e}")