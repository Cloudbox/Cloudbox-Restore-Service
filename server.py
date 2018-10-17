#!/usr/bin/env python3
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from flask import Flask, jsonify, request
from gevent.pywsgi import WSGIServer
from walrus.tusks.rlite import WalrusLite
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename

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

# Flask
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = cfg.config['uploads']['max_file_size_kb'] * 1024

# Walrus
db = WalrusLite(cfg.config['core']['database_path'])


############################################################
# FUNCTIONS
############################################################

def json_response(msg: str, error: bool = False):
    return jsonify({
        'msg': msg,
        'error': error
    })


############################################################
# ENDPOINTS
############################################################

@app.route('/', methods=['GET', 'POST'])
def index():
    return json_response('Hello?!', True)


@app.route('/<store_hash>/<store_filename>', methods=['POST'])
def store(store_hash, store_filename):
    # validate supplied parameters
    if not store_hash or not len(store_hash):
        log.error("Invalid hash provided in store request from %s", request.environ.get('REMOTE_ADDR'))
        return json_response('Invalid hash provided', True)
    if not store_filename or not len(store_filename):
        log.error("Invalid filename in store request from %s", request.environ.get('REMOTE_ADDR'))
        return json_response('Invalid filename provided', True)

    # validate filename was an allowed filename
    secured_filename = os.path.basename(secure_filename(store_filename)).lower()
    if secured_filename not in cfg.config['uploads']['allowed_files']:
        log.error("Unspported filename in store request from %s for %s", request.environ.get('REMOTE_ADDR'),
                  secured_filename)
        return json_response('Unsupported filename provided', True)

    # set secured variables
    secured_store_hash = secure_filename(store_hash)
    secured_store_filepath = os.path.join(cfg.config['uploads']['upload_folder'], secured_store_hash, secured_filename)

    # retrieve file
    try:
        if 'file' not in request.files:
            log.error("Request from %s had no file attached...", request.environ.get('REMOTE_ADDR'))
            return json_response('No file was attached to the request', True)

        # there is a file, lets read it
        file = request.files['file']
        # validate filename
        if file.filename == '':
            return json_response('Invalid file was attached', True)

        # store
        log.info("Storing %r to %r for %s", secured_filename, secured_store_filepath,
                 request.environ.get('REMOTE_ADDR'))

        # create directories
        try:
            os.makedirs(os.path.dirname(secured_store_filepath))
        except FileExistsError:
            pass
        except Exception:
            log.exception("Exception with request from %s while creating upload folder %r",
                          request.environ.get('REMOTE_ADDR'), os.path.dirname(secured_store_filepath))
            return json_response('Failed unexpectedly while storing %s' % secured_filename, True)

        # save file
        file.save(secured_store_filepath)
        return json_response('Successfully stored %s' % secured_filename)

    except RequestEntityTooLarge:
        log.exception("Exception with request from %s while storing upload for %r with filename %r: ",
                      request.environ.get('REMOTE_ADDR'), secured_store_hash, secured_filename)
        return json_response('File was too large to be stored', True)
    except Exception:
        log.exception("Exception with request from %s while storing upload for %r with filename %r: ",
                      request.environ.get('REMOTE_ADDR'), secured_store_hash, secured_filename)

    return json_response('Failed unexpectedly while storing %s' % secured_filename, True)


############################################################
# MAIN
############################################################

if __name__ == "__main__":
    log.info("Initializing")

    # start webserver
    log.info("Listening on %s:%d", cfg.config['server']['ip'], cfg.config['server']['port'])
    try:
        server = WSGIServer((cfg.config['server']['ip'], cfg.config['server']['port']), app, log=None)
        server.serve_forever()
    except Exception:
        log.exception("Fatal exception occurred in server: ")
    log.info("Finished!")
