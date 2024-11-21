# Gunicorn configuration file
import multiprocessing
import os
from datetime import datetime

# Server socket
bind = "0.0.0.0:5000"

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'
worker_connections = 1000

# Timeouts
timeout = 120
graceful_timeout = 120
keepalive = 5

# Worker settings
max_requests = 1000
max_requests_jitter = 50
# Removed worker_tmp_dir as it's not needed in Replit environment
preload_app = True
worker_class = 'sync'  # Using sync worker for better compatibility
workers = 2  # Limiting workers for Replit environment

# Logging
accesslog = 'logs/gunicorn_access.log'
errorlog = 'logs/gunicorn_error.log'
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(L)s'

# Create logs directory if it doesn't exist
import os
os.makedirs('logs', exist_ok=True)

logconfig_dict = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(process)d] [%(levelname)s] %(name)s: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S %z'
        },
        'access': {
            'format': '%(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S %z'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout'
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'standard',
            'filename': 'logs/gunicorn_error.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
            'level': 'ERROR'
        },
        'access_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'access',
            'filename': 'logs/gunicorn_access.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10
        }
    },
    'loggers': {
        '': {
            'handlers': ['console', 'error_file'],
            'level': 'INFO',
        },
        'gunicorn.access': {
            'handlers': ['console', 'access_file'],
            'level': 'INFO',
            'propagate': False
        },
        'gunicorn.error': {
            'handlers': ['console', 'error_file'],
            'level': 'INFO',
            'propagate': False
        }
    }
}

# Process naming
proc_name = 'sms-simulator'

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Reload strategy
reload_engine = 'auto'
reload_extra_files = []

# SSL (configured through environment variables in production)
keyfile = os.getenv('SSL_KEYFILE', None)
certfile = os.getenv('SSL_CERTFILE', None)

# Security
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190
forwarded_allow_ips = '*'

# Server hooks
def on_starting(server):
    """Log when the server starts."""
    server.log.info(f"Starting server at {datetime.now()}")

def worker_int(worker):
    """Log when a worker dies."""
    worker.log.info(f"Worker {worker.pid} received INT signal")

def worker_abort(worker):
    """Log when a worker is aborted."""
    worker.log.info(f"Worker {worker.pid} aborted")
