from informatics_classroom import create_app
from informatics_classroom.config import Config

app=create_app()
app.config.from_object(Config)
#print(app.config)

if __name__ == '__main__':
    app.run()