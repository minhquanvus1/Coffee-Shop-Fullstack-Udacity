import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
'''
#db_drop_and_create_all()

# ROUTES
'''
@TODO implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks', methods=['GET'])
def get_drinks():
    list_of_all_drinks = Drink.query.all()
    if len(list_of_all_drinks) == 0:
        abort(404)
    drinks = [drink.short() for drink in list_of_all_drinks]
    return jsonify({"success": True, "drinks": drinks}), 200

'''
@TODO implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drinks_detail(token):
    list_of_all_drinks = Drink.query.all()
    if len(list_of_all_drinks) == 0:
        abort(404)
    drinks = [drink.long() for drink in list_of_all_drinks]
    return jsonify({"success": True, "drinks": drinks}), 200

'''
@TODO implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''

def validate_and_return_processable_request_body(request_body):
    if not isinstance(request_body, dict):
        abort(422)
    if not all(key in request_body for key in ['title', 'recipe']):
        abort(422)
    recipe = request_body['recipe']
    if recipe is None:
        abort(422)
    if not all(key in request_body for key in ['color', 'name', 'parts']) and not all(isinstance(key, str) in recipe for key in ['color', 'name', 'parts']):
        abort(422)
    if isinstance(recipe, dict):
        recipe = [recipe]
    request_body['recipe'] = json.dumps(request_body['recipe'])
    return request_body

@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drink(token):
    body_in_json_string = request.get_data()
    body_in_dict = json.loads(body_in_json_string)
    processable_request_body = validate_and_return_processable_request_body(body_in_dict)
    
    new_drink = Drink(**processable_request_body) # **body_in_dict is the same as title=body_in_dict['title'], recipe=body_in_dict['recipe'] - unpack the dictionary into keyword arguments
    new_drink.insert()
    return jsonify({"success": True, "drinks": [new_drink.long()]}), 200

'''
@TODO implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''


'''
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''


# Error Handling
'''
Example error handling for unprocessable entity
'''


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


'''
@TODO implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False,
                    "error": 404,
                    "message": "resource not found"
                    }), 404

'''

'''
@TODO implement error handler for 404
    error handler should conform to general task above
'''


'''
@TODO implement error handler for AuthError
    error handler should conform to general task above
'''
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)