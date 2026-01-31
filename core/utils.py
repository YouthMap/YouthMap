from os import listdir
from os.path import isfile, join

from core.config import UPLOAD_DIR

def serialize_everything(obj):
    """Convert objects to serialisable things"""
    if "__dict__" in dir(obj):
        return obj.__dict__
    else:
        return None

def get_all_icons():
    """Get all icons (files in the upload directory)"""
    return sorted([f for f in listdir(UPLOAD_DIR) if isfile(join(UPLOAD_DIR, f))])