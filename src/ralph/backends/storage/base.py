"""Base storage backend for Ralph"""

from abc import ABC, abstractmethod


class BaseStorage(ABC):
    """Base storage backend interface"""

    name = "base"

    @abstractmethod
    def list(self):
        """List files in the storage backend"""

    @abstractmethod
    def url(self, name):
        """Get `name` file absolute URL"""

    @abstractmethod
    def read(self, name, chunk_size=4096):
        """Read `name` file and stream its content by chunks of a given size"""

    @abstractmethod
    def write(self, name, content):
        """Write content to the `name` target"""