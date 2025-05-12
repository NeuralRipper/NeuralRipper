from torchvision import transforms

transform = transforms.Compose([
    transforms.Resize((480, 480)),      # smaller -> trains faster
    transforms.RandomHorizontalFlip(0.5),   # probability of flipping current image
    transforms.ToTensor(),              # PIL -> PyTorch FloatTensor
    transforms.Normalize(               # data from ImageNet, pixel normalization
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

