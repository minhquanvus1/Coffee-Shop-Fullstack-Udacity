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
db_drop_and_create_all()


@app.route('/reset-db', methods=['POST'])
def reset_db():
    db_drop_and_create_all()
    return jsonify({"success": True, "message": "database reset successfully"}), 200
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
def get_drinks_detail(payload):
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

def validate_recipe(recipe: list):
    
    
    for each_recipe in recipe:
        if not all(key in each_recipe for key in ['color', 'name', 'parts']):
            abort(422, description='recipe must contain "color", "name", and "parts"')
        if not isinstance(each_recipe['color'], str) or each_recipe['color'] == '':
            abort(422, description='color must be a non-empty string')
        if not isinstance(each_recipe['name'], str) or each_recipe['name'] == '':
            abort(422, description='name must be a non-empty string')
        if not isinstance(each_recipe['parts'], (int, float)) or each_recipe['parts'] <= 0:
            abort(422, description='parts must be a positive number')

def validate_and_return_processable_request_body(request_body: dict) -> dict:
    if not isinstance(request_body, dict):
        abort(422, description='request body must be a dictionary')
    if not all(key in request_body for key in ['title', 'recipe']):
        abort(422, description='request body must contain "title" and "recipe"')
    if not isinstance(request_body['title'], str) or request_body['title'] == '':
        abort(422, description='title must be a non-empty string')
    recipe = request_body['recipe']
    if recipe is None:
        abort(422, description='recipe must be provided')
    
    if isinstance(recipe, dict):
        recipe = [recipe]
    validate_recipe(recipe)
    request_body['recipe'] = json.dumps(recipe)
    return request_body

@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drink(payload):
    body_in_json_string = request.get_data()
    body_in_dict = json.loads(body_in_json_string)
    processable_request_body = validate_and_return_processable_request_body(body_in_dict)
    
    new_drink = Drink(**processable_request_body) # **body_in_dict is the same as title=body_in_dict['title'], recipe=body_in_dict['recipe'] - unpack the dictionary into keyword arguments
    list_of_drinks_with_the_same_title = list(filter(lambda drink: drink.title.lower() == new_drink.title.lower(), Drink.query.all()))
    if len(list_of_drinks_with_the_same_title) > 0:
        abort(422, description='title must be unique')
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
@app.route('/drinks/<int:drink_id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(payload, drink_id):
    requested_drink = Drink.query.filter(Drink.id == drink_id).one_or_none()
    if requested_drink is None:
        abort(404)
    try:
        request_body = request.get_json()
        print(request_body)
    except:
        abort(400, description='request body must be in JSON format')
    
    if 'title' in request_body:
        title = request_body.get('title', None)
        if title is None or not isinstance(title, str) or title == '':
            abort(422, description='title must be a non-empty string, and must be provided')
        # if title.lower() == requested_drink.title.lower():
        #     abort(422, description='title must be different from the current title')
        list_of_existing_titles = [drink.title.lower() for drink in Drink.query.filter(Drink.id != requested_drink.id).all()]
        if title.lower() in list_of_existing_titles:
            abort(422, description='title must be unique')
        requested_drink.title = title
        
    if 'recipe' in request_body:
        recipe = request_body['recipe']
        if recipe is None:
            abort(422, description='recipe must be provided')
        if isinstance(recipe, dict):
            recipe: list = [recipe]
        validate_recipe(recipe)
        requested_drink.recipe = json.dumps(recipe)
    requested_drink.update()
    return jsonify({"success": True, "drinks": [requested_drink.long()]}), 200
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
@app.route('/drinks/<int:drink_id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(payload, drink_id):
    requested_drink = Drink.query.filter_by(id=drink_id).one_or_none()
    if requested_drink is None:
        abort(404)
    requested_drink.delete()
    return jsonify({"success": True, "delete": drink_id}), 200

# Error Handling
'''
Example error handling for unprocessable entity
'''


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": error.description
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
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
    }), 404

@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({
        "success": False,
        "error": 500,
        "message": "internal server error"
    }), 500

@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": error.description
    }), 400


'''
@TODO implement error handler for AuthError
    error handler should conform to general task above
'''
@app.errorhandler(AuthError)
def auth_error(error):
    print('from autherror')
    return jsonify({
        "success": False,
        "error": error.status_code,
        "message": error.error['description']
    }), error.status_code

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)