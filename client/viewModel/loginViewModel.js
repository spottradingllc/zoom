define(['service', 'sammyApp', 'model/loginModel'],
function(service, sammyApp, loginModel) {

    var viewModel;
    viewModel = function () {

        var model;
        model = {};


        model.login = loginModel.model();


        model.reset = function () {
            return loginModel.model().reset();
        };


        model.submit = function () {
            var self = this;

            var params = { username: self.login.elements.username(), password: self.login.elements.password() };

            return loginModel.model().submit(params);
        };


        return model;
    };


    return {
        login: function (context) {
            context.view = "login";
            return context.viewModel = viewModel();
        }
    };
});