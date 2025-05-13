import torch.nn as nn       # Neural Network lib
import torchvision
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms, datasets


class MyResNet18(nn.Module):
    """
    Model Definition
    Inherit PyTorch nn Module, define and train my own ResNet from scratch
    """
    def __init__(self):
        super.__init__()
        self.backbone = torchvision.models.resnet18(pretrained=False)   # Main feature extractor, no pretrained weights

    def forward(self, x):
        """
        Forward process in CNN
        :param x: input vector
        :return: None
        """
        self.backbone(x)


