import torch
from torch import nn
import torch.nn.functional as F
import torchvision
import torchvision.transforms as transforms
from torchvision import models
from torchvision.datasets import ImageFolder
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np

trans_train = transforms.Compose([transforms.RandomResizedCrop(224), transforms.RandomHorizontalFlip(),
     transforms.ToTensor(), transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])])

trans_valid = transforms.Compose([transforms.Resize(256), transforms.CenterCrop(224),
    transforms.ToTensor(), transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])])

trainset = torchvision.datasets.CIFAR10(root='./data', train=True, download=False, transform=trans_train)
trainloader = torch.utils.data.DataLoader(trainset, batch_size=128, shuffle=True, pin_memory=True)

testset = torchvision.datasets.CIFAR10(root='./data', train=False, download=False, transform=trans_valid)
testloader = torch.utils.data.DataLoader(testset, batch_size=128, shuffle=False, pin_memory=True)

classes = ('plane', 'car', 'bird', 'cat', 'deer', 'dog', 'frog', 'horse', 'ship', 'truck')

# 使用预训练模型
net = models.resnet18(pretrained=True)
# 冻结模型参数
for param in net.parameters():
    param.requires_grad = False
# 将全连接层改为十分类
device = torch.device("cuda:0" if torch.cuda.is_available() else "cup")
net.fc = nn.Linear(512, 10)

# 查看总参数及训练参数
total_params = sum(p.numel() for p in net.parameters())
print("总参数个数：{}".format(total_params))
total_trainable_params = sum(p.numel() for p in net.parameters() if p.requires_grad)
print("需要训练的参数个数：{}".format(total_trainable_params))

net = net.to(device)
def get_acc(output, label):
    total = output.shape[0]  # 批量数
    _, pred_label = output.max(1)
    num_correct = (pred_label == label).sum().item()
    return num_correct / total
criterion = nn.CrossEntropyLoss()
# 只需要优化最后一层参数
optimizer = torch.optim.SGD(net.fc.parameters(), lr=1e-3, weight_decay=1e-3, momentum=0.9)
num_epochs = 20  # 周期数

def train(net, train_data, valid_data, num_epochs, optimizer, criterion):
    prev_time = datetime.now()
    for epoch in range(num_epochs):
        train_loss = 0
        train_acc = 0
        net = net.train()
        for im, label in train_data:
            im = im.to(device)  # (bs, 3, h, w)
            label = label.to(device)  # (bs, h, w)
            # forward
            output = net(im)
            loss = criterion(output, label)
            # backward
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            train_loss += loss.item()
            train_acc += get_acc(output, label)

        cur_time = datetime.now()
        h, remainder = divmod((cur_time - prev_time).seconds, 3600)
        m, s = divmod(remainder, 60)
        time_str = "Time %02d:%02d:%02d" % (h, m, s)
        if valid_data is not None:
            valid_loss = 0
            valid_acc = 0
            net = net.eval()
            for im, label in valid_data:
                im = im.to(device)  # (bs, 3, h, w)
                label = label.to(device)  # (bs, h, w)
                output = net(im)
                loss = criterion(output, label)
                valid_loss += loss.item()
                valid_acc += get_acc(output, label)
            epoch_str = ("Epoch %d. Train Loss: %f, Train Acc: %f, Valid Loss: %f, Valid Acc: %f, " %
                         (epoch, train_loss / len(train_data),train_acc / len(train_data), valid_loss / len(valid_data),
                          valid_acc / len(valid_data)))
        else:
            epoch_str = ("Epoch %d. Train Loss: %f, Train Acc: %f, " %
                         (epoch, train_loss / len(train_data), train_acc / len(train_data)))
        prev_time = cur_time
        print(epoch_str + time_str)

#  训练模型
train(net, trainloader, testloader, num_epochs, optimizer, criterion)