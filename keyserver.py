import os

from keyserv import create_app

if os.environ.get("FLASK_DEBUG"):
    print('<', '='*20, 'DEVELOPMENT', '='*20, '>')
    app = create_app('DevelopmentConfig')
else:
    print('<', '='*20, 'PRODUCTION', '='*20, '>')
    app = create_app('ProductionConfig')

if __name__ == '__main__':
    app.run()
