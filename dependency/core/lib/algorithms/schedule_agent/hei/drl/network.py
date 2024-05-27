import torch
from torch.distributions import Normal
import torch.nn as nn
import numpy as np
import torch.nn.functional as F

from .net_utils import build_net, build_conv1d_net
from .utils import format_input_state


class SpecificConvFeatureExtractor(nn.Module):
    def __init__(self, input_channels, hid_channels, kernel_size, output_features, activation=nn.ReLU):
        super(SpecificConvFeatureExtractor, self).__init__()
        self.conv = build_conv1d_net(input_channels, hid_channels, kernel_size, activation)
        self.fc = nn.Linear(hid_channels[-1] * (10 - 2 * 2), output_features*input_channels)

    def forward(self, x):
        x = self.conv(x)
        x = x.view(x.size(0), -1)  # Flatten
        x = self.fc(x)
        return x


class FeatureExtractor(nn.Module):
    def __init__(self):
        super(FeatureExtractor, self).__init__()

    def forward(self, state):
        pass


class Actor(nn.Module):
    def __init__(self, state_dim, action_dim, hid_shape, conv_kernel_size,
                 conv_out_dim, h_activation=nn.ReLU, o_activation=nn.ReLU):
        super(Actor, self).__init__()

        self.conv_net = build_conv1d_net(state_dim[0], conv_out_dim, conv_kernel_size)
        layers = [self._get_net_out(state_dim)] + list(hid_shape)
        self.a_net = build_net(layers, h_activation, o_activation)
        self.mu_layer = nn.Linear(layers[-1], action_dim)
        self.log_std_layer = nn.Linear(layers[-1], action_dim)

        self.LOG_STD_MAX = 2
        self.LOG_STD_MIN = -20

    def forward(self, state, deterministic=False, with_logprob=True):
        """Network with Enforcing Action Bounds"""

        state = format_input_state(state)

        conv_out = self.conv_net(state)
        state_out = conv_out.view(1, -1)

        net_out = self.a_net(state_out)
        mu = self.mu_layer(net_out)
        log_std = self.log_std_layer(net_out)
        log_std = torch.clamp(log_std, self.LOG_STD_MIN, self.LOG_STD_MAX)  # 总感觉这里clamp不利于学习
        std = torch.exp(log_std)
        dist = Normal(mu, std)

        if deterministic:
            u = mu
        else:
            u = dist.rsample()  # '''reparameterization trick of Gaussian'''#
        a = torch.tanh(u)

        if with_logprob:
            # get probability density of logp_pi_a from probability density of u, which is given by the original paper.
            # logp_pi_a = (dist.log_prob(u) - torch.log(1 - a.pow(2) + 1e-6)).sum(dim=1, keepdim=True)

            # Derive from the above equation. No a, thus no tanh(h), thus less gradient vanish and more stable.
            logp_pi_a = dist.log_prob(u).sum(axis=1, keepdim=True) - (2 * (np.log(2) - u - F.softplus(-2 * u))).sum(
                axis=1, keepdim=True)
        else:
            logp_pi_a = None

        return a, logp_pi_a

    def _get_net_out(self, shape):
        o = self.conv_net(torch.zeros(1, *shape))
        return int(np.prod(o.view(1, -1).size()))


class Critic(nn.Module):
    def __init__(self, state_dim, action_dim, hid_shape, conv_kernel_size,
                 conv_out_dim):
        super(Critic, self).__init__()

        self.conv_net = build_conv1d_net(state_dim[0], conv_out_dim, conv_kernel_size)

        layers = [self._get_net_out(state_dim) + action_dim] + list(hid_shape) + [1]

        self.Q_1 = build_net(layers, nn.ReLU, nn.Identity)
        self.Q_2 = build_net(layers, nn.ReLU, nn.Identity)

    def forward(self, state, action):
        format_input_state(state)

        conv_out = self.conv_net(state)
        state_out = conv_out.view(1, -1)

        sa = torch.cat([state_out, action], 1)
        q1 = self.Q_1(sa)
        q2 = self.Q_2(sa)
        return q1, q2

    def _get_net_out(self, shape):
        o = self.conv_net(torch.zeros(1, *shape))
        return int(np.prod(o.view(1, -1).size()))
