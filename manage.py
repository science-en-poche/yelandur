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

    page_size = 10000
    results = Result.objects
    n_results = results.count()
    pages_indices = range(1 + n_results / page_size)
    print "Exporting results to 'results-{{{}}}.json'".format(
        ', '.join(pages_indices))
    for i in pages_indices:
        results_range = results[i*page_size:(i+1)*page_size]
        with open('results-{}.json'.format(i), 'w') as r:
            json.dump({'results': results_range.to_jsonable_private()},
                      r, indent=2, separators=(',', ': '))


if __name__ == "__main__":
    manager.run()
