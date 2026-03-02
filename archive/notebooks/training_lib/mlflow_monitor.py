"""
MLflow monitoring and tracking utilities.
Comprehensive metrics and parameter logging extracted from all notebook implementations.
"""

import mlflow
import mlflow.pytorch
from mlflow.models import infer_signature
import torch
import numpy as np
import time
from datetime import datetime
from typing import Optional, Dict, Any, List
from .utils import get_system_info, get_environment_info, get_gpu_metrics, get_system_metrics
from .aws_utils import build_mlflow_uri


class MLflowMonitor:
    """
    Comprehensive MLflow monitoring with all metrics and parameters from notebooks.
    """
    
    def __init__(self, model, optimizer, criterion, device, 
                 model_name: str, dataset_name: str,
                 mlflow_uri: str = None, **kwargs):
        """
        Initialize MLflow monitor with comprehensive parameter tracking.
        
        Args:
            model: PyTorch model
            optimizer: Optimizer instance
            criterion: Loss criterion
            device: Training device
            model_name: Model name (e.g., 'ResNet18')
            dataset_name: Dataset name (e.g., 'CIFAR-100')
            mlflow_uri: MLflow tracking URI
            **kwargs: Additional parameters to track
        """
        self.model = model
        self.optimizer = optimizer
        self.criterion = criterion
        self.device = device
        self.model_name = model_name
        self.dataset_name = dataset_name
        
        # Build MLflow URI with credentials from AWS Secrets Manager
        if mlflow_uri:
            self.mlflow_uri = mlflow_uri
        else:
            self.mlflow_uri = build_mlflow_uri()
        
        # Extract training parameters
        self.batch_size = kwargs.get('batch_size', 128)
        self.epochs = kwargs.get('epochs', 100)
        self.learning_rate = kwargs.get('learning_rate', 5e-3)
        self.input_size = kwargs.get('input_size', (3, 32, 32))
        self.use_pretrained = kwargs.get('use_pretrained', True)
        self.train_size = kwargs.get('train_size', 50000)
        self.val_size = kwargs.get('val_size', 10000)
        self.num_workers = kwargs.get('num_workers', 0)
        
        # Tracking state
        self.run_started = False
        self.run_id = None
        self.start_time = None
        self.best_metric = float('-inf')  # For accuracy (higher is better)
        self.best_loss = float('inf')     # For loss (lower is better)
        self.prev_loss = None
        self.epoch_times = []
        
        # Registry URI for model registration
        self.registry_uri = self.mlflow_uri
    
    def initialize(self) -> bool:
        """
        Initialize MLflow tracking with comprehensive parameter logging.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if self.run_started:
            return True
            
        try:
            # End any existing run
            if mlflow.active_run():
                mlflow.end_run()
            
            # Configure MLflow
            print(f"Connecting to MLflow...")
            mlflow.set_tracking_uri(self.mlflow_uri)
            mlflow.set_registry_uri(self.mlflow_uri)
            mlflow.set_experiment(f"{self.model_name}-{self.dataset_name}")
            
            # Start run with timestamp
            run_name = f"{self.model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            mlflow.start_run(run_name=run_name)
            self.run_started = True
            self.run_id = mlflow.active_run().info.run_id
            self.start_time = time.time()
            
            # Log all comprehensive parameters
            all_params = {
                **self._get_core_params(),
                **self._get_model_params(),
                **self._get_system_params(),
                **self._get_environment_params(),
                **self._get_data_params(),
                **self._get_training_params()
            }
            
            mlflow.log_params(all_params)
            
            print(f"MLflow tracking initialized: {run_name}")
            return True
            
        except Exception as e:
            print(f"MLflow initialization failed: {e}")
            self.run_started = False
            return False
    
    def _get_core_params(self) -> Dict[str, Any]:
        """Core training parameters."""
        return {
            "model_name": self.model_name,
            "dataset_name": self.dataset_name,
            "batch_size": self.batch_size,
            "learning_rate": self.learning_rate,
            "epochs": self.epochs,
            "optimizer": self.optimizer.__class__.__name__,
            "criterion": self.criterion.__class__.__name__,
            "device": str(self.device),
            "use_pretrained": self.use_pretrained,
            "model_type": "classification" if self.dataset_name != "Conversational" else "language_modeling"
        }
    
    def _get_model_params(self) -> Dict[str, Any]:
        """Model architecture and hyperparameters."""
        total_params = sum(p.numel() for p in self.model.parameters())
        trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        
        # Model size calculation
        param_size = sum(p.numel() * p.element_size() for p in self.model.parameters())
        buffer_size = sum(b.numel() * b.element_size() for b in self.model.buffers())
        model_size_mb = (param_size + buffer_size) / (1024 ** 2)
        
        params = {
            "total_parameters": total_params,
            "trainable_parameters": trainable_params,
            "parameters_millions": round(total_params / 1e6, 2),
            "model_size_mb": round(model_size_mb, 2),
            "model_architecture": self.model.__class__.__name__,
            "input_channels": self.input_size[0] if isinstance(self.input_size, tuple) else None,
            "input_height": self.input_size[1] if isinstance(self.input_size, tuple) else None,
            "input_width": self.input_size[2] if isinstance(self.input_size, tuple) else None,
        }
        
        # Add optimizer-specific parameters
        if hasattr(self.optimizer, 'param_groups'):
            first_group = self.optimizer.param_groups[0]
            params.update({
                "weight_decay": first_group.get('weight_decay', 0),
                "momentum": first_group.get('momentum', 0),
            })
        
        # Add model-specific parameters (GPT-2)
        if hasattr(self.model, 'config'):
            config = self.model.config
            params.update({
                "vocab_size": getattr(config, 'vocab_size', None),
                "n_positions": getattr(config, 'n_positions', None),
                "n_ctx": getattr(config, 'n_ctx', None),
                "n_embd": getattr(config, 'n_embd', None),
                "n_layer": getattr(config, 'n_layer', None),
                "n_head": getattr(config, 'n_head', None),
            })
        
        return params
    
    def _get_system_params(self) -> Dict[str, Any]:
        """System hardware and software parameters."""
        return get_system_info()
    
    def _get_environment_params(self) -> Dict[str, Any]:
        """Environment and reproducibility parameters."""
        return get_environment_info()
    
    def _get_data_params(self) -> Dict[str, Any]:
        """Data pipeline parameters."""
        return {
            "train_size": self.train_size,
            "val_size": self.val_size,
            "total_samples": self.train_size + self.val_size,
            "num_workers": self.num_workers,
        }
    
    def _get_training_params(self) -> Dict[str, Any]:
        """Advanced training configuration."""
        return {
            "mlflow_uri": self.mlflow_uri,
            "experiment_name": f"{self.model_name}-{self.dataset_name}",
        }
    
    def log_epoch_metrics(self, epoch: int, epoch_loss: float, 
                         epoch_acc: Optional[float] = None,
                         epoch_perplexity: Optional[float] = None,
                         epoch_token_accuracy: Optional[float] = None,
                         epoch_top5_accuracy: Optional[float] = None,
                         batch_count: Optional[int] = None) -> Dict[str, Any]:
        """
        Log comprehensive epoch metrics for both image and text models.
        
        Args:
            epoch: Current epoch
            epoch_loss: Epoch loss
            epoch_acc: Epoch accuracy (for image models)
            epoch_perplexity: Perplexity (for text models)
            epoch_token_accuracy: Token-level accuracy (for text models)
            epoch_top5_accuracy: Top-5 accuracy (for text models)
            batch_count: Number of batches processed
        
        Returns:
            Dictionary of logged metrics
        """
        if not self.run_started:
            return {}
        
        try:
            current_time = time.time()
            
            # Calculate timing
            epoch_time = self.epoch_times[-1] if self.epoch_times else 0
            total_time = current_time - self.start_time if self.start_time else 0
            
            # Core metrics - using standardized names for frontend compatibility
            metrics = {
                "epoch": epoch,
                "train_loss": epoch_loss,
                "learning_rate": self.optimizer.param_groups[0]["lr"],
                "epoch_time_seconds": epoch_time,
                "total_time_seconds": total_time,
                "total_time_minutes": total_time / 60,
            }
            
            # Add accuracy metrics based on model type
            if epoch_acc is not None:
                metrics["train_accuracy"] = epoch_acc
            if epoch_token_accuracy is not None:
                metrics["train_accuracy"] = epoch_token_accuracy  # Frontend expects 'train_accuracy'
            if epoch_perplexity is not None:
                metrics["perplexity"] = epoch_perplexity
            if epoch_top5_accuracy is not None:
                metrics["top5_accuracy"] = epoch_top5_accuracy
            
            # Training dynamics
            if self.prev_loss is not None:
                loss_improvement = self.prev_loss - epoch_loss
                metrics.update({
                    "loss_improvement": loss_improvement,
                    "loss_improvement_percent": (loss_improvement / self.prev_loss) * 100 if self.prev_loss != 0 else 0,
                })
            self.prev_loss = epoch_loss
            
            # Performance metrics
            if batch_count and epoch_time > 0:
                samples_per_sec = (self.batch_size * batch_count) / epoch_time
                metrics.update({
                    "batches_per_second": batch_count / epoch_time,
                    "samples_per_second": samples_per_sec,
                })
            
            # Running statistics
            if self.epoch_times:
                metrics.update({
                    "average_epoch_time": np.mean(self.epoch_times),
                    "min_epoch_time": min(self.epoch_times),
                    "max_epoch_time": max(self.epoch_times),
                })
            
            # System metrics
            gpu_metrics = get_gpu_metrics()
            system_metrics = get_system_metrics()
            metrics.update(gpu_metrics)
            metrics.update(system_metrics)
            
            # Log to MLflow
            mlflow.log_metrics(metrics, step=epoch)
            
            # Update best metrics
            current_metric = epoch_acc if epoch_acc is not None else epoch_token_accuracy
            if current_metric is not None and current_metric > self.best_metric:
                self.best_metric = current_metric
                self._log_best_model_checkpoint(epoch, current_metric)
            
            if epoch_loss < self.best_loss:
                self.best_loss = epoch_loss
            
            return metrics
            
        except Exception as e:
            print(f"Failed to log epoch metrics: {e}")
            return {}
    
    def _log_best_model_checkpoint(self, epoch: int, metric_value: float):
        """Log best model checkpoint with metadata."""
        try:
            # Create sample input for signature inference
            if isinstance(self.input_size, tuple):
                sample_input = torch.randn(1, *self.input_size)
            else:
                # For text models, create dummy input
                sample_input = torch.randint(0, 1000, (1, 512))
            
            sample_input_np = sample_input.numpy()
            
            # Get model prediction
            was_training = self.model.training
            self.model.eval()
            
            with torch.no_grad():
                if hasattr(self.model, 'forward'):
                    sample_output = self.model(sample_input.to(self.device))
                    if hasattr(sample_output, 'logits'):
                        sample_output = sample_output.logits
                    sample_output_np = sample_output.cpu().numpy()
                else:
                    sample_output_np = np.random.randn(1, 100)  # Fallback
            
            if was_training:
                self.model.train()
            
            # Infer signature
            signature = infer_signature(sample_input_np, sample_output_np)
            
            # Log model
            mlflow.pytorch.log_model(
                self.model,
                artifact_path="model",
                registered_model_name=f"{self.model_name}-{self.dataset_name}",
                signature=signature,
                pip_requirements=self._get_pip_requirements()
            )
            
            # Log checkpoint metrics
            checkpoint_metrics = {
                "best_epoch_checkpoint": epoch,
                "best_accuracy_checkpoint": metric_value,
                "best_loss_checkpoint": self.best_loss,
            }
            mlflow.log_metrics(checkpoint_metrics, step=epoch)
            
            # Add checkpoint timestamp tag
            mlflow.set_tag("last_checkpoint_time", datetime.now().isoformat())
            
        except Exception as e:
            print(f"Failed to log model checkpoint: {e}")
    
    def _get_pip_requirements(self) -> List[str]:
        """Get pip requirements for model."""
        base_requirements = ["torch", "numpy"]
        
        if "gpt" in self.model_name.lower():
            base_requirements.extend(["transformers", "datasets"])
        else:
            base_requirements.extend(["torchvision", "pillow"])
        
        return base_requirements
    
    def add_epoch_time(self, epoch_time: float):
        """Add epoch time for tracking."""
        self.epoch_times.append(epoch_time)
    
    def should_log_checkpoint(self, current_metric: float, metric_type: str = "accuracy") -> bool:
        """
        Determine if current model should be checkpointed.
        
        Args:
            current_metric: Current metric value
            metric_type: 'accuracy' (higher better) or 'loss' (lower better)
        
        Returns:
            bool: Whether to log checkpoint
        """
        if metric_type == "accuracy":
            return current_metric > self.best_metric
        elif metric_type == "loss":
            return current_metric < self.best_loss
        return False
    
    def end_run(self, status: str = "FINISHED") -> Dict[str, Any]:
        """
        End MLflow run with final summary.
        
        Args:
            status: Run status
        
        Returns:
            Training summary dictionary
        """
        if not self.run_started:
            return {}
        
        try:
            total_time = time.time() - self.start_time if self.start_time else 0
            
            # Final summary parameters
            summary = {
                "training_status": status,
                "final_total_training_time_minutes": round(total_time / 60, 2),
                "final_best_accuracy": float(self.best_metric) if self.best_metric != float('-inf') else 0,
                "final_best_loss": float(self.best_loss) if self.best_loss != float('inf') else 0,
                "final_epochs_completed": len(self.epoch_times),
            }
            
            # Log final summary
            mlflow.log_params(summary)
            
            # End the run
            mlflow.end_run(status=status)
            self.run_started = False
            
            return summary
            
        except Exception as e:
            print(f"Failed to end MLflow run: {e}")
            return {}
    
    def log_custom_metric(self, name: str, value: float, step: Optional[int] = None):
        """Log custom metric to MLflow."""
        if self.run_started:
            try:
                mlflow.log_metric(name, value, step=step)
            except Exception as e:
                print(f"Failed to log custom metric {name}: {e}")
    
    def log_custom_param(self, name: str, value: Any):
        """Log custom parameter to MLflow."""
        if self.run_started:
            try:
                mlflow.log_param(name, value)
            except Exception as e:
                print(f"Failed to log custom param {name}: {e}")
    
    def set_tag(self, key: str, value: str):
        """Set custom tag in MLflow."""
        if self.run_started:
            try:
                mlflow.set_tag(key, value)
            except Exception as e:
                print(f"Failed to set tag {key}: {e}")