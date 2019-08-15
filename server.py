#!/usr/bin/env python3
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from flask import Flask, jsonify, request, send_from_directory
from gevent.pywsgi import WSGIServer
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


@app.route('/load/<load_hash>/<load_filename>', methods=['GET'])
def load(load_hash, load_filename):
    # validate supplied parameters
    if not load_hash or not len(load_hash):
        log.error("Invalid hash provided in load request from %s", request.environ.get('REMOTE_ADDR'))
        return json_response('Invalid hash provided', True)
    if not load_filename or not len(load_filename):
        log.error("Invalid filename in load request from %s", request.environ.get('REMOTE_ADDR'))
        return json_response('Invalid filename provided', True)

    # validate filename was an allowed filename
    secured_filename = os.path.basename(secure_filename(load_filename)).lower()
    if secured_filename not in cfg.config['uploads']['allowed_files']:
        log.error("Unsupported filename in load request from %s for %r", request.environ.get('REMOTE_ADDR'),
                  secured_filename)
        return json_response('Unsupported filename provided', True)

    # set secured variables
    secured_load_hash = secure_filename(load_hash)
    secured_load_directory = os.path.join(cfg.config['uploads']['upload_folder'], secured_load_hash)
    secured_load_filepath = os.path.join(secured_load_directory, secured_filename)

    try:
        # does file exist?
        if not os.path.exists(secured_load_filepath):
            log.error("Load request from %s for %r by %s did not exist at %r", request.environ.get('REMOTE_ADDR'),
                      secured_filename, secured_load_hash, secured_load_filepath)
            return json_response('%s was missing' % secured_filename, True), 404

        log.info("Load request from %s for %r by %s", request.environ.get('REMOTE_ADDR'), secured_filename,
                 secured_load_hash)
        return send_from_directory(secured_load_directory, secured_filename)

    except Exception:
        log.exception("Unexpected exception with load request from %s for %s with filename %r: ",
                      request.environ.get('REMOTE_ADDR'), secured_load_hash, secured_filename)

    return json_response('Failed unexpectedly while loading %s' % secured_filename, True)


@app.route('/save/<save_hash>/<save_filename>', methods=['POST'])
def save(save_hash, save_filename):
    # validate supplied parameters
    if not save_hash or not len(save_hash):
        log.error("Invalid hash provided in save request from %s", request.environ.get('REMOTE_ADDR'))
        return json_response('Invalid hash provided', True)
    if not save_filename or not len(save_filename):
        log.error("Invalid filename in save request from %s", request.environ.get('REMOTE_ADDR'))
        return json_response('Invalid filename provided', True)

    # validate filename was an allowed filename
    secured_filename = os.path.basename(secure_filename(save_filename)).lower()
    if secured_filename not in cfg.config['uploads']['allowed_files']:
        log.error("Unsupported filename in save request from %s for %r", request.environ.get('REMOTE_ADDR'),
                  secured_filename)
        return json_response('Unsupported filename provided', True)

    # set secured variables
    secured_save_hash = secure_filename(save_hash)
    secured_save_filepath = os.path.join(cfg.config['uploads']['upload_folder'], secured_save_hash, secured_filename)

    # retrieve file
    try:
        if 'file' not in request.files:
            log.error("Save request from %s for %s had no file attached...", request.environ.get('REMOTE_ADDR'),
                      secured_save_hash)
            return json_response('No file was attached to the save request', True)

        # there is a file, lets read it
        file = request.files['file']
        # validate filename
        if file.filename == '':
            return json_response('Invalid file was attached', True)

        log.info("Save request from %s for %r by %s to %r", request.environ.get('REMOTE_ADDR'), secured_filename,
                 secured_save_hash, secured_save_filepath)

        # create directories
        try:
            os.makedirs(os.path.dirname(secured_save_filepath))
        except FileExistsError:
            pass
        except Exception:
            log.exception("Exception with save request from %s while creating upload folder %r",
                          request.environ.get('REMOTE_ADDR'), os.path.dirname(secured_save_filepath))
            return json_response('Failed unexpectedly while saving %s' % secured_filename, True)

        # save file
        file.save(secured_save_filepath)
        return json_response('Successfully saved %s' % secured_filename)

    except RequestEntityTooLarge:
        log.error(
            "Exception with save request from %s for %s with filename %r, the file was too large...",
            request.environ.get('REMOTE_ADDR'), secured_save_hash, secured_filename)
        return json_response('File was too large to be saved', True)
    except Exception:
        log.exception("Unexpected exception with save request from %s for %s with filename %r: ",
                      request.environ.get('REMOTE_ADDR'), secured_save_hash, secured_filename)

    return json_response('Failed unexpectedly while saving %s' % secured_filename, True)


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
