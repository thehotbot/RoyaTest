import os
import logging
from logging.handlers import RotatingFileHandler
from flask import request, has_request_context
from datetime import datetime

class RequestFormatter(logging.Formatter):
    def format(self, record):
        if has_request_context():
            record.url = request.url
            record.remote_addr = request.remote_addr
            record.method = request.method
        else:
            record.url = None
            record.remote_addr = None
            record.method = None
        return super().format(record)

def setup_logging(app):
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Configure formatters
    console_formatter = RequestFormatter(
        '%(asctime)s - %(levelname)s - [%(remote_addr)s] %(method)s %(url)s - %(message)s'
    )
    file_formatter = RequestFormatter(
        '%(asctime)s - %(levelname)s - [%(remote_addr)s] %(method)s %(url)s - %(message)s\n'
        'Path: %(pathname)s:%(lineno)d\n'
        'Function: %(funcName)s\n'
    )

    # Configure handlers
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)

    # Rotating file handler for application logs
    app_handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    app_handler.setFormatter(file_formatter)
    app_handler.setLevel(logging.INFO)

    # Error log handler
    error_handler = RotatingFileHandler(
        'logs/error.log',
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    error_handler.setFormatter(file_formatter)
    error_handler.setLevel(logging.ERROR)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(app_handler)
    root_logger.addHandler(error_handler)

    # Configure Flask app logger
    app.logger.setLevel(logging.INFO)
    for handler in root_logger.handlers:
        app.logger.addHandler(handler)

    # Log application startup
    app.logger.info(f"Application started at {datetime.now().isoformat()}")
    app.logger.info(f"Environment: {os.getenv('FLASK_ENV', 'production')}")

class RequestLoggingMiddleware:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        import logging
        logger = logging.getLogger('request')
        
        path = environ.get('PATH_INFO')
        method = environ.get('REQUEST_METHOD')
        remote_addr = environ.get('REMOTE_ADDR')
        
        logger.info(
            f"Request: {method} {path} - Client: {remote_addr}"
        )
        
        return self.wsgi_app(environ, start_response)
