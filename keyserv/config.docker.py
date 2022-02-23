# adjust the Config class below, then rename this file to config.py
import os


class DefaultConfig(object):
    # a decent way to generate a secret key is by running: python -c "import os; print(repr(os.urandom(24)))"
    # then pasting the output here.
    SECRET_KEY = os.environ['SECRET_KEY']

    DEBUG = False
    TESTING = False

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///data/sqlite.db"


class ProductionConfig(DefaultConfig):
    SQLALCHEMY_DATABASE_URI = "sqlite:////data/sqlite.db"

class DevelopmentConfig(ProductionConfig):
    DEBUG = True
    TESTING = True
    SQLALCHEMY_TRACK_MODIFICATIONS = True
