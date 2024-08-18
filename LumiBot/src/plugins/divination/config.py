from pydantic import BaseModel


class Config(BaseModel):
    """Plugin Config Here"""
    current_system: str = 'guanyin'  # 默认为观音灵签