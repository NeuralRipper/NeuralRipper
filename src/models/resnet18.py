import torch.nn as nn  # Neural Network lib
import torchvision


class MyResNet18(nn.Module):
    """
    ResNet18 backbone
    Inherit PyTorch nn Module, define and train my own ResNet from scratch
    num_classes: class num for the model, 91 classes(categories) for COCO dataset
    """

    def __init__(self, num_classes=1000, pretrained=False):
        """
        Args:
            num_classes (int):
                Number of output channels from the final linear layer.
                For ImageNet classification use 1000; for a custom task like COCO, 91 classes(categories)
            pretrained (bool):
                If True, loads ImageNet‑pretrained weights.
                If False, train from scratch
        """
        super().__init__()
        # load ResNet18 architecture
        self.backbone = torchvision.models.resnet18(
            pretrained=pretrained)  # Main feature extractor, no pretrained weights
        # replace the final fully connected layer with new classes
        in_features = self.backbone.fc.in_features
        self.backbone.fc = nn.Linear(in_features, num_classes)

    def forward(self, x):
        """
        Forward pass through the network.

        Args:
            x (torch.Tensor): Input tensor of shape [B, 3, H, W],
                              where B = batch size.

        Returns:
            torch.Tensor: Output logits of shape [B, num_classes].
        """
        return self.backbone(x)
