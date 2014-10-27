define(['jquery', 'knockout' ], function($, ko) {
    return function AppInfoModel(configPath, login) {
        // Application info box
        var self = this;

        self.data = ko.observable('');
        self.showInfo = ko.observable(false);
        self.maxLength = 120;

        self.toggle = function() {
            self.showInfo(!self.showInfo());
        };

        self.save = function() {
            self.data(document.getElementsByName(configPath)[0].textContent);
            if (self.data().length > 120) {
                swal('Text too long.', 'The maximum comment length is 120 characters. It will not be saved until it is shorter.', 'error');
                return;
            }
            var dict = {
                loginName: login.elements.username(),
                configurationPath: configPath,
                serviceInfo: self.data()
            };

            $.post('/api/serviceinfo/', dict).fail(function(data) {
                swal('Error Posting ServiceInfo.', JSON.stringify(data), 'error');
            });
        };

        self.getInfo = ko.computed(function() {
            if (self.showInfo()) {
                var dict = {configurationPath: configPath};
                if (self.showInfo()) {
                    $.getJSON('/api/serviceinfo/', dict, function(data) {
                        self.data(data.servicedata);
                    }).fail(function(data) {
                        swal('Failed GET for ServiceInfo.', JSON.stringify(data), 'error');
                    });
                }
            }
        });

    };
});
