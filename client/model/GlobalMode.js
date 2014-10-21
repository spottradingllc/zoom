define(
    [
        'knockout',
        'service',
        'jquery',
        'model/loginModel'
    ],
    function(ko, service, $, login) {
        var self = this;
        self.login = login;
        self.current = ko.observable('Unknown');
        self.maxTimingEstimate = ko.observable('');
        self.minTimingEstimate = ko.observable('');

        self.isOn = ko.computed(function() {
            return self.current() === 'auto';
        });

        self.OnClass = ko.computed(function() {
            if (self.isOn()) {
                return 'btn btn-default active';
            }
            else {
                return 'btn btn-default';
            }
        });
        self.OffClass = ko.computed(function() {
            if (self.current() === 'manual') {
                return 'btn btn-default active';
            }
            else {
                return 'btn btn-default';
            }
        });

        self.handleModeUpdate = function(data) {
            var update = JSON.parse(data.global_mode);
            self.current(update.mode);
        };

        self.handleTimingUpdate = function(data) {
            var maxtime = JSON.parse(data.maxtime);
            var endMs = Date.now() + maxtime * 1000;
            var end = new Date(endMs);
            self.maxTimingEstimate(end.toLocaleTimeString());

            var mintime = JSON.parse(data.mintime);
            var endMs = Date.now() + mintime * 1000;
            end = new Date(endMs);
            self.minTimingEstimate(end.toLocaleTimeString());
        };

        self.timingString = ko.computed(function() {
            if (self.maxTimingEstimate() === self.minTimingEstimate()) {
                return self.maxTimingEstimate();
            }
            else {
                return self.minTimingEstimate() + ' - ' + self.maxTimingEstimate();
            }
        });

        var onGlobalModeError = function(data) {
            swal('Well shoot...', 'An Error has occurred while getting the global mode.', 'error');
        };

        self.getGlobalMode = function() {
            return service.get('api/mode/', self.handleModeUpdate, onGlobalModeError);
        };

        self.getTimingEstimate = function() {
            return service.get('api/timingestimate',
                self.handleTimingUpdate,
                function() {
                    swal('Well shoot...', 'An Error has occurred while getting the initial time estimate', 'error');
                });
        };

        self.setGlobalMode = function(mode) {
            if (confirm('Please confirm that you want to set Zookeeper to ' + mode + ' mode by pressing OK.')) {
                var dict = {
                    'command': mode,
                    'user': self.login.elements.username()
                };
                $.post('/api/mode/', dict).fail(function(data) {
                    swal('Error Posting Mode Control.', JSON.stringify(data), 'error');
                });
            }
        };

        self.getGlobalMode();  // get initial data
        self.getTimingEstimate();  // get initial data

        return self;
    });
