import logging
import os

import yaml

# Check you have a config file
if not os.path.isfile("config.yml"):
    logging.error(
        "Your config file is missing. Ensure config.yml is present and that you have updated it according to your needs.")
    exit()

# Load config
config = yaml.safe_load(open("config.yml"))
logging.info("Loaded config.")

HTTP_PORT = config["http-port"]
DATABASE_DIR = config["database-dir"]
UPLOAD_DIR = config["upload-dir"]
