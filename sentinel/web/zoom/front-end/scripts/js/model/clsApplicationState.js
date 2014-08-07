function ApplicationState (ko, data, parent) {
    var self = this;

    var colors = {
        actionBlue: '#057D9F',
        errorRed: '#CC574F',
        successTrans: "",
        unknownGray: '#F7EEDA',
        warnOrange: '#FFAE2F'
    };

    var glyphs = {
        runningCheck: "glyphicon glyphicon-ok-circle btn-lg",
        stoppedX: "glyphicon glyphicon-remove-circle btn-lg",
        unknownQMark: "glyphicon glyphicon-question-sign btn-lg",
        thumpsUp: "glyphicon glyphicon-thumbs-up btn-lg",
        startingRetweet: "glyphicon glyphicon-retweet btn-lg",
        stoppingDown: "glyphicon glyphicon-arrow-down btn-lg",
        errorWarning: "glyphicon glyphicon-warning-sign btn-lg",
        notifyExclamation: "glyphicon glyphicon-exclamation-sign btn-lg",
        filledStar: "glyphicon glyphicon-star",
        emptyStar: "glyphicon glyphicon-star-empty"
    };

    var applicationStatuses = {running : "running", stopped : "stopped", unknown : "unknown"};
    var errorStates = {ok : "ok", starting : "starting", stopping : "stopping", error : "error", notify: "notify", unknown : "unknown"};

    self.componentId = data.application_name;
    self.configurationPath = data.configuration_path;
    self.applicationStatus = ko.observable(data.application_status);
    self.applicationHost = ko.observable(data.application_host);
    self.startTime = ko.observable(data.start_time);
    self.errorState = ko.observable(data.error_state);
    self.environment = ko.observable(data.environment);
    self.mtime = Date.now();

    self.applicationStatusClass = ko.computed(function () {
        if (self.applicationStatus().toLowerCase() == applicationStatuses.running) {
            return glyphs.runningCheck;
        }
        else if (self.applicationStatus().toLowerCase() == applicationStatuses.stopped) {
            return glyphs.stoppedX;
        }
        else {
            return glyphs.unknownQMark;
        }
    }, self);
    self.applicationStatusClass.extend({rateLimit: 100});

    self.applicationStatusBg = ko.computed(function () {
        if (self.applicationStatus().toLowerCase() == applicationStatuses.running) {
            return colors.successTrans;
        }
        else if (self.applicationStatus().toLowerCase() == applicationStatuses.stopped) {
            return colors.errorRed;
        }
        else {
            return colors.unknownGray;
        }
    }, self);
    self.applicationStatusBg.extend({rateLimit: 100});

    self.launchGraphiteData = function(){
        //http://graphite.readthedocs.org/en/latest/render_api.html
        var url = "http://graphite" + parent.environment.toLowerCase() + "/render?";
        var appName = self.configurationPath.replace("/spot/software/state/", "");
        var dotname = appName.replace(/\//g, ".");
        url = url + "target=alias(secondYAxis(Infrastructure.startup." + dotname + '.result), "Last Exit Code")';
        url = url + "&target=alias(Infrastructure.startup." + dotname + '.runtime, "Startup Time")';
        url = url + "&from=-7d";
        url = url + "&yMinRight=-2";
        url = url + "&yMaxRight=2";
        url = url + "&yStepRight=1";
        url = url + "&lineMode=staircase";
        url = url + "&width=900";
        url = url + "&height=500";
        url = url + "&vtitle=Startup Time (seconds)";
        url = url + '&vtitleRight=Exit Code%0A(0 = Success)';
        url = url + '&title='+appName;
             
        window.open(url, "GraphiteData");
    };


    self.errorStateClass = ko.computed(function () {
        if (self.errorState() && self.errorState().toLowerCase() == errorStates.ok) {
            return glyphs.thumpsUp;
        }
        else if (self.errorState() && self.errorState().toLowerCase() == errorStates.starting) {
            return glyphs.startingRetweet;
        }
        else if (self.errorState() && self.errorState().toLowerCase() == errorStates.stopping) {
            return glyphs.stoppingDown;
        }
        else if (self.errorState() && self.errorState().toLowerCase() == errorStates.error) {
            return glyphs.errorWarning;
        }
        else if (self.errorState() && self.errorState().toLowerCase() == errorStates.notify) {
            return glyphs.notifyExclamation;
        }
        else {
            return glyphs.unknownQMark;
        }
    }, self);
    self.errorStateClass.extend({rateLimit: 100});


    self.errorStateBg = ko.computed(function () {
        if (self.errorState() && self.errorState().toLowerCase() == errorStates.ok) {
            return colors.successTrans;
        }
        else if (self.errorState() && self.errorState().toLowerCase() == errorStates.starting) {
            return colors.actionBlue;
        }
        else if (self.errorState() && self.errorState().toLowerCase() == errorStates.stopping) {
            return colors.actionBlue;
        }
        else if (self.errorState() && self.errorState().toLowerCase() == errorStates.error) {
            return colors.errorRed;
        }
        else if (self.errorState() && self.errorState().toLowerCase() == errorStates.notify) {
            return colors.warnOrange;
        }
        else {
            return colors.unknownGray;
        }
    }, self);
    self.errorStateBg.extend({rateLimit: 100});


    // Controlling
    self.groupControlStar = ko.computed(function() {
        if (parent.groupControl.indexOf(self) == -1) {
            return glyphs.emptyStar;
        }
        else {
            return glyphs.filledStar;
        }
    });
    self.groupControlStar.extend({rateLimit: 100});

    self.toggleGroupControl = function () {
        if (parent.groupControl.indexOf(self) == -1) {
            parent.groupControl.push(self);
        }
        else {
            parent.groupControl.remove(self);
        }
    };

    // Application info box
    self.serviceInfo = ko.observable("");    
    self.showInfo = ko.observable(false);
    
    self.toggleInfo = function() {
        self.showInfo(!self.showInfo());
    };

    self.saveInfo = function() {
        self.serviceInfo(document.getElementsByName(self.configurationPath)[0].textContent);
        var dict = {loginName : parent.login.elements.username(), configurationPath : self.configurationPath, serviceInfo : self.serviceInfo()};

        $.post("/api/serviceinfo/", dict);
    };

    self.getInfo = ko.computed(function() {
        if (self.showInfo()) {
            var dict = {configurationPath : self.configurationPath};
            if (self.showInfo()) {
                $.getJSON("/api/serviceinfo/", dict, function(data) {
                    self.serviceInfo(data);
                });
            }
        }
    });

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
                var dict = {
                    "componentId": self.componentId,
                    "applicationHost": self.applicationHost(),
                    "command": com,
                    "user": parent.login.elements.username()
                };
                $.post("/api/agent/", dict);
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
    self.predType = {children: "zookeeperhaschildren", 
                     grandchildren: "zookeeperhasgrandchildren"};

    self.requires = ko.observableArray([]);
    self.setRequires = function(update) {
        self.requires.removeAll();
        self.mtime = Date.now();
        if (self.applicationHost() == "") return;

        update.dependencies.forEach( function(entry) {

            var predType = entry.type;
            var path = entry.path;

            // determine predicate type and filter proper application states
            if (predType == self.predType.children) {
                var applicationState = ko.utils.arrayFirst(parent.applicationStates(), function(applicationState) {
                    return (path == applicationState.configurationPath);
                });
                if (applicationState) self.requires.push(applicationState);
            }
            else if (predType == self.predType.grandchildren) {
                ko.utils.arrayForEach(parent.applicationStates(), function(applicationState) {
                    if (ko.utils.stringStartsWith(applicationState.configurationPath, path)) {
                        self.requires.push(applicationState);
                    }
                });
            }
            else {
                throw "Unknown predType: " + predType;
            }
        });
    };

    self.requires.extend({rateLimit: 100});

    self.requirementsAreUp = ko.computed(function() {
        if (self.requires().length > 0) {
            for(var i = 0; i < self.requires().length; i++) {
                if (self.requires()[i].applicationStatus() == applicationStatuses.stopped) {
                    return false;
                }
            }
            return true;
        }
        else {
            return true;
        }
    });

    self.requiredBy = ko.computed(function() {
        var dependencies = ko.observableArray([]);
        ko.utils.arrayForEach(parent.applicationStates(), function(applicationState) {
            if (applicationState.requires().indexOf(self) > -1) {
                dependencies.push(applicationState);
            }
        });

        return dependencies().slice();
    });
    self.requiredBy.extend({rateLimit: 100});
}
