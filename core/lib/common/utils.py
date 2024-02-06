def reverse_key_value_in_dict(in_dict: dict) -> dict:
    """
    reverse the key and value in dict object
    {(k:v)} -> {(v:k)}
    :param in_dict: input dict
    :return: output dict
    """

    return {v: k for k, v in in_dict.items()}
