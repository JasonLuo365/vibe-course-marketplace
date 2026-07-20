"""vibe-submit client package."""

import importlib.metadata

__version__ = "0.1.4"


def installed_version() -> str:
    """Return the installed distribution version, or the source fallback."""
    try:
        return importlib.metadata.version("vibe-submit")
    except importlib.metadata.PackageNotFoundError:
        return __version__

