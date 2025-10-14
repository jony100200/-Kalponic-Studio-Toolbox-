import os
import torch
import torch.nn as nn
import torchvision.transforms as transforms
from torchvision.models import efficientnet_b0, EfficientNet_B0_Weights
from PIL import Image
import numpy as np

class AISeamChecker:
    def __init__(self, model_path=None):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model_path = model_path or os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models', 'efficientnet_b0_seamless.pth')
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        
        # Load EfficientNet-B0 with binary classifier head
        self.model = efficientnet_b0(weights=EfficientNet_B0_Weights.IMAGENET1K_V1)
        self.model.classifier[1] = nn.Linear(self.model.classifier[1].in_features, 2)  # Binary: seamless vs not seamless
        
        # Load or initialize weights
        if os.path.exists(self.model_path):
            self.model.load_state_dict(torch.load(self.model_path, map_location=self.device))
        else:
            # Save initial weights (can be fine-tuned later)
            torch.save(self.model.state_dict(), self.model_path)
        
        self.model.to(self.device)
        self.model.eval()
        
        # Preprocessing transform
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

    def is_seamless_ai(self, image_path):
        """Use EfficientNet-B0 to check if image is seamless."""
        try:
            image = Image.open(image_path).convert('RGB')
            input_tensor = self.transform(image).unsqueeze(0).to(self.device)

            with torch.no_grad():
                outputs = self.model(input_tensor)
                _, predicted = torch.max(outputs, 1)
                return predicted.item() == 1  # 1 = seamless, 0 = not seamless
        except Exception as e:
            return None

    def download_model(self, url, save_path):
        """Download pre-trained model (placeholder - would need actual model)."""
        # For now, just use the pre-trained weights
        pass