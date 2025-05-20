import os

from PIL import Image
from torch.utils.data import Dataset


class ImageDataset(Dataset):
    """
    Custom Dataset for COCO detection tasks
    """

    def __init__(self, img_dir, transform=None):
        """
        Args:
            img_dir (str): path to COCO images folder
            transform (transforms.Compose, optional): torchvision transforms to apply
        """
        super().__init__()
        self.img_dir = img_dir
        # get all images files under image folder
        self.files = sorted([f for f in os.listdir(img_dir)
                           if f.lower().endswith((".png", ".jpg", ".jpeg"))])
        self.transform = transform  # Pixel Normalization, Image Resize, to PyTorch Tensor, etc

    def __len__(self):
        return len(self.files)  # images count

    def __getitem__(self, idx):
        fname = self.files[idx]  # find the file name based on index
        path = os.path.join(self.img_dir, fname)  # get absolute path of it
        img = Image.open(path).convert("RGB")  # open it and convert to 3 channels

        # everytime we process an image, transform applies
        if self.transform:
            img = self.transform(img)
        return img, fname
