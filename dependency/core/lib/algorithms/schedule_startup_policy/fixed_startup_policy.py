import abc

from core.lib.common import ClassFactory, ClassType
from .base_startup_policy import BaseStartupPolicy

__all__ = ('FixedStartupPolicy',)


@ClassFactory.register(ClassType.SCH_STARTUP, alias='fixed')
class FixedStartupPolicy(BaseStartupPolicy, abc.ABC):
    def __call__(self, info):
        return {
            'resolution': '1080p',
            'fps': 30,
            'encoding': 'mp4v',
            'buffer_size': 8,
            'pipeline': info['pipeline']
        }
