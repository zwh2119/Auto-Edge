import abc

from core.lib.common import ClassFactory, ClassType
from .base_policy_extraction import BasePolicyExtraction

__all__ = ('SimplePolicyExtraction',)


@ClassFactory.register(ClassType.SCH_POLICY, alias='simple')
class SimplePolicyExtraction(BasePolicyExtraction, abc.ABC):
    def __call__(self, task):
        policy = {}

        meta_data = task.get_metadata()
        policy.update(meta_data)

        pipeline = task.get_pipeline_dicts()

        return policy
