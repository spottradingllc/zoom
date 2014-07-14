function GlobalMode(service, ko, $) {
    var self = this;

    self.current = ko.observable("Unknown");
    self.reactClass = ko.computed(function() {
        if (self.current() == 'Reacting to ZK changes.') {
            return "btn btn-success";
        }
        else {
            return "btn btn-default";
        }
    });
    self.ignoreClass = ko.computed(function() {
        if (self.current() == 'Ignoring ZK changes.') {
            return "btn btn-success";
        }
        else {
            return "btn btn-default";
        }
    });

    var fnOnGlobalModeSuccess = function(data) {
        if (data.mode == 'manual') {
            self.current('Ignoring ZK changes.');
        }
        else if (data.mode == 'auto') {
            self.current('Reacting to ZK changes.');
        }
    };

    var fnOnGlobalModeError = function(data) {
        alert('An Error has occurred while getting the global mode.');
    };

    self.fnGetGlobalMode = function() {
      return service.get('api/get_global_mode/', fnOnGlobalModeSuccess, fnOnGlobalModeError);
    };

    self.fnSetGlobalMode = function (mode) {
        if (confirm("Please confirm that you want to set Zookeeper to " + mode + " mode by pressing OK.")) {
            var dict = {"command" : mode};
            $.post("/api/control_zk/", dict);
        }
    };

    self.fnGetGlobalMode();  // get initial data
}