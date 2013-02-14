from flask.ext.script import Manager, Server

from yelandur import create_app


manager = Manager(create_app())


class RunServer(Server):

    def handle(self, app, *args, **kwargs):
        app.run(host=app.config['HOST'])


manager.add_command('runserver', RunServer())


if __name__ == "__main__":
    manager.run()
