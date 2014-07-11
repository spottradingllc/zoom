function ApplicationState (ko, data, parent) {
    var self = this;

    var colors = {
        actionBlue: '#057D9F',
        errorRed: '#CC574F',
        successTrans: "",
        unknownGray: '#F7EEDA'
    };

    var glyphs = {
        runningCheck: "glyphicon glyphicon-ok-circle btn-lg",
        stoppedX: "glyphicon glyphicon-remove-circle btn-lg",
        unknownQMark: "glyphicon glyphicon-question-sign btn-lg",
        thumpsUp: "glyphicon glyphicon-thumbs-up btn-lg",
        startingRetweet: "glyphicon glyphicon-retweet btn-lg",
        stoppingDown: "glyphicon glyphicon-arrow-down btn-lg",
        errorWarning: "glyphicon glyphicon-warning-sign btn-lg",
        filledStar: "<span class='glyphicon glyphicon-star'></span>",
        emptyStar: "<span class='glyphicon glyphicon-star-empty'></span>"
    };

    self.configurationPath = data.configuration_path;
    self.applicationStatus = ko.observable(data.application_status);
    self.applicationHost = ko.observable(data.application_host);
    self.startTime = ko.observable(data.start_time);
    self.errorState = ko.observable(data.error_state);

    self.applicationStatusClass = ko.computed(function () {
        if (self.applicationStatus().toLowerCase() == "running") {
            return glyphs.runningCheck;
        }
        else if (self.applicationStatus().toLowerCase() == "stopped") {
            return glyphs.stoppedX;
        }
        else {
            return glyphs.unknownQMark;
        }
    }, self);

    self.applicationStatusBg = ko.computed(function () {
        if (self.applicationStatus().toLowerCase() == "running") {
            return colors.successTrans;
        }
        else if (self.applicationStatus().toLowerCase() == "stopped") {
            return colors.errorRed;
        }
        else {
            return colors.unknownGray;
        }
    }, self);


    self.errorStateClass = ko.computed(function () {
        if (self.errorState() && self.errorState().toLowerCase() == "ok") {
            return glyphs.thumpsUp;
        }
        else if (self.errorState() && self.errorState().toLowerCase() == "starting") {
            return glyphs.startingRetweet;
        }
        else if (self.errorState() && self.errorState().toLowerCase() == "stopping") {
            return glyphs.stoppingDown;
        }
        else if (self.errorState() && self.errorState().toLowerCase() == "error") {
            return glyphs.errorWarning;
        }
        else {
            return glyphs.unknownQMark;
        }
    }, self);

    self.errorStateBg = ko.computed(function () {
        if (self.errorState() && self.errorState().toLowerCase() == "ok") {
            return colors.successTrans;
        }
        else if (self.errorState() && self.errorState().toLowerCase() == "starting") {
            return colors.actionBlue;
        }
        else if (self.errorState() && self.errorState().toLowerCase() == "stopping") {
            return colors.actionBlue;
        }
        else if (self.errorState() && self.errorState().toLowerCase() == "error") {
            return colors.errorRed;
        }
        else {
            return colors.unknownGray;
        }
    }, self);

    // Controlling
    self.groupControlStar = ko.computed(function() {
        if (parent.groupControl.indexOf(self) == -1) {
            return glyphs.emptyStar;
        }
        else {
            return glyphs.filledStar;
        }
    });
    self.groupControlStar.extend({rateLimit: 10});

    self.toggleGroupControl = function () {
        if (parent.groupControl.indexOf(self) == -1) {
            parent.groupControl.push(self);
        }
        else {
            parent.groupControl.remove(self);
        }
    };

    // control agent
    self.isHostEmpty = function () {
        if (self.applicationHost() == "") {
            alert("Cannot control an agent with an empty host.");
            return true;
        }
        else {
            return false;
        }
    };

    self.controlAgent = function (com) {
        var confirmString = ["Please confirm that you want to send a " + com + " command to ",
                self.configurationPath + " on " + self.applicationHost() + " by pressing OK."].join('\n');
        confirmString = confirmString.replace(/(\r\n|\n|\r)/gm, "");

        if (!self.isHostEmpty()) {
            if (confirm(confirmString)) {
                var dict = {"configurationPath": self.configurationPath,
                            "applicationHost": self.applicationHost(),
                            "command": com};
                $.post("/api/control_agent/", dict);
            }
        }
    };

    self.onControlAgentError = function () {
        alert("Error controlling agent.");
    };

    // Dependency bubbling
    self.showDependencies = ko.observable(false);
    self.toggleDependencies = function() {
        self.showDependencies(!self.showDependencies());
    };

    self.dependencyClass = ko.computed(function() {
        if (self.showDependencies()) {
            return "caret";
        }
        else {
            return "caret-left"
        }
    });

    self.requires = ko.observableArray([]);
    self.getRequirements = ko.computed(function() {
        self.requires.removeAll();
        var dict = {"configurationPath": self.configurationPath,
                    "applicationHost": self.applicationHost()};
        if (self.applicationHost() == "") return;

        $.getJSON("/api/get_application_dependencies/", dict, function(data) {
            $.each(data, function(index, value) {
                var dict = value;
                var predType = value["type"];
                var path = value["path"]

                // determine predicate type and filter proper application states
                if (predType == "ZookeeperHasChildren") {
                    var applicationState = ko.utils.arrayFirst(parent.applicationStates(), function(applicationState) {
                        return (path == applicationState.configurationPath);
                    });
                    if (applicationState) self.requires.push(applicationState);
                }
                else if (predType == "ZookeeperHasGrandChildren") {
                    ko.utils.arrayForEach(parent.applicationStates(), function(applicationState) {
                        if (ko.utils.stringStartsWith(applicationState.configurationPath, path)) {
                            self.requires.push(applicationState);
                        }
                    });
                }
                else {
                    return;
                }
            });
        });
    });
    self.requires.extend({rateLimit: 2000});

    self.requiredBy = ko.computed(function() {
        var dependencies = ko.observableArray([]);
        ko.utils.arrayForEach(parent.applicationStates(), function(applicationState) {
            if (applicationState.requires().indexOf(self) > -1) {
                dependencies.push(applicationState);
            }
        });

        return dependencies().slice();
    });
    self.requiredBy.extend({rateLimit: 1000});
}
