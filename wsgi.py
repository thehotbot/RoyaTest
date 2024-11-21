import os
from main import app, find_available_port

if __name__ == "__main__":
    default_port = int(os.environ.get('PORT', 5000))
    port = find_available_port(default_port)
    
    try:
        app.run(
            host='0.0.0.0',
            port=port,
            debug=False,
            use_reloader=False
        )
    except Exception as e:
        app.logger.error(f"Failed to start server: {e}")
        raise
