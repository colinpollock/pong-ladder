from app.models import db
from app.app import create_app

app = create_app()

context = app.app_context()
context.push()
db.create_all()
