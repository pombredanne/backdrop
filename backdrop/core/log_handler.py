from logging import FileHandler
from logstash_formatter import LogstashFormatter
import logging
from flask import request


def get_log_file_handler(path, log_level=logging.DEBUG):
    handler = FileHandler(path)
    handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] -> %(message)s"))
    handler.setLevel(log_level)
    return handler


def get_json_log_handler(path):
    handler = FileHandler(path)
    formatter = LogstashFormatter()
    formatter.defaults['@tags'] = ['application']
    handler.setFormatter(formatter)
    return handler


def set_up_logging(app, name, env):
    log_level = logging._levelNames[app.config['LOG_LEVEL']]
    app.logger.addHandler(
        get_log_file_handler("log/%s.log" % env, log_level)
    )
    app.logger.addHandler(
        get_json_log_handler("log/%s.log.json" % env)
    )
    app.logger.setLevel(log_level)
    app.logger.info("Backdrop %s API logging started" % name)


def create_request_logger(app):
    def log_request():
        app.logger.info("request: %s - %s" % (request.method, request.url))
    return log_request


def create_response_logger(app):
    def log_response(response):
        app.logger.info(
            "response: %s - %s - %s" % (
                request.method, request.url, response.status
            )
        )
        return response
    return log_response
