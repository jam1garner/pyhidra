import functools
import re
from itertools import starmap
from pathlib import Path
from typing import NamedTuple, Union

from pyhidra import __version__
from pyhidra.constants import GHIDRA_INSTALL_DIR

_APPLICATION_PATTERN = re.compile(r"^application\.(\S+?)=(.*)$")
_APPLICATION_PATH = GHIDRA_INSTALL_DIR / "Ghidra" / "application.properties"


# this is not a NamedTuple as the fields may change
class ApplicationInfo:
    """
    Ghidra Application Properties
    """
    revision_ghidra_src: str = None
    build_date: str = None
    build_date_short: str = None
    name: str
    version: str
    release_name: str
    layout_version: str = None
    gradle_min: str = None
    java_min: str = None
    java_max: str = None
    java_compiler: str = None

    def __init__(self):
        for line in _APPLICATION_PATH.read_text(encoding="utf8").splitlines():
            match = _APPLICATION_PATTERN.match(line)
            if not match:
                continue
            attr = match.group(1).replace('.', '_').replace('-', '_')
            value = match.group(2)
            super().__setattr__(attr, value)

    def __setattr__(self, *attr):
        raise AttributeError(f"cannot assign to field '{attr[0]}'")

    def __delattr__(self, attr):
        raise AttributeError(f"cannot delete field '{attr}'")

    @property
    def extension_path(self) -> Path:
        """
        Path to the user's Ghidra extensions folder
        """
        root = Path.home() / f".{self.name.lower()}"
        return root / f"{root.name}_{self.version}_{self.release_name}" / "Extensions"


CURRENT_APPLICATION = ApplicationInfo()
CURRENT_GHIDRA_VERSION = CURRENT_APPLICATION.version
MINIMUM_GHIDRA_VERSION = "10.1.1"


def _properties_wrapper(cls):
    @functools.wraps(cls)
    def wrapper(ext: Union[Path, dict] = None):
        if isinstance(ext, dict):
            return cls(**ext)
        def cast(key, value):
            # __annotations__ is created for NamedTuple since its first implementation
            return cls.__annotations__[key](value)

        if ext is None:
            return cls()
        lines = ext.read_text().splitlines()
        args = tuple(starmap(cast, map(lambda l: l.split('='), lines)))
        return cls(*args)
    return wrapper


@_properties_wrapper
class ExtensionDetails(NamedTuple):
    """
    Python side ExtensionDetails
    """

    name: str = "pyhidra"
    description: str = "Native Python Plugin"
    author: str = "Department of Defense Cyber Crime Center (DC3)"
    createdOn: str = ""
    version: str = CURRENT_GHIDRA_VERSION
    pyhidra: str = __version__

    def __repr__(self):
        cls = self.__class__
        return '\n'.join(starmap(lambda i, k: f"{k}={self[i]}", enumerate(cls.__annotations__)))
