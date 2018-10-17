#!/usr/bin/env python3
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from utils.config import Config

############################################################
# INIT
############################################################

# Logging
logFormatter = logging.Formatter('%(asctime)24s - %(levelname)8s - %(name)50s - %(funcName)30s '
                                 '[%(thread)5d]: %(message)s')
rootLogger = logging.getLogger()
rootLogger.setLevel(logging.INFO)

# Console logger, log to stdout instead of stderr
consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)

# File logger
fileHandler = RotatingFileHandler(
    os.path.join(os.path.dirname(sys.argv[0]), 'activity.log'),
    maxBytes=1024 * 1024 * 5,
    backupCount=5,
    encoding='utf-8'
)

fileHandler.setFormatter(logFormatter)
rootLogger.addHandler(fileHandler)

# Config
cfg = Config(rootLogger)

# Logger
log = rootLogger.getChild("cloudbox_restore_service")

############################################################
# MAIN
############################################################

if __name__ == "__MAIN__":
    log.info("Hello")
