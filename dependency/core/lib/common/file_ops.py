import os
import hashlib
import shutil
import pickle
import tempfile
import joblib
import re
import codecs


class FileOps:
    """
    This is a class with some class methods
    to handle some files or folder.
    """

    _GCS_PREFIX = "gs://"
    _S3_PREFIX = "s3://"
    _LOCAL_PREFIX = "file://"
    _URI_RE = "https?://(.+)/(.+)"
    _HTTP_PREFIX = "http(s)://"
    _HEADERS_SUFFIX = "-headers"

    @classmethod
    def make_dir(cls, *args):
        """Make new a local directory.

        :param * args: list of str path to joined as a new directory to make.

        """
        _path = cls.join_path(*args)
        if not os.path.isdir(_path):
            os.makedirs(_path, exist_ok=True)

    @classmethod
    def get_file_hash(cls, filepath):
        md5_hash = hashlib.md5()
        if not (filepath and os.path.isfile(filepath)):
            return ""
        a_file = open(filepath, "rb")
        content = a_file.read()
        md5_hash.update(content)
        digest = md5_hash.hexdigest()
        return digest

    @classmethod
    def clean_folder(cls, target, clean=True):
        """clean the target directories.
        create path if `target` not exists,
        initial path if `clean` be True

        :param target: list of str path need to clean.
        :type target: list
        :param clean: clear target if exists.
        :type clean: bool
        """
        if isinstance(target, str):
            target = [target]
        for path in set(target):
            args = str(path).split(os.path.sep)
            if len(args) < 2:
                continue
            if not args[0]:
                args[0] = os.path.sep
            _path = cls.join_path(*args)
            if clean:
                cls.delete(_path)
            if os.path.isfile(_path):
                _path = cls.join_path(*args[:len(args) - 1])
            os.makedirs(_path, exist_ok=True)
        return target

    @classmethod
    def delete(cls, path):
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            if os.path.isfile(path):
                os.remove(path)
        except Exception:
            pass

    @classmethod
    def make_base_dir(cls, *args):
        """Make new a base directory.

        :param * args: list of str path to joined as a
        new base directory to make.

        """
        _file = cls.join_path(*args)
        if os.path.isfile(_file):
            return
        _path, _ = os.path.split(_file)
        if not os.path.isdir(_path):
            os.makedirs(_path, exist_ok=True)

    @classmethod
    def join_path(cls, *args):
        """Join list of path and return.

        :param * args: list of str path to be joined.
        :return: joined path str.
        :rtype: str

        """
        if len(args) == 1:
            return args[0]
        is_root = os.path.sep if str(args[0]).startswith(os.path.sep) else ""
        args = list(map(lambda x: x.lstrip(os.path.sep), args))
        args[0] = f"{is_root}{args[0]}"
        # local path
        if ":" not in args[0]:
            args = tuple(args)
            return os.path.join(*args)
        # http or s3 path
        tail = os.path.join(*args[1:])
        return os.path.join(args[0], tail)

    @classmethod
    def remove_path_prefix(cls, org_str: str, prefix: str):
        """remove the prefix, for converting path
        in container to path in host."""
        if not prefix:
            return org_str
        p = prefix[:-1] if prefix.endswith(os.path.sep) else prefix
        if org_str.startswith(p):
            out_str = org_str.replace(p, '', 1)
            return out_str
        else:
            return org_str

    @classmethod
    def dump_pickle(cls, obj, filename):
        """Dump a object to a file using pickle.

        :param object obj: target object.
        :param str filename: target pickle file path.

        """
        if not os.path.isfile(filename):
            cls.make_base_dir(filename)
        with open(filename, "wb") as f:
            pickle.dump(obj, f)

    @classmethod
    def load_pickle(cls, filename):
        """Load a pickle file and return the object.

        :param str filename: target pickle file path.
        :return: return the loaded original object.
        :rtype: object or None.

        """
        filename = cls.download(filename)
        if not os.path.isfile(filename):
            return None
        with open(filename, "rb") as f:
            return pickle.load(f)

    @classmethod
    def copy_folder(cls, src, dst):
        """Copy a folder from source to destination.

        :param str src: source path.
        :param str dst: destination path.

        """
        if dst is None or dst == "" or (not os.path.isdir(src)):
            return
        if not os.path.exists(dst):
            shutil.copytree(src, dst)
        else:
            if os.path.samefile(src, dst):
                return
            for files in os.listdir(src):
                name = os.path.join(src, files)
                back_name = os.path.join(dst, files)
                if os.path.isfile(name):
                    shutil.copy(name, back_name)
                else:
                    if not os.path.isdir(back_name):
                        shutil.copytree(name, back_name)
                    else:
                        cls.copy_folder(name, back_name)

    @classmethod
    def copy_file(cls, src, dst):
        """Copy a file from source to destination.

        :param str src: source path.
        :param str dst: destination path.

        """
        if not dst:
            return

        if os.path.isfile(src):
            if os.path.isfile(dst) and os.path.samefile(src, dst):
                return
            if os.path.isdir(dst):
                basename = os.path.basename(src)
                dst = os.path.join(dst, basename)
            parent_dir = os.path.dirname(dst)
            cls.clean_folder([parent_dir], clean=False)

            shutil.copy(src, dst)
        elif os.path.isdir(src):
            cls.clean_folder([dst], clean=False)
            cls.copy_folder(src, dst)

    @classmethod
    def dump(cls, obj, dst=None) -> str:
        fd, name = tempfile.mkstemp()
        os.close(fd)
        joblib.dump(obj, name)
        return cls.upload(name, dst)

    @classmethod
    def load(cls, src: str):
        src = cls.download(src)
        obj = joblib.load(src)
        return obj

    @classmethod
    def download(cls, src, dst=None, unzip=False) -> str:
        if dst is None:
            fd, dst = tempfile.mkstemp()
            os.close(fd)
        cls.clean_folder([os.path.dirname(dst)], clean=False)
        if src.startswith(cls._GCS_PREFIX):
            cls.gcs_download(src, dst)
        elif src.startswith(cls._S3_PREFIX):
            cls.s3_download(src, dst)
        elif cls.is_local(src):
            cls.copy_file(src, dst)
        elif re.search(cls._URI_RE, src):
            cls.http_download(src, dst)
        if unzip is True and dst.endswith(".tar.gz"):
            cls._untar(dst)
        return dst

    @classmethod
    def upload(cls, src, dst, tar=False, clean=True) -> str:
        if dst is None:
            fd, dst = tempfile.mkstemp()
            os.close(fd)
        if not cls.is_local(src):
            fd, name = tempfile.mkstemp()
            os.close(fd)
            cls.download(src, name)
            src = name
        if tar:
            cls._tar(src, f"{src}.tar.gz")
            src = f"{src}.tar.gz"

        if dst.startswith(cls._GCS_PREFIX):
            cls.gcs_upload(src, dst)
        elif dst.startswith(cls._S3_PREFIX):
            cls.s3_upload(src, dst)
        else:
            cls.copy_file(src, dst)
        if cls.is_local(src) and clean:
            if cls.is_local(dst) and os.path.samefile(src, dst):
                return dst
            cls.delete(src)
        return dst

    @classmethod
    def is_local(cls, src):
        return src.startswith(cls._LOCAL_PREFIX) or cls.exists(src)


    @classmethod
    def http_download(cls, src, dst):
        """Download data from http or https web site.

        :param src: the data path
        :type src: str
        :param dst: the data path
        :type dst: str
        :raises FileNotFoundError: if the file path is
         not exist, an error will raise
        """
        from six.moves import urllib

        try:
            urllib.request.urlretrieve(src, dst)
        except (urllib.error.URLError, IOError) as e:
            raise e

    @classmethod
    def _untar(cls, src, dst=None):
        import tarfile
        if dst is None:
            dst = os.path.dirname(src)
        with tarfile.open(src, 'r:gz') as tar:
            tar.extractall(path=dst)

    @classmethod
    def _tar(cls, src, dst):
        import tarfile
        with tarfile.open(dst, 'w:gz') as tar:
            if os.path.isdir(src):
                for root, _, files in os.walk(src):
                    for file in files:
                        filepath = os.path.join(root, file)
                        tar.add(filepath)
            elif os.path.isfile(src):
                tar.add(os.path.realpath(src))

    @classmethod
    def exists(cls, folder):
        """Is folder existed or not.

        :param folder: folder
        :type folder: str
        :return: folder existed or not.
        :rtype: bool
        """
        return os.path.isdir(folder) or os.path.isfile(folder)

    @classmethod
    def obj_to_pickle_string(cls, x):
        return codecs.encode(pickle.dumps(x), "base64").decode()

    @classmethod
    def pickle_string_to_obj(cls, s):
        return pickle.loads(codecs.decode(s.encode(), "base64"))
