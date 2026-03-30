class UnsupportedFileTypeError(Exception):
    """Raised when no parser can handle the given file."""
    pass

class UnsupportedBlockTypeError(Exception):
    """Raised when chunker encounters unsupported block type."""
    pass

class InvalidFileNameError(Exception):
    """Raised when company or quarter cannot be parsed from the filename."""
    pass