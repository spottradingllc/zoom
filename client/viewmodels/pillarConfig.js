define(
    [
        'durandal/app',
        'knockout',
        'service',
        'jquery',
        'd3',
        'model/loginModel',
        'model/pillarModel',
        'model/GlobalMode',
        'bindings/radio'
    ],
    function(app, ko, service, $, d3, login, pillarModel, GlobalMode) {
        self.pillarModel = new pillarModel();
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
