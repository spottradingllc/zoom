define(
    [
        'durandal/app',
        'knockout',
        'service',
        'jquery',
        'd3',
        'model/loginModel',
        'model/pillarModel',
        'model/adminModel',
        'bindings/radio',
        'bindings/tooltip'
    ],
    function(app, ko, service, $, d3, login, pillarModel, admin) {
        self.login = login;
        self.adminModel = admin;
        self.pillarModel = new pillarModel(self.login, self.adminModel);
        self.attached = function() {
            self.pillarModel.pillarApiModel.loadServers(true);
        };
        self.activate = function(host) {
            self.pillarModel.searchVal(host)
        };
        self.detached = function() {
            // do something here??
        };
        
        return {
            pillarModel: self.pillarModel,
            detached: self.detached,
            attached: self.attached,
            activate: self.activate
        };
    });
