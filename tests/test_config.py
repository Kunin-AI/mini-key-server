# -*- coding: utf-8 -*-
"""Test configs."""
from kunin.app import create_app
from kunin.settings import DevConfig, ProdConfig


def test_production_config():
    """Production config."""
    app = create_app(ProdConfig)
    assert app.config['ENV'] == 'prod'
    assert not app.config['DEBUG']
    assert app.config['SQLALCHEMY_BINDS'] and app.config['SQLALCHEMY_BINDS']['staff_data'] == 'sqlite://yoda.db'


def test_dev_config():
    """Development config."""
    app = create_app(DevConfig)
    assert app.config['ENV'] == 'dev'
    assert app.config['DEBUG']
    assert app.config['SQLALCHEMY_BINDS'] and app.config['SQLALCHEMY_BINDS']['staff_data']
