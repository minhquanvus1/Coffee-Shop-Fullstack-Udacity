import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS
import redis
from typing import List, Dict, Union, Any
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


# Initialize Redis connection
redis_client = redis.Redis(host='localhost', port=6379, db=0)
EXPIRATION_TIME = 300  # 5 minutes

def set_to_redis(key: str, expiration_time: int, value: Any):
    redis_client.setex(key, expiration_time, value)
def get_from_redis(key: str):
    return redis_client.get(key)

@app.route('/reset-db', methods=['POST'])
def reset_db():
    db_drop_and_create_all()
    redis_client.flushall()
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
    # Check if the data is cached in Redis
    cached_drinks = get_from_redis('drinks')
    print(f'cached_drinks', cached_drinks)
    print(type(cached_drinks))
    return_list = []
    if cached_drinks:
        print('from cache')
        cached_drinks_list: List[Dict[str, Any]] = json.loads(cached_drinks)
        print(type(cached_drinks_list))
        print(f'cached_drinks_list', cached_drinks_list)
        print(type(cached_drinks_list[0]))
        print(f'cached_drinks_list[0]', cached_drinks_list[0])
        # convert the list of dict to list of Drink instances
        cached_drinks_list = [Drink(**drink) for drink in cached_drinks_list]
        drink_not_in_cache_list = []
        
        # for drink_in_db in Drink.query.all():
        #     if drink_in_db.id not in [drink.id for drink in cached_drinks_list]:
        #         drink_not_in_cache_list.append(drink_in_db)
        drink_not_in_cache_list: List[Drink] = Drink.query.filter(~Drink.id.in_([drink.id for drink in cached_drinks_list])).all()
        print(f'drink_not_in_cache_list', drink_not_in_cache_list)
        if len(drink_not_in_cache_list) > 0:
            return_list: List[Drink] = [*drink_not_in_cache_list, *cached_drinks_list]
            set_to_redis('drinks', EXPIRATION_TIME, json.dumps([drink.short() for drink in return_list])) # Cache for 5 minutes
        else:
            return_list: List[Drink] = cached_drinks_list
        # If cached data exists, return it
        print(type(return_list))
        print(f'return_list', return_list)
        print(type(return_list[0]))
        print(f'return_list[0]', return_list[0])
        print(f'return_list[0]["recipe"]', return_list[0].recipe)
        
        return_list = [drink.short() for drink in return_list]
        return jsonify({"success": True, "drinks": return_list}), 200    
    list_of_all_drinks: List[Drink] = Drink.query.all()
    if len(list_of_all_drinks) == 0:
        abort(404)
    drinks = [drink.short() for drink in list_of_all_drinks]
    # Cache the data in Redis for future use
    set_to_redis('drinks', EXPIRATION_TIME, json.dumps(drinks)) # Cache for 5 minutes
    
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
    
    cached_drinks_detail = get_from_redis('drinks-detail')
    if cached_drinks_detail:
        print('from cache')
        print(type(cached_drinks_detail))
        print(type(cached_drinks_detail.decode('utf-8')))
        print(json.loads(cached_drinks_detail.decode('utf-8')))
        print(type(json.loads(cached_drinks_detail.decode('utf-8'))[0]))
        print(json.loads(cached_drinks_detail.decode('utf-8'))[0])
        print(type(json.loads(cached_drinks_detail)[0]['recipe']))
        print(json.loads(cached_drinks_detail)[0]['recipe'])
        #print(Drink(**json.loads(cached_drinks_detail.decode('utf-8'))[0]))
        drink_obj: Drink = Drink(**json.loads(cached_drinks_detail.decode('utf-8'))[0])
        print(type(drink_obj))
        print(type(drink_obj.recipe))
        return jsonify({"success": True, "drinks": json.loads(cached_drinks_detail)}), 200
    
    list_of_all_drinks = Drink.query.all()
    print(len(list_of_all_drinks))
    print('list_of_all_drinks', list_of_all_drinks)
    for drink in list_of_all_drinks:
        print(type(drink))
        print(type(drink.recipe))
    if len(list_of_all_drinks) == 0:
        abort(404)
    drinks = [drink.long() for drink in list_of_all_drinks]
    set_to_redis('drinks-detail', EXPIRATION_TIME, json.dumps(drinks)) # Cache for 5 minutes
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
    body_in_json_string: str = request.get_data()
    body_in_dict = json.loads(body_in_json_string)
    processable_request_body = validate_and_return_processable_request_body(body_in_dict)
    
    new_drink = Drink(**processable_request_body) # **body_in_dict is the same as title=body_in_dict['title'], recipe=body_in_dict['recipe'] - unpack the dictionary into keyword arguments
    list_of_drinks_with_the_same_title = list(filter(lambda drink: drink.title.lower() == new_drink.title.lower(), Drink.query.all()))
    if len(list_of_drinks_with_the_same_title) > 0:
        abort(422, description='title must be unique')
    new_drink.insert()
    
    # Retrieve the existing list of drinks from the cache
    cached_drinks = redis_client.get('drinks')
    drinks_instances = []
    if cached_drinks:
        drinks: List[Dict[str, Any]] = json.loads(cached_drinks) # list of Python dict, not list of Drink instances
        drinks_instances: List[Drink] = [Drink(**drink_data) for drink_data in drinks]
        #print(f'drinks 1', drinks[0])
    # Append the newly created drink to the list
    drinks_instances.append(new_drink)  # Replace new_drink_data with actual data
    print(f'drinks_instances', drinks_instances)
    print(f'drinks_instances 1st', drinks_instances[0])

    drinks_json = list(map(lambda drink: drink.short(), drinks_instances))

    # Set the updated list back into the cache
    set_to_redis('drinks', EXPIRATION_TIME, json.dumps(drinks_json)) # Cache for 5 minutes
    
    cached_drinks_detail = redis_client.get('drinks-detail')
    drinks_detail_instances = []
    if cached_drinks_detail:
        drinks_detail: List[Dict[str, Any]] = json.loads(cached_drinks_detail)
        drinks_detail_instances: List[Drink] = [Drink(**each_drink_detail) for each_drink_detail in drinks_detail]

    # Append the newly created drink to the list
    drinks_detail_instances.append(new_drink)  # Replace new_drink_data with actual data
    drinks_detail_json = list(map(lambda drink: drink.long(), drinks_detail_instances))
    # Set the updated list back into the cache
    set_to_redis('drinks-detail', EXPIRATION_TIME, json.dumps(drinks_detail_json)) # Cache for 5 minutes
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
    requested_drink: Union[Drink, None] = Drink.query.filter(Drink.id == drink_id).one_or_none()
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
    cached_data = get_from_redis('drinks')
    if cached_data:
        drinks = json.loads(cached_data)
        # changed_drinks = list(filter(lambda drink: drink['id'] == drink_id, drinks))
        # changed_drinks[0] = requested_drink
        for drink in drinks:
            if drink['id'] == drink_id:
                drink.update(requested_drink.short())
                #drink = changed_drinks[0].short() # This doesn't work, because drink is a copy of the original drink, not the original drink itself. by which I mean that drink is a new object, not the original object, so changing drink doesn't change the original object. To solve this, we can use the index of the original drink in the list of drinks to change the original drink
        set_to_redis('drinks', EXPIRATION_TIME, json.dumps(drinks))
    
    cached_data_detail = get_from_redis('drinks-detail')
    if cached_data_detail:
        drinks_details = json.loads(cached_data_detail)
        
        for drinks_detail in drinks_details:
            if drinks_detail['id'] == drink_id:
                drinks_detail.update(requested_drink.long())
                #drink = changed_drinks_detail[0].long()
        set_to_redis('drinks-detail', EXPIRATION_TIME, json.dumps(drinks_details))
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
    
    # Check if the resource is present in the cache
    cached_drinks = redis_client.get('drinks')
    if cached_drinks:
        drinks = json.loads(cached_drinks)
        # Remove the deleted drink from the cached list
        #drinks = [drink for drink in drinks if drink['id'] != drink_id]
        drinks = list(filter(lambda drink: drink['id'] != drink_id, drinks))
        # Set the updated list back to the cache
        set_to_redis('drinks', EXPIRATION_TIME, json.dumps(drinks)) # Cache for 5 minutes
    
    # Check if the resource is present in the cache
    cached_drinks_detail = redis_client.get('drinks-detail')
    if cached_drinks_detail:
        drinks_detail = json.loads(cached_drinks_detail)
        # Remove the deleted drink from the cached list
        
        drinks_detail = list(filter(lambda drink: drink['id'] != drink_id, drinks_detail))
        # Set the updated list back to the cache
        set_to_redis('drinks-detail', EXPIRATION_TIME, json.dumps(drinks_detail)) # Cache for 5 minutes
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