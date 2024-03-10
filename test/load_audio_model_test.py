import torch

def load_model_test():
    device = torch.device('cuda:0')
    model_path = '/home/nvidia/zwh/Auto-Edge/model_lib_mid/model.pth'
    print(f'device: {type(device)}   {device}')
    try:
        with open(model_path, 'rb') as f:
            model = torch.jit.load(f, map_location=device)
    except Exception as e:
        with open(model_path, 'rb') as f:
            model = torch.jit.load(f, map_location=torch.device('cpu'))
    print('load model')
    model.to(device)
    print('transform model to target device')
    model.eval()
    print('evaluation mode of model')
    print('load model completed ..')


if __name__ == '__main__':
    load_model_test()
