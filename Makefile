.PHONY: clean run-dev run-prod test

# Note: pass PYTHON=XXX to override.
PYTHON ?= python2.7

default: venv

venv:
#	virtualenv --python python2.7 venv
	virtualenv --python ${PYTHON} venv
	venv/bin/pip install --requirement requirements.txt
	venv/bin/python create_db.py

run-dev: venv
	FLASK_ENV=DEVELOPMENT venv/bin/python -m app

run-prod: venv
	FLASK_ENV=PRODUCTION venv/bin/python -m app

test: venv
	FLASK_ENV=TESTING venv/bin/py.test tests/test*

clean:
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -delete
	rm -r venv
