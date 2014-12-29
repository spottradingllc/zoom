define(
    [
        'durandal/app',
        'knockout',
        'service',
        'jquery',
        'model/toolsModel',
        'bindings/radio',
        'bindings/tooltip'
    ],
    function(app, ko, service, $, toolsModel) {
        self.toolsModel = new toolsModel();

        return {
            toolsModel: self.toolsModel
        };
    });
