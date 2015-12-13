"""This is the entry point for running the ladder service API.

The app will be configured to run in a particular environment, specified by the
`FLASK_ENV` environment variable.
"""

from app import create_app
app = create_app()
app.run(port=app.config['PORT'], debug=app.config['DEBUG'])
