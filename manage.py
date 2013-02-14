from flask.ext.script import Manager, Server

from yelandur import create_app


manager = Manager(create_app)
manager.add_option('-m', '--mode', dest='mode', default='dev',
                   required=False)

class RunServer(Server):

    def handle(self, app, *args, **kwargs):
        app.run(host=app.config['HOST'])


manager.add_command('runserver', RunServer())


if __name__ == "__main__":
    manager.run()
