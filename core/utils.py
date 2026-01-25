from os import listdir
from os.path import isfile, join

from core.config import UPLOAD_DIR


def get_all_icons():
    """Get all icons (files in the upload directory)"""
    return [f for f in listdir(UPLOAD_DIR) if isfile(join(UPLOAD_DIR, f))].sorted()