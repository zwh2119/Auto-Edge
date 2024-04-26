from functools import wraps


def reverse_key_value_in_dict(in_dict: dict) -> dict:
    """
    reverse the key and value in dict object
    {(k:v)} -> {(v:k)}
    :param in_dict: input dict
    :return: output dict
    """

    return {v: k for k, v in in_dict.items()}


def singleton(cls):
    """Set class to singleton class.

    :param cls: class
    :return: instance
    """
    __instances__ = {}

    @wraps(cls)
    def get_instance(*args, **kw):
        """Get class instance and save it into glob list."""
        if cls not in __instances__:
            __instances__[cls] = cls(*args, **kw)
        return __instances__[cls]

    return get_instance

