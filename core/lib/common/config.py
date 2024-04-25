import os

from .class_factory import ClassFactory,ClassType


class Context:
    """The Context provides the capability of obtaining the context"""
    parameters = os.environ

    @classmethod
    def get_parameter(cls, param, default=None, direct=True):
        """get the value of the key `param` in `PARAMETERS`,
        if not exist, the default value is returned"""

        value = cls.parameters.get(param) or cls.parameters.get(str(param).upper())
        value = value if value else default

        if not direct:
            value = eval(value)

        return value

    @classmethod
    def get_file_path(cls, file_name):
        prefix = cls.parameters.get('DATA_PATH_PREFIX', '/home/data')
        file_dir = os.path.basename(cls.parameters.get('FILE_URL'))
        return os.path.join(prefix, file_dir, file_name)

    @classmethod
    def get_algorithm(cls, algorithm, **param):
        algorithm_dict = Context.get_algorithm_info(algorithm, **param)
        if not algorithm_dict:
            return None
        return ClassFactory.get_cls(
            eval(f'ClassType.{algorithm}'),
            algorithm_dict['method']
        )(**algorithm_dict['param'])

    @classmethod
    def get_algorithm_info(cls, algorithm, **param):
        al_name = cls.get_parameter(f'{algorithm}_NAME')
        al_params = cls.get_parameter(f'{algorithm}_PARAMETERS', default='{}', direct=False)

        if not al_name:
            return None

        al_params.update(**param)

        algorithm_dict = {
            'method': al_name,
            'param': al_params
        }

        return algorithm_dict
