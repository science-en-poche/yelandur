# -*- coding: utf-8 -*-

from flask import Blueprint


# Create the actual blueprint
exps = Blueprint('exps', __name__)


#class ExpsView(MethodView):

    #@cors()
    #def get(self, login):
        #u = User.objects.get(login=login)
        #exps = Exp.objects(owner=u)

        #if current_user.is_authenticated() and current_user == u:
            #return jsonify(exps.to_jsonable_private())
        #else:
            #return jsonify(exps.to_jsonable())

    #@login_required
    #@cors()
    #def post(self, login):
        #u = User.objects.get(login=login)

        #if current_user == u:
            #name = request.json.get('name') or request.json.get('name_claim')
            #description = request.json.get('description')
            ## Errors generated here are caught by errorhandlers, see below
            #e = Exp.create(name, u, description)
            #e.save()
            #return jsonify(e.to_jsonable_private()), 201
        #else:
            ## User not authorized
            #abort(403)

    #@cors()
    #def options(self, login):
        #pass


#users.add_url_rule('/<login>/exps/', view_func=ExpsView.as_view('exps'))


#class ExpView(MethodView):

    #@cors()
    #def get(self, login, name):
        #u = User.objects.get(login=login)
        #e = Exp.objects(owner=u).get(name=name)

        #if (current_user.is_authenticated() and
                #(current_user == e.owner or current_user in e.collaborators)):
            #return jsonify(e.to_jsonable_private())
        #else:
            #return jsonify(e.to_jsonable())

    #@cors()
    #@login_required
    #def put(self, login, name):
        #u = User.objects.get(login=login)
        #e = Exp.objects(owner=u).get(name=name)

        #if current_user == e.owner or current_user in e.collaborators:
            #if name != request.json['name']:
                #abort(400)
            #e.description = request.json['description']
            #e.save()
            #return jsonify(e.to_jsonable_private())
        #else:
            ## User not authorized
            #abort(403)

    #@cors()
    #def options(self, login, name):
        #pass


#users.add_url_rule('/<login>/exps/<name>', view_func=ExpView.as_view('exp'))


#@users.route('/<login>/exps/<name>/results/')
#@cors()
#@login_required
#def results(login, name):
    ## No POST method here since results are added by devices only
    #u = User.objects.get(login=login)
    #e = Exp.objects(owner=u).get(name=name)

    #if current_user == e.owner or current_user in e.collaborators:
        #return jsonify(e.to_jsonable_private('results'))
    #else:
        #abort(403)
