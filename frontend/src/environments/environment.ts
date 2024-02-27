/* @TODO replace with your variables
 * ensure all variables on this page match your project
 */

export const environment = {
  production: false,
  apiServerUrl: 'http://127.0.0.1:5000', // the running FLASK api server url
  auth0: {
    url: 'dev-tioi4bnfisc6bcli.us', // the auth0 domain prefix
    audience: 'https://coffeeShop/api', // the audience set for the auth0 app
    clientId: 'SMw7PxBz1yJGmCquqfVmi4kqUAzWtgGz', // the client id generated for the auth0 app
    callbackURL: 'http://localhost:8100', // the base url of the running ionic application. 
  }
};
