define(['knockout', 'service' ], function(ko, service) {
    var environment = {};
    environment.env = ko.observable('Unknown');
    
    var envColor = {
        staging: '#FFDA47',
        stagText: '#000000',
        production: '#E64016',
        prodText: '#FFFFFF',
        unknown: '#FF33CC'
     };

    var envType = {
        stg: 'staging',
        uat: 'uat',
        prod: 'production'
    };

    environment.envColor = ko.computed(function() {
        switch (self.environment().toLowerCase()) {
            case envType.stg:
                return envColor.staging;
            case envType.uat:
                return envColor.uat;
            case envType.prod:
                return envColor.production;
            default:
                return envColor.unknown;
        }
    });

    environment.envTextColor = ko.computed(function() {
        switch (self.environment().toLowerCase()) {
            case envType.prod:
                return envColor.prodText;
            default:
                return envColor.stagText;
        }
    });

    var onSuccess = function(data) {
        env(data.environment);
        var stylename = data.environment.toLowerCase().concat('_style');
        document.getElementById(stylename).removeAttribute('disabled');
    };

    var onFailure = function(data) {
        alert('There was an error getting environment');
    };

    service.get('api/environment/', onSuccess, onFailure);

    return environment;
});
