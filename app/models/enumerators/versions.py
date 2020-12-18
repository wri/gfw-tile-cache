from aenum import Enum


class Versions(str, Enum):
    __doc__ = "Version name of dataset. When using `latest` call will be redirected (307) to version tagged as latest."
    latest = "latest"
