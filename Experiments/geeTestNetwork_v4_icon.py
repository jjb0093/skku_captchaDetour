import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
import torchvision.transforms as transforms
from torchvision import models

import cv2, os, random
import numpy as np
import matplotlib.pyplot as plt

class SiamNetwork(nn.Module):
    def __init__(self, embeddingDim = 128):
        super().__init__()

        self.backbone = models.resnet18(pretrained = True)
        self.backbone = nn.Sequential(*list(self.backbone.children())[:-1])

        self.fc = nn.Sequential(
            nn.Linear(512, 256),
            nn.ReLU(inplace = True),
            nn.Dropout(0.3),
            nn.Linear(256, embeddingDim)
        )

    def forward_once(self, img):
        features = self.backbone(img)
        features = features.view(features.size(0), -1)
        embedding = self.fc(features)

        return embedding
        
    def forward(self, img1, img2):
        output1 = self.forward_once(img1)
        output2 = self.forward_once(img2)

        return output1, output2
        
class SiamDataset(Dataset):
    def __init__(self, imgPairs, labels):
        self.imgPairs = imgPairs
        self.labels = labels
        
    def __getitem__(self, index):
        path_img1, path_img2 = self.imgPairs[index]
        label = self.labels[index]

        img1, img2 = cv2.imread(f"trainDataNew/icons/{path_img1}", cv2.IMREAD_UNCHANGED), cv2.imread(f"trainDataNew/{path_img2}")
        img1 = cv2.Canny(img1, 300, 400)

        '''
        img1, img2 = cv2.imread(f"trainData/icons/{path_img1}", cv2.IMREAD_UNCHANGED), cv2.imread(f"trainDataNew/{path_img2}")
        
        b, g, r, a = cv2.split(img1)

        mask = a != 255
        b[mask], g[mask], r[mask], a[mask] = 255, 255, 255, 255

        img1 = cv2.merge((b, g, r, a))
        '''
        
        img1, img2 = cv2.cvtColor(img1, cv2.COLOR_BGR2RGB), cv2.cvtColor(img2, cv2.COLOR_BGR2RGB)

        img1, img2 = transform(img1), transform(img2)
        return img1, img2, torch.tensor(label, dtype = torch.float32)
    
    def __len__(self):
        return len(self.imgPairs)

class Loss(nn.Module):
    def __init__(self, margin = 2.0):
        super().__init__()
        self.margin = margin

    def forward(self, output1, output2, label):
        distance = F.pairwise_distance(output1, output2)
        loss = torch.mean(
            (1 - label) * torch.pow(distance, 2) +
            label * torch.pow(torch.clamp(self.margin - distance, min = 0.0), 2)
        )

        return loss
    
def train(model, trainLoader, criterion, optimizer, device, epoch):
    model.train()
    totalLoss = 0.0

    for batch_idx, (img1, img2, label) in enumerate(trainLoader):
        print(f"\tBatch {batch_idx + 1}/{len(trainLoader)} 처리 중...", end = "\r")
        img1, img2, label = img1.to(device), img2.to(device), label.to(device)

        optimizer.zero_grad()
        output1, output2 = model(img1, img2)
        loss = criterion(output1, output2, label)
        loss.backward()
        optimizer.step()

        totalLoss += loss.item()

    avgLoss = totalLoss / len(trainLoader)
    return avgLoss

def evaluate(model, testLoader, device):
    model.eval()

    distances = []
    with torch.no_grad():
        for img1, img2, label in testLoader:
            img1, img2 = img1.to(device), img2.to(device)
            output1, output2 = model(img1, img2)

            distance = F.pairwise_distance(output1, output2)
            distances.append(distance.mean().item())

    return np.mean(distances)

print(torch.cuda.is_available()) 
device = torch.device("cpu")

transform = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((50, 50)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225])
])

pos_pairs, neg_pairs = [], []

iconNames = os.listdir("trainDataNew/icons")
for i in range(len(iconNames)):
    print(f"아이콘 {i + 1}/{len(iconNames)} : {iconNames[i]}")
    for k in range(len(iconNames)):
        name = iconNames[k].split(".")[0]

        for data in os.listdir(f"trainDataNew/datas/{name}"):
            if(i == k):
                pos_pairs.append([iconNames[i], f"datas/{name}/{data}"])
            else:
                neg_pairs.append([iconNames[i], f"datas/{name}/{data}"])

neg_back_pairs = []
backgroundNames = os.listdir("trainDataNew/backgrounds")
for i in range(len(iconNames)):
    for k in range(len(backgroundNames)):
        neg_back_pairs.append([iconNames[i], f"backgrounds/{backgroundNames[k]}"])

model = SiamNetwork().to(device)
criterion = Loss()
optimizer = optim.Adam(model.parameters(), lr = 0.001)

num_epochs = 100
avantLoss = float('inf')
lossCount = 0

for epoch in range(num_epochs):
    neg_sampled = random.sample(neg_pairs, len(pos_pairs))
    neg_back_sampled = random.sample(neg_back_pairs, len(pos_pairs) // 2)

    imgPairs = pos_pairs + neg_sampled + neg_back_sampled
    labels = [0] * len(pos_pairs) + [1] * len(neg_sampled) + [1] * len(neg_back_sampled)

    combined = list(zip(imgPairs, labels))
    random.shuffle(combined)
    imgPairs[:], labels[:] = zip(*combined)

    print(f"총 이미지 쌍: {len(imgPairs)}, 긍정 쌍: {labels.count(0)}, 부정 쌍: {labels.count(1)}")

    dataset = SiamDataset(imgPairs, labels)
    trainLoader = DataLoader(dataset, batch_size = 32, shuffle = True)

    print(f"Epoch {epoch + 1}/{num_epochs} 학습 시작!")
    avgLoss = train(model, trainLoader, criterion, optimizer, device, epoch)
    print(f"Epoch [{epoch + 1}/{num_epochs}] 학습 종료, Avg Loss: {avgLoss:.4f}")

    if(avgLoss < avantLoss):
        avantLoss = avgLoss
        torch.save(model.state_dict(), "iconSolverModel.pth")
        lossCount = 0
    else:
        lossCount += 1
    
    if(lossCount == 5):
        print("개선 없음. 학습 종료")
        break


