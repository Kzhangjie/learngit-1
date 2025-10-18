import logging

logger = logging.getLogger('kllm')
_handler = logging.StreamHandler()
_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(_handler)

import socket

__hook_dns = {
    'aigc-gateway-test.ksord.com': '120.92.124.158',
    'aibot-api.wps.cn': '120.92.124.158',
    'api.wps.cn': '101.126.4.125',
    'copilot.wps.cn': "101.126.87.240",
}

__original_getaddrinfo = socket.getaddrinfo

def _hook_getaddrinfo(host, port, *args, **kwargs):
    if host in __hook_dns:
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (__hook_dns[host], port))]
    else:
        return __original_getaddrinfo(host, port, *args, **kwargs)

socket.getaddrinfo = _hook_getaddrinfo

from .chat import *
from .lingxi import *
from .dataset import *
from .wps365 import *
from .kdc import *
# from .doubao import *
