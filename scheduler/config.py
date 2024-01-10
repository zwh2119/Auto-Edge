import os


class Context:
    """The Context provides the capability of obtaining the context"""
    parameters = os.environ

    @classmethod
    def get_parameters(cls, param, default=None):
        """get the value of the key `param` in `PARAMETERS`,
        if not exist, the default value is returned"""
        value = cls.parameters.get(
            param) or cls.parameters.get(str(param).upper())
        return value if value else default

    @classmethod
    def get_file_path(cls, file_name):
        prefix = cls.parameters.get('DATA_PATH_PREFIX', '/home/data')
        file_dir = os.path.basename(cls.parameters.get('FILE_URL'))
        return os.path.join(prefix, file_dir, file_name)
