import os
import toml

def _load(paths:list[str]):
    for p in paths:
        if os.path.exists(p):
            return toml.load(p)
    return {}

home_dir = os.getenv("HOME") or os.getenv("USERPROFILE") or ""
# 获取项目根目录路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
project_config = os.path.join(project_root, ".kllm.toml")

_config = _load([
    '.kllm.toml', 
    project_config,
    os.path.join(home_dir, ".kllm.toml") if home_dir else ""
])

class AutoConfig:
    @staticmethod
    def get(key:str):
        val = os.getenv(key)
        if val:
            return val
        
        val = _config
        for p in key.split("."):
            if p not in val:
                return None
            val = val[p]
        return val

