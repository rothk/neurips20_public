import os
import torch as th
import torch.nn as nn
import torch.utils.model_zoo as model_zoo
from collections import OrderedDict

model_urls = {
    'cifar10': 'http://ml.cs.tsinghua.edu.cn/~chenxi/pytorch-models/cifar10-d875770b.pth',
    'cifar100': 'http://ml.cs.tsinghua.edu.cn/~chenxi/pytorch-models/cifar100-3a55a987.pth',
}

class CIFAR(nn.Module):
    def __init__(self, features, n_channel, num_classes):
        super(CIFAR, self).__init__()
        assert isinstance(features, nn.Sequential), type(features)
        self.features = features
        self.classifier = nn.Sequential(
            nn.Linear(n_channel, num_classes)
        )

    def forward(self, x):
        x = self.features(x)
        x = x.view(x.size(0), -1)
        x = self.classifier(x)
        return x


class Carlini(nn.Module):
    def __init__(self, features, n_channel):
        super(Carlini, self).__init__()
        assert isinstance(features, nn.Sequential), type(features)
        self.features = features
        self.classifier = nn.Sequential(
                nn.Linear(n_channel, 256),
                nn.ReLU(),
                nn.Dropout(),
                nn.Linear(256, 256),
                nn.ReLU(),
                nn.Linear(256, 10)
        )

    def forward(self, x):
        x = self.features(x)
        x = x.view(x.size(0), -1)
        x = self.classifier(x)
        return x


def make_layers(cfg, batch_norm=False):
    layers = []
    in_channels = 3
    for i, v in enumerate(cfg):
        if v == 'M':
            layers += [nn.MaxPool2d(kernel_size=2, stride=2)]
        else:
            padding = v[1] if isinstance(v, tuple) else 1
            out_channels = v[0] if isinstance(v, tuple) else v
            conv2d = nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=padding)
            if batch_norm:
                layers += [conv2d, nn.BatchNorm2d(out_channels, affine=False), nn.ReLU()]
            else:
                layers += [conv2d, nn.ReLU()]
            in_channels = out_channels
    return nn.Sequential(*layers)

def cifar10_tiny(n_channel, pretrained=False, map_location=None, padding=1, trained_adv=False):
    if padding == 1:
        cfg = [(n_channel, padding), 'M', (n_channel, padding), 'M', (2*n_channel, padding), 'M', (2*n_channel, 0), 'M']
    elif padding == 0:
        cfg = [(n_channel, padding), (n_channel, padding), 'M', (2*n_channel, padding), 'M', (2*n_channel, 0), 'M']
    layers = make_layers(cfg, batch_norm=False)
    model = CIFAR(layers, n_channel=2*n_channel if padding == 1 else 4*2*n_channel, num_classes=10)
    if pretrained:
        if padding == 1:
            state_dict = th.load(model_urls['cifar10_tiny'], map_location=map_location)
        elif padding == 0:
            if trained_adv:
                state_dict = th.load(model_urls['cifar10_tinyb_adv'], map_location=map_location)
            else:
                state_dict = th.load(model_urls['cifar10_tinyb'], map_location=map_location)
        assert isinstance(state_dict, (dict, OrderedDict)), type(state_dict)
        model.load_state_dict(state_dict)
    return model

def cifar10(n_channel, pretrained=False, map_location=None, trained_adv_l2_eps=0, trained_yoshida_eps=0, trained_static_eps=0, trained_dynamic_eps=0, load_inf=False):
    cfg = [n_channel, n_channel, 'M', 2*n_channel, 2*n_channel, 'M', 4*n_channel, 4*n_channel, 'M', (8*n_channel, 0), 'M']
    layers = make_layers(cfg, batch_norm=True)
    model = CIFAR(layers, n_channel=8*n_channel, num_classes=10)
    if pretrained:
        if trained_adv_l2_eps > 0:
            e = round(trained_adv_l2_eps * 255)
            url = 'cifar10_advl2_{}'.format(e)
            if load_inf:
                url = 'cifar10_inf_adv'
            state_dict = th.load(model_urls[url], map_location=map_location)
        elif trained_yoshida_eps > 0:
            e = round(trained_yoshida_eps * 255)
            url = 'cifar10_yoshida_{}'.format(e)
            state_dict = th.load(model_urls[url], map_location=map_location)
        elif trained_static_eps > 0:
            e = round(trained_static_eps * 255)
            url = 'cifar10_static_{}'.format(e)
            state_dict = th.load(model_urls[url], map_location=map_location)
        elif trained_dynamic_eps > 0:
            e = round(trained_dynamic_eps * 255)
            url = 'cifar10_dynamic_{}'.format(e)
            state_dict = th.load(model_urls[url], map_location=map_location)
        elif load_inf:
            url = 'cifar10_inf'
            state_dict = th.load(model_urls[url], map_location=map_location)
        else:
            m = model_zoo.load_url(model_urls['cifar10'], map_location=map_location)
            state_dict = m.state_dict() if isinstance(m, nn.Module) else m
        assert isinstance(state_dict, (dict, OrderedDict)), type(state_dict)
        model.load_state_dict(state_dict)
    return model

def carlini(pretrained=False, map_location=None):
    cfg = [(64, 0), (64, 0), 'M', (128, 0), (128, 0), 'M']
    layers = make_layers(cfg, batch_norm=False)
    model = Carlini(layers, n_channel=128*5*5)
    if pretrained:
        state_dict = th.load(model_urls['carlini'], map_location=map_location)
        assert isinstance(state_dict, (dict, OrderedDict)), type(state_dict)
        model.load_state_dict(state_dict)
    return model

def cifar100(n_channel, pretrained=None):
    cfg = [n_channel, n_channel, 'M', 2*n_channel, 2*n_channel, 'M', 4*n_channel, 4*n_channel, 'M', (8*n_channel, 0), 'M']
    layers = make_layers(cfg, batch_norm=True)
    model = CIFAR(layers, n_channel=8*n_channel, num_classes=100)
    if pretrained is not None:
        m = model_zoo.load_url(model_urls['cifar100'])
        state_dict = m.state_dict() if isinstance(m, nn.Module) else m
        assert isinstance(state_dict, (dict, OrderedDict)), type(state_dict)
        model.load_state_dict(state_dict)
    return model

