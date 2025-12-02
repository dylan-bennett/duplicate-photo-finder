"""Image hashing functionality for duplicate photo detection.

This module provides the Hasher class for computing perceptual hashes (dHash)
of image files, enabling the identification of duplicate or similar images
regardless of minor differences in format, compression, or metadata.
"""

import imagehash
from PIL import Image


class Hasher:
    """
    A class for computing hashes of image files.
    """

    def __init__(self):
        """
        Initialize the Hasher class.

        No initialization parameters are required for this hasher.
        """
        pass

    def dhash_file(self, filepath):
        """
        Compute the difference hash (dHash) for the image at the given file path.

        Args:
            filepath (str): Path to the image file to hash.

        Returns:
            tuple: (filepath, file_hash) where file_hash is the string representation
            of the dHash, or None if hashing fails or an error occurs.
        """
        try:
            file_hash = str(imagehash.dhash(Image.open(filepath)))
            return (filepath, file_hash)
        except Exception:
            return (filepath, None)
