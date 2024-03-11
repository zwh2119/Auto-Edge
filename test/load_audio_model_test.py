import torch
from torchvision.models import resnet34

def load_model_test():
    device = torch.device('cuda:0')
    model_path = 'model_state_dict.pth'
    print(f'device: {type(device)}   {device}')
    model = resnet34(num_classes=10)
    model.load_state_dict(torch.load(model_path))
    print('load model')
    model.to(device)
    print('transform model to target device')
    model.eval()
    print('evaluation mode of model')
    print('load model completed ..')


if __name__ == '__main__':
    load_model_test()
