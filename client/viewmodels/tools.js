define(
    [
        'durandal/app',
        'knockout',
        'service',
        'jquery',
        'model/toolsModel',
        'model/loginModel',
        'bindings/radio',
        'bindings/tooltip'
    ],
    function(app, ko, service, $, toolsModel, login) {
        self.login = login;
        self.toolsModel = new toolsModel(self.login);

        return {
            toolsModel: self.toolsModel
        };
    });
