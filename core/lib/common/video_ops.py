class VideoOps:

    # TODO: here config file?
    @staticmethod
    def text2resolution(text: str):
        resolution_dict = {'1080p': (1920, 1080),
                           '720p': (1280, 720),
                           '360p': (640, 360)}

        assert text in resolution_dict
        return resolution_dict[text]

    @staticmethod
    def resolution2text(resolution: tuple):
        resolution_dict = {(1920, 1080): '1080p',
                           (1280, 720): '720p',
                           (640, 360): '360p'}
        assert resolution in resolution_dict
        return resolution_dict[resolution]
