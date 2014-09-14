define(['jquery', 'knockout' ], function($, ko){
return function AppInfoModel(configPath, login) {
    // Application info box
    var self = this;

    self.data = ko.observable("");
    self.showInfo = ko.observable(false);

    self.toggle = function () {
        self.showInfo(!self.showInfo());
    };

    self.save = function () {
        self.data(document.getElementsByName(configPath)[0].textContent);
        var dict = {
            loginName: login.elements.username(),
            configurationPath: configPath,
            serviceInfo: self.serviceInfo()
        };

        $.post("/api/serviceinfo/", dict).fail(function (data) {
            alert("Error Posting ServiceInfo " + JSON.stringify(data));
        });
    };

    self.getInfo = ko.computed(function () {
        if (self.showInfo()) {
            var dict = {configurationPath: configPath};
            if (self.showInfo()) {
                $.getJSON("/api/serviceinfo/", dict, function (data) {
                    self.data(data.servicedata);
                }).fail(function (data) {
                    alert("Failed Get for ServiceInfo " + JSON.stringify(data));
                });
            }
        }
    });

}});