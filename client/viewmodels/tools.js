define(
    [
        'durandal/app',
        'knockout',
        'service',
        'jquery',
        'd3',
        'model/loginModel',
        'model/toolsModel',
        'bindings/radio',
        'bindings/tooltip'
    ],
    function(app, ko, service, $, d3, login, toolsModel) {
        self.login = login;
        self.toolsModel = new toolsModel(self.login);

        return {
            toolsModel: self.toolsModel
        };
    });
