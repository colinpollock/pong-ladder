
from app.app import create_app
from app.models import db


class BaseFlaskTest(object):
    @classmethod
    def setup_class(cls):
        cls.app = create_app()
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        db.create_all()

    @classmethod
    def teardown_class(cls):
        cls.app_context.pop()
