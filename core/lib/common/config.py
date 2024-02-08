import os


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

        assert value, f'parameter "{param}" not exists in environment!'

        return value

    @classmethod
    def get_file_path(cls, file_name):
        prefix = cls.parameters.get('DATA_PATH_PREFIX', '/home/data')
        file_dir = os.path.basename(cls.parameters.get('FILE_URL'))
        return os.path.join(prefix, file_dir, file_name)
