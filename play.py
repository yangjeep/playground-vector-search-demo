from getpass import getuser
from firexapp.engine.celery import app

@app.task()
def greet(name=getuser()):
    return 'Hello %s!' % name
