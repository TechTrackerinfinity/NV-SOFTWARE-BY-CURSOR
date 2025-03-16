import os
from . import create_app

# Get the environment from the FLASK_ENV environment variable, defaulting to 'development'
env = os.environ.get('FLASK_ENV', 'development')
app = create_app(env)

if __name__ == '__main__':
    # Run the app in debug mode if we're in development
    debug = env == 'development'
    app.run(debug=debug) 