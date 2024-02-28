## Coffee Shop Backend

- The backend uses Flask, SQLAlchemy, and a SQLite database.
- The backend is set up to use Auth0 for authentication.
- The backend is set up to use RBAC for authorization.
- Additionally, I also use Redis for caching to improve the performance of the backend.

## Getting Started

- Because the backend uses Python 3.7 for the virtual environment, you need to install Python 3.7 to set up a virtual environment.
- Install Redis database: [Redis Quick Start](https://redis.io/topics/quickstart)
- Install Python 3.7: [Python 3.7](https://www.python.org/downloads/release/python-370/)

### Installing Dependencies

- After installing Python 3.7, Redis, we can create a virtual environment and install the dependencies:

```bash

# Windows users

cd backend
virtuallenv my_venv --python=python3.7
./env/Scripts/activate

```

- **Install Dependencies**

```bash
pip install -r requirements.txt
```

- **Run the development server**

```bash
# Windows Powershell users:
cd backend/src
$env:FLASK_APP = "api.py"
flask run --reload
```

The backend Flask application will run on `http://127.0.0.1:5000/` by default and is a proxy in the frontend configuration.

- To deactivate the virtual environment, run:

```bash
deactivate
```

- The Redis server needs to be run in the Linux environment (you can use WSL for Windows users) by running the following command:

```bash
redis-server
```

- To start the Redis CLI, run the following command:

```bash
redis-cli
```

- The Redis server will run on `http://localhost:6379/` by default.

- Note: The Redis server is not required to run the backend server. It is only used for caching to improve the performance of the backend.

- Now when you run the Frontend and send the API request to the backend, the Redis server will cache the response and improve the performance of the backend. Therefore, the response time will be faster than without the Redis server.

- For Role-Based Access Control (RBAC), I create 2 users, Barista, and Manager, respectively. The Barista user can only perform `get:drinks` and `get:drinks-detail` actions, while the Manager user can perform all actions.
- when we register the new user, they will have NO role. We need to assign the role to the user manually in the Auth0 dashboard.

- To view data in the SQLite database, you can use the SQLite browser to open the `database.db` file in the `backend/src` directory.
- Or, you can use the following command to view the data in the SQLite database:

```bash
cd backend/src/database
sqlite3 database.db
```

- Notice that I use the same database for both the development and testing environment. Therefore, when you run the test, the data in the database will be changed. Therefore, I have added the `POST /reset_db` endpoint in the `Redis-coffee-shop-udacity-fsnd-udaspicelatte.postman_collection.json` Postman collection to reset the database, and clear the Redis cache after the Collection's Test to ensure the test is independent of each other.

- For API Test with Postman, you can import the `Redis-coffee-shop-udacity-fsnd-udaspicelatte.postman_collection.json` file in the root directory of the backend folder to test the API.
- I have also included the result of the API test in the `Redis-coffee-shop-udacity-fsnd-udaspicelatte.postman_test_run.json` file in the root directory of the backend folder.
