define([ 'classes/applicationStates', ], function(ApplicationStates){
return function ApplicationState (ko, data, parent) {
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
    self.mode = ko.observable(data.local_mode);
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
            return "glyphicon glyphicon-eye-open"; 
        }
        else if(self.mode() == 'manual'){
            return "glyphicon glyphicon-eye-close"; 
        }
        else {
            return "glyphicon glyphicon-question-sign";
        }

    });

    self.graphiteApplicationURL = function(){
        var url = "http://haproxy" + parent.environment.toLowerCase() + "/render?";
        var appName = self.configurationPath.replace("/spot/software/state/", "");
        var dotname = appName.replace(/\//g, ".");
        url = url + "target=alias(secondYAxis(Infrastructure.startup." + dotname + '.result), "Last Exit Code")';
        url = url + "&target=alias(Infrastructure.startup." + dotname + '.runtime, "Startup Time")';
        url = url + "&from=-7d";
        url = url + "&yMinRight=-2";
        url = url + "&yMaxRight=2";
        url = url + "&yStepRight=1";
        url = url + "&lineMode=staircase";
        url = url + "&width=850";
        url = url + "&height=500";
        url = url + "&vtitle=Startup Time (seconds)";
        url = url + '&vtitleRight=Exit Code (0 = Success)';
        url = url + '&title='+appName;
        return encodeURI(url);
    };

    self.modalShow = function(urls){
        $('#graphiteBody').empty();

        for(i=0; i< urls.length; ++i){
            var url = urls[i];
            //console.log("getting "+ url);
            var html = '<img style="-webkit-user-select: none" src="'+url+'"/>';
            $('#graphiteBody').append($.parseHTML(html));
        }

        $('#graphiteModal').modal('show');
        //$('.big-modal-class').modal('show');
    };

    self.graphiteBaseURL = function(){
        //http://graphite.readthedocs.org/en/latest/render_api.html
        var url = "http://haproxy" + parent.environment.toLowerCase() + "/render?";
        url = url + "&from=-7d";
        url = url + "&width=850";
        url = url + "&height=500";
        return (url);

    };
    self.graphiteCPUURL = function(){
        var url = self.graphiteBaseURL();
        url = url + "&target=alias("+self.applicationHost() + '.cpuload.avg1,"CPU avg1 Load")';
        url = url + "&yRight=0";
        url = url + '&title='+self.applicationHost() + "'s CPU";
        url = url + "&vtitle=Load";
        return encodeURI(url);
    };

    self.graphiteMemoryURL = function(){
        var url = self.graphiteBaseURL();
        url = url + "&target=alias("+self.applicationHost() + '.meminfo.tot, "Total Memory")';
        url = url + "&target=alias("+self.applicationHost() + '.meminfo.used, "Memory Usage")';
        url = url + '&title='+self.applicationHost() + "'s Memory";
        url = url + "&vtitle=Bytes";
        return encodeURI(url);
    };

    self.graphiteNetworkURL = function(){
        var url = self.graphiteBaseURL();
        url = url + "&target="+self.applicationHost() + '.nettotals.kbin.*';
        url = url + "&target="+self.applicationHost() + '.nettotals.kbout.*';
        url = url + '&title='+self.applicationHost() + "'s Network Usage";
        url = url + "&vtitle=KB sent/recieved";
        return encodeURI(url);
    };

    self.graphiteDiskSpaceURL = function(){
        var url = self.graphiteBaseURL();
        url = url + "&target="+self.applicationHost() + '.diskinfo.opt.total_bytes';
        url = url + "&target="+self.applicationHost() + '.diskinfo.opt.used_bytes';
        url = url + '&title='+self.applicationHost() + "'s Disk Space";
        url = url + "&vtitle= Bytes of Disk Space";
        return encodeURI(url);
    };

    self.graphiteBufferErrorsURL = function(){
        var url = self.graphiteBaseURL();
        url = url + "&target="+self.applicationHost() + '.tcpinfo.udperrs';
        url = url + "&target="+self.applicationHost() + '.nicinfo.*.*';
        url = url + '&title='+self.applicationHost() + "'s Buffer Errors";
        url = url + "&vtitle= Errors";
        return encodeURI(url);
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

    // Application info box
    self.serviceInfo = ko.observable("");    
    self.showInfo = ko.observable(false);
    
    self.toggleInfo = function() {
        self.showInfo(!self.showInfo());
    };

    self.saveInfo = function() {
        self.serviceInfo(document.getElementsByName(self.configurationPath)[0].textContent);
        var dict = {loginName : parent.login.elements.username(), configurationPath : self.configurationPath, serviceInfo : self.serviceInfo()};

        $.post("/api/serviceinfo/", dict).fail(function(data) {
            alert( "Error Posting ServiceInfo " + JSON.stringify(data));
        });
    };


    self.getInfo = ko.computed(function() {
        if (self.showInfo()) {
            var dict = {configurationPath : self.configurationPath};
            if (self.showInfo()) {
                $.getJSON("/api/serviceinfo/", dict, function(data) {
                    self.serviceInfo(data.servicedata);
                }).fail(function(data){
                    alert("Failed Get for ServiceInfo " + JSON.stringify(data));
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

    self.passwordConfirm = ko.observable("");
    
    self.options = "";

    self.allowAction = function(data) {
        if (!self.isHostEmpty()) {
                var dict = {
                    "componentId": self.componentId,
                    "applicationHost": self.applicationHost(),
                    "command": self.options.com,
                    "argument": self.options.arg,
                    "user": parent.login.elements.username()
                };
                $.post("/api/agent/", dict, function() {
                    $('#passwordCheckModal').modal('hide');                
                    })    
                    .fail(function(data) {
                        alert( "Error Posting ControlAgent " + JSON.stringify(data));
                    });
        }
        self.passwordConfirm("");
    
    };

    self.disallowAction = function(data) {
        self.passwordConfirm("");
        $('#passwordField').popover('show');
    };

    // Re-checks password and provides success and failure functions to $.post
    self.submitAction = function() {
        // client-side blank password check
        if ("" ===  self.passwordConfirm()){
            return self.disallowAction();
        }
 
        var params = {
            username: parent.login.elements.username(),
            password: self.passwordConfirm()
        };
        
        return $.post("/login", JSON.stringify(params), self.allowAction).fail(self.disallowAction);
    };

    self.buttonLabel = ko.observable("");

    self.appName = function() {
        var copy = self.configurationPath;
        copy = copy.match(/([^\/]*)\/*$/)[1];
        return copy;
    };

    self.controlAgent = function (options) {
        //options.com: command
        //options.arg: command argument
        
        self.buttonLabel("Send " + options.com.toUpperCase() + " command");
        self.options = options;

        $('#passwordField').popover('destroy');
        $('#passwordCheckModal').modal('show');
        
    };

    self.checkEnter = function (d, e){    
        if (e.which == 13){
                $('#send').trigger('click');
                return false;
        }
        return true;
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
                var applicationState = ko.utils.arrayFirst(ApplicationStates(), function(applicationState) {
                    return (path == applicationState.configurationPath);
                });
                if (applicationState) self.requires.push(applicationState);
            }
            else if (predType == self.predType.grandchildren) {
                ko.utils.arrayForEach(ApplicationStates(), function(applicationState) {
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
        ko.utils.arrayForEach(ApplicationStates(), function(applicationState) {
            if (applicationState.requires().indexOf(self) > -1) {
                dependencies.push(applicationState);
            }
        });

        return dependencies().slice();
    });
    self.requiredBy.extend({rateLimit: 1000});

    self.deleteRow = function() {
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
                ApplicationStates.remove(self);
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
}});

