"""autoharness — globally-installed agent harness framework."""

try:
    from importlib.metadata import version
    __version__ = version("autoharness")
except Exception:
    __version__ = "1.1.1"  # fallback for editable / pre-install contexts
