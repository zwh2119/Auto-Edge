import torch.nn as nn


def build_net(layer_shape, activation, output_activation):
    """Build net with for loop"""
    layers = []
    for j in range(len(layer_shape) - 1):
        act = activation if j < len(layer_shape) - 2 else output_activation
        layers += [nn.Linear(layer_shape[j], layer_shape[j + 1]), act()]
    return nn.Sequential(*layers)


def build_conv1d_net(input_shape, output_shape, kernel_size):
    layers = [nn.Conv1d(in_channels=input_shape,
                        out_channels=output_shape,
                        kernel_size=kernel_size), nn.ReLU()]

    return nn.Sequential(*layers)
