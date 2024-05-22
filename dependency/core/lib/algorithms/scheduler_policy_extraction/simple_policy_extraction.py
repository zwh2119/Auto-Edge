import abc

from core.lib.common import ClassFactory, ClassType
from .base_policy_extraction import BasePolicyExtraction

__all__ = ('SimplePolicyExtraction',)


@ClassFactory.register(ClassType.SCH_POLICY, alias='simple')
class SimplePolicyExtraction(BasePolicyExtraction, abc.ABC):
    def __call__(self, task):
        policy = {}

        return policy
