function GlobalMode(service, ko, $, login) {
    var self = this;

    self.login = login;
    self.current = ko.observable("Unknown");
    self.OnClass = ko.computed(function() {
        if (self.current() == 'auto') {
            return "btn btn-default active";
        }
        else {
            return "btn btn-default";
        }
    });
    self.OffClass = ko.computed(function() {
        if (self.current() == 'manual') {
            return "btn btn-default active";
        }
        else {
            return "btn btn-default";
        }
    });

    self.fnHandleUpdate = function(data) {
        update = JSON.parse(data.global_mode);
        self.current(update.mode);
    };

    var fnOnGlobalModeError = function(data) {
        alert('An Error has occurred while getting the global mode.');
    };

    self.fnGetGlobalMode = function() {
      return service.get('api/mode/', self.fnHandleUpdate, fnOnGlobalModeError);
    };

    self.fnSetGlobalMode = function (mode) {
        if (confirm("Please confirm that you want to set Zookeeper to " + mode + " mode by pressing OK.")) {
            var dict = {
                "command" : mode,
                "user": self.login.elements.username()
            };
            $.post("/api/mode/", dict);
        }
    };

    self.fnGetGlobalMode();  // get initial data
}
