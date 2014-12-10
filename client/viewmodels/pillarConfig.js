define(
    [
        'durandal/app',
        'knockout',
        'service',
        'jquery',
        'd3',
        'model/loginModel',
        'model/pillarModel',
        'bindings/radio',
        'bindings/tooltip'
    ],
    function(app, ko, service, $, d3, login, pillarModel) {
        self.login = login;
        self.pillarModel = new pillarModel(self.login);
        self.attached = function() {
            self.pillarModel.loadServers(true);
        };
        self.detached = function() {
            // do something here??
        };
        
        return {
            pillarModel: self.pillarModel,
            detached: self.detached,
            attached: self.attached
        };
    });
