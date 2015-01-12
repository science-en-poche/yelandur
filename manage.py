# -*- coding: utf-8 -*-

import json

from flask.ext.script import Manager

from yelandur import create_app


manager = Manager(create_app)
manager.add_option('-m', '--mode', dest='mode', default='dev',
                   required=False)


@manager.command
def export_results(*args, **kwargs):
    from yelandur.models import Profile, Result

    print "Exporting profiles to 'profiles.json'"
    with open('profiles.json', 'w') as p:
        json.dump({'profiles': Profile.objects.to_jsonable_private()},
                  p, indent=2, separators=(',', ': '))

    print "Exporting results to 'results.json'"
    with open('results.json', 'w') as r:
        json.dump({'results': Result.objects.to_jsonable_private()},
                  r, indent=2, separators=(',', ': '))


if __name__ == "__main__":
    manager.run()
