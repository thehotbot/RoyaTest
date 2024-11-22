import os
import logging
from main import app, find_available_port

if __name__ == "__main__":
    # Configure basic logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Get port configuration
    default_port = int(os.environ.get('PORT', 5000))
    port = find_available_port(default_port)
    
    logger.info(f"Starting server on port {port}")
    
    try:
        app.run(
            host='0.0.0.0',
            port=port,
            debug=False,
            use_reloader=False,
            threaded=True,
            max_content_length=16 * 1024 * 1024  # 16MB max content length
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        app.logger.error(f"Application error: {e}")
        raise
