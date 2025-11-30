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
