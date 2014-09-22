define(['knockout',
        'classes/applicationStateArray',
        'model/graphiteModel',
        'model/appInfoModel'],
function(ko, ApplicationStateArray, GraphiteModel, AppInfoModel){
    return function ApplicationState(data, parent) {
        var self = this;
        var colors = {
            actionBlue: '#057D9F',
            errorRed: '#CC574F',
            successTrans: "",
            unknownGray: '#F7EEDA',
            warnOrange: '#FFAE2F'
        };

        var glyphs = {
            runningCheck: "glyphicon glyphicon-ok-circle",
            stoppedX: "glyphicon glyphicon-remove-circle",
            unknownQMark: "glyphicon glyphicon-question-sign",
            thumpsUp: "glyphicon glyphicon-thumbs-up",
            startingRetweet: "glyphicon glyphicon-retweet",
            stoppingDown: "glyphicon glyphicon-arrow-down",
            errorWarning: "glyphicon glyphicon-warning-sign",
            notifyExclamation: "glyphicon glyphicon-exclamation-sign",
            filledStar: "glyphicon glyphicon-star",
            emptyStar: "glyphicon glyphicon-star-empty",
            modeAuto: "glyphicon glyphicon-eye-open",
            modeManual: "glyphicon glyphicon-eye-close"
        };

        var applicationStatuses = {running : "running", stopped : "stopped", unknown : "unknown"};
        var errorStates = {ok : "ok", starting : "starting", stopping : "stopping", error : "error", notify: "notify", unknown : "unknown"};

        self.componentId = data.application_name;
        self.configurationPath = data.configuration_path;
        self.applicationStatus = ko.observable(data.application_status);
        self.applicationHost = ko.observable(data.application_host);
        self.triggerTime = ko.observable(data.trigger_time);
        self.startTime = ko.observable(data.start_time);
        self.errorState = ko.observable(data.error_state);
        self.mode = ko.observable(data.local_mode);
        self.mtime = Date.now();
        self.graphite = new GraphiteModel(parent.environment().toLowerCase(), self.applicationHost(), self.configurationPath);
        self.appInfo = new AppInfoModel(self.configurationPath, parent.login);

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

        self.modeClass = ko.computed(function(){
            if (self.mode() == parent.globalMode.current()){
                return "";
            }
            else if(self.mode() == 'auto'){
                return glyphs.modeAuto;
            }
            else if(self.mode() == 'manual'){
                return glyphs.modeManual;
            }
            else {
                return glyphs.runningCheck;
            }

        });

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

        self.errorStateBg = ko.computed(function () {
            if (self.errorState() && self.errorState().toLowerCase() == errorStates.ok) {
                if (self.mode() != parent.globalMode.current()){
                    return colors.warnOrange;
                }

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

        // Creates group for sending commands
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
        
        self.onControlAgentError = function () {
            alert("Error controlling agent.");
        };

        // Dependency bubbling
        self.showDependencies = ko.observable(false);
        self.toggleDependencies = function() {
            self.showDependencies(!self.showDependencies());
        };

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
                    var applicationState = ko.utils.arrayFirst(ApplicationStateArray(), function(applicationState) {
                        return (path == applicationState.configurationPath);
                    });
                    if (applicationState) self.requires.push(applicationState);
                }
                else if (predType == self.predType.grandchildren) {
                    ko.utils.arrayForEach(ApplicationStateArray(), function(applicationState) {
                        if (applicationState.configurationPath.substring(0, path.length) == path) {
                            self.requires.push(applicationState);
                        }
                    });
                }
                else {
                    throw "Unknown predType: " + predType;
                }
            });
        };

        self.requires.extend({rateLimit: 2000});

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
            ko.utils.arrayForEach(ApplicationStateArray(), function(applicationState) {
                if (applicationState.requires().indexOf(self) > -1) {
                    dependencies.push(applicationState);
                }
            });

            return dependencies().slice();
        });
        self.requiredBy.extend({rateLimit: 1000});

        self.deleteRow = function() {
            // delete an application row on the web page
            // parses the config and deletes the component with a matching id
            // deletes the path in zookeeper matching the configurationPath
            if (self.requiredBy().length > 0){
                var message = "Someone depends on this! ";
                ko.utils.arrayForEach(self.requiredBy(), function(applicationState) {
                    message = message + "\n" + applicationState.configurationPath;
                });
                alert(message);
            }
            else if(self.applicationHost() == ""){
                if(confirm(self.configurationPath + " has no Host listed, this delete is mostly artificial"))
                {
                    ApplicationStateArray.remove(self);
                }
            }
            else{

                if(confirm(self.configurationPath + " will be deleted, and its dependency configuration lost, continue?"))
                {

                    var dict = {loginName : parent.login.elements.username(), delete : self.configurationPath};

                    var zk_deleted = true;

                    $.post("/api/delete/", dict)
                        .fail(function(data) {
                            zk_deleted = false;
                    });

                    if(zk_deleted){
                        $.get("/api/config/" + self.applicationHost(),
                            function(data){
                                if (data != "Node does not exist.") {
                                    parser = new DOMParser();
                                    xmlDoc = parser.parseFromString(data,"text/xml");
                                    var found = 0;
                                    var x = xmlDoc.getElementsByTagName("Component");
                                    for (var i=0;i<x.length;i++)
                                    {
                                        var id = x[i].getAttribute("id");
                                        if(self.configurationPath.indexOf(id, self.configurationPath.length - id.length) !== -1){
                                            x[i].parentNode.removeChild(x[i]);
                                            found = found + 1;
                                            i = i - 1;
                                        }
                                    }

                                    if(found == 0){
                                        alert("Didn't find component " + self.configurationPath +" in "+self.applicationHost()+"'s config");
                                    }
                                    else if(found == 1){
                                        var oSerializer = new XMLSerializer();
                                        var sXML = oSerializer.serializeToString(xmlDoc);
                                        var params = {
                                            "XML" : sXML,
                                            "serverName" : self.applicationHost()
                                        };
                                        $.ajax({
                                            url: "/api/config/" + self.applicationHost(),
                                            type: 'PUT',
                                            data: JSON.stringify(params)})
                                            .fail(function(data){
                                                alert("Failed putting Config " + JSON.stringify(data));
                                            })
                                    }
                                    else{
                                        alert("Multiple components matched " + self.configurationPath +" in "+self.applicationHost()+"'s config, not acting");
                                    }
                                }
                                else {
                                    alert("no data for host " + self.applicationHost());
                                }
                            })
                            .fail(function(data){
                                alert("Failed Get Config " + JSON.stringify(data));
                        });
                    }
                    else{
                            alert( "Error deleting path: " + JSON.stringify(data.responseText));
                    }

                }
            }

        };

        self.dependencyClass = ko.computed(function() {
            if (self.requires().length == 0 && self.requiredBy().length == 0){
                return "";
            }
            else if (self.showDependencies()) {
                return "caret";
            }
            else {
                return "caret-left"
            }
        });
    }
});

