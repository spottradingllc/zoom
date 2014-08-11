require(['sammyApp', 'viewModel/loginViewModel', 'viewModel/applicationStateViewModel'],
function(sammyApp, loginViewModel, applicationStateViewModel) {

    var app = sammyApp.initialize();

//    app.get('#/login', loginViewModel.login);
    app.get('#/application_state', applicationStateViewModel.application_state);
//    app.get('#/serverConfig');

    return app.run('#/application_state');
});