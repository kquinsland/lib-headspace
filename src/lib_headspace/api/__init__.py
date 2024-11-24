"""
lib-headspace
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("lib-headspace")
except PackageNotFoundError:
    __version__ = None


__all__ = ["client"]
