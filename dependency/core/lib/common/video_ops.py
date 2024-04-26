from core.lib.common import reverse_key_value_in_dict


class VideoOps:
    resolution_dict = {'1080p': (1920, 1080),
                       '720p': (1280, 720),
                       '480p': (640, 480),
                       '360p': (640, 360)}

    resolution_dict_reverse = reverse_key_value_in_dict(resolution_dict)

    @classmethod
    def text2resolution(cls, text: str):
        assert text in cls.resolution_dict, f'Invalid resolution "{text}"!'
        return cls.resolution_dict[text]

    @classmethod
    def resolution2text(cls, resolution: tuple):
        assert resolution in cls.resolution_dict_reverse, f'Invalid resolution "{resolution}"!'
        return cls.resolution_dict_reverse[resolution]
