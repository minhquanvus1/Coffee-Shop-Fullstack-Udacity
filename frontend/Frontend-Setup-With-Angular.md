## Coffee Shop Frontend

- The frontend uses Angular, Ionic, and TypeScript.
- The frontend is set up to use Auth0 for authentication.
- The frontend is set up to use RBAC for authorization.

## Frontend Setup'

- Because the frontend uses Angular and Ionic, you need to install Node.js, npm, and Ionic CLI to set up the frontend environment, as referred by the readme in the frontend/ folder: [View the README.md within ./frontend for more details.](./frontend/README.md)

## Run the Frontend

- Before running the frontend, we need to use this command to solve the error of `Digital Envelope routines: EVP_DecryptFinal_ex:wrong final block length` in Node.js 16.0.0+ versions. Run the following command in the terminal to solve the error:

  ```bash
  $env:NODE_OPTIONS = "--openssl-legacy-provider"
  ```

- After that, to run the frontend app, you need to run the following commands:
  ```bash
  cd frontend
  npm install
  ionic serve
  ```
- Notice that: if you install Ionic CLI globally, you can run `ionic serve` directly. Otherwise, you need to run `npx ionic serve`.
- The frontend app will be running on `http://localhost:8100/`.

- This is the GitHub repository for the entire project: [Coffee Shop Full Stack](https://github.com/minhquanvus1/Coffee-Shop-Fullstack-Udacity/tree/main)
