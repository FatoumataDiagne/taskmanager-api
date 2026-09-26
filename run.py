import os
from app import create_app

app = create_app(os.environ.get('FLASK_CONFIG', 'dev'))

if __name__ == '__main__':
    app.run()
