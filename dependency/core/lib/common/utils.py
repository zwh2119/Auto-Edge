from functools import wraps
import threading


def reverse_key_value_in_dict(in_dict: dict) -> dict:
    """
    reverse the key and value in dict object
    {(k:v)} -> {(v:k)}
    :param in_dict: input dict
    :return: output dict
    """

    return {v: k for k, v in in_dict.items()}


def convert_ndarray_to_list(obj):
    import numpy as np
    if isinstance(obj, np.ndarray):
        return convert_ndarray_to_list(obj.tolist())
    elif isinstance(obj, list):
        return [convert_ndarray_to_list(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_ndarray_to_list(item) for item in obj)
    elif isinstance(obj, dict):
        return {convert_ndarray_to_list(key): convert_ndarray_to_list(value) for key, value in obj.items()}
    else:
        return obj


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


def timeout(seconds):
    """Decorator to run a function with a timeout."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            class FuncThread(threading.Thread):
                def __init__(self):
                    super().__init__()
                    self.result = None
                    self.exc = None

                def run(self):
                    try:
                        self.result = func(*args, **kwargs)
                    except Exception as e:
                        self.exc = e

            func_thread = FuncThread()
            func_thread.start()
            func_thread.join(seconds)

            if func_thread.is_alive():
                func_thread.join()
                raise TimeoutError(f"Function {func.__name__} exceeded its timeout of {seconds} seconds")

            if func_thread.exc:
                raise func_thread.exc

            return func_thread.result

        return wrapper

    return decorator
