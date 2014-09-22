define(['knockout',
        'plugins/router',
        'service',
        'jquery',
        'model/ApplicationState',
        'model/environmentModel',
        'model/adminModel', 
        'model/GlobalMode',
        'model/customFilterModel',
        'classes/applicationStateArray',
        'classes/dependency-maps/DependencyMaps'],
function(ko, router, service, $, ApplicationState, Environment, admin, GlobalMode, CustomFilterModel, ApplicationStateArray, DependencyMaps){
return function ApplicationStateModel(login) {
    var self = this;
    self.login = login;
    self.admin = admin;
    self.globalMode = GlobalMode;
    self.applicationStateArray = ApplicationStateArray;
    self.textFilter = ko.observable("");
    self.environment = Environment;
    self.name = "Application State Table";
    self.passwordConfirm = ko.observable("");
    self.options = {};
    self.buttonLabel = ko.observable("");   
    self.groupMode = ko.observable(false);
    self.clickedApp = ko.observable({});
    self.customFilters = new CustomFilterModel(self);

    var envColor = {
        staging: '#FFDA47',
        stagText: '#000000',
        production: '#E64016',
        prodText: '#FFFFFF',
        unknown: '#FF33CC'
    };

    var env = {
        stg: 'staging',
        uat: 'uat',
        prod: 'production'
    };

    self.headers = [
        {title: 'Up/Down', sortPropertyName: 'applicationStatus', asc: ko.observable(true)},
        {title: 'Configuration Path', sortPropertyName: 'configurationPath', asc: ko.observable(true)},
        {title: 'Host', sortPropertyName: 'applicationHost', asc: ko.observable(true)},
        {title: 'Start Time', sortPropertyName: 'startTime', asc: ko.observable(false)},
        {title: 'Status', sortPropertyName: 'errorState', asc: ko.observable(true)},
        {title: 'Control', sortPropertyName: 'control', asc: ko.observable(true)},
        {title: 'Delete', sortPropertyName: 'control', asc: ko.observable(true)}
    ];

    self.showHeader = function(index){
        if(self.headers[index].title == 'Control' &&
           !self.login.elements.authenticated()){
            return false;
        }
        return !(self.headers[index].title == 'Delete' && !self.admin.enabled());

    };

    self.showServerConfig = function(hostname) {
        router.navigate('#config/' +  hostname(), { trigger: true });
    };

    // Changes modal header color to reflect current environment
    self.envModalColor = ko.computed(function(){
        switch(self.environment().toLowerCase()){
            case env.stg:
                return envColor.staging;
                break;
            case env.uat:
                return envColor.uat;
                break;
            case env.prod:
                return envColor.production;
                break;
            default:
                return envColor.unknown;
                break;
        }
    });

    self.envTextColor = ko.computed(function(){
        switch(self.environment().toLowerCase()){
            case env.prod:
                return envColor.prodText;
                break;
            default:
                return envColor.stagText;
                break;
        }
    });

    // control agent
    self.isHostEmpty = function () {
        if (self.clickedApp.applicationHost == "") {
            alert("Cannot control an agent with an empty host.");
            return true;
        }
        else {
            return false;
        }
    };

    self.executeSingleControl = function(options) {
        if (!self.isHostEmpty()) {
                var dict = {
                    "componentId": self.clickedApp().componentId,
                    "applicationHost": self.clickedApp().applicationHost,
                    "command": options.com,
                    "argument": options.arg,
                    "user": self.login.elements.username()
                };
                $.post("/api/agent/", dict, function() {
                    $('#groupCheckModal').modal('hide');                
                    })    
                    .fail(function(data) {
                        alert("Error Posting ControlAgent " + JSON.stringify(data));
                    });
        }
        self.passwordConfirm("");
    
    };

    // Takes in 'options' as an argument and actually sends a command to the server
    self.executeGroupControl = function(options){
        ko.utils.arrayForEach(self.groupControl(), function(applicationState) {
            var dict = {
                "componentId": applicationState.componentId,
                "configurationPath": applicationState.configurationPath,
                "applicationHost": applicationState.applicationHost,
                "command": options.com,
                "argument": options.arg,
                "user": self.login.elements.username()
             };

            if (self.isHostEmpty()) {
                alert("Skipping the agent with configuration path " + application.configurationPath + ": empty host.");
            }
            else {
                $.post("/api/agent/", dict).fail(function(data) {
                    alert( "Error Posting Group Control " + JSON.stringify(data));
                });
            }
        });

        if (options.clear_group){
            self.clearGroupControl();
        }
        
        // Clears modal dialog password entry field
        self.passwordConfirm("");
    };

    // Replaces dep_restart by checking self.options. Will also call every other command by passing
    // through self.options to executeGroupControl or executeSingleControl
    self.determineAndExecute = function() {
        if (self.groupMode()){
            if (self.options.com === 'dep_restart'){
                self.executeGroupControl({'com':'ignore', 'arg':false, 'clear_group':false});
                self.executeGroupControl({'com':'stop', 'arg': false, 'clear_group':false});
                self.checkDown();
            }
            else {
                self.executeGroupControl(self.options);
            }
        }
        else self.executeSingleControl(self.options);

        $('#groupCheckModal').modal('hide');
    };

    self.disallowAction = function() {
        self.passwordConfirm("");
        $('#passwordFieldG').popover('show');
    };

    // Re-checks password and provides success and failure functions to $.post
    self.submitAction = function() {
        // client-side blank password check
        if ("" ===  self.passwordConfirm()){
            return self.disallowAction();
        }
        
        var params = {
            username: self.login.elements.username(),
            password: self.passwordConfirm()
        };
        
        return $.post("/login", JSON.stringify(params), self.determineAndExecute).fail(self.disallowAction);
    };
    
    self.parseAppName = function(path) {
        if (typeof path === "undefined"){
            return;
        }
        
        return path.split("application/")[1];
    };

    // functions/variables for group control of agents
    self.groupControl = ko.observableArray([]);
    
    self.controlAgent = function (options, clickedApp) {
        //options.com: command
        //options.arg: command argument
        if (options == undefined) options = {'com': 'dep_restart'};
        
        //if no provided individual, this is a group
        if (typeof clickedApp === "undefined") self.groupMode(true);
        else {
            self.clickedApp(clickedApp);
            self.groupMode(false);
        }

        self.buttonLabel("Send " + options.com.toUpperCase() + " command");
        self.options = options;
        
        $('#passwordFieldG').popover('destroy');
        $('#groupCheckModal').modal('show');
    };


    self.checkEnter = function (d, e){    
        if (e.which == 13) {
            $('#Gsend').trigger('click');
            return false;
        }
        return true;
    };


    // Checks if all groupControl services are down. Used in self.determineAndExecute
    var interval = 0;
    self.checkDown = function (){
        clearInterval(interval);
        var alldown = ko.utils.arrayFirst(self.groupControl(), function(item){
            return item.applicationStatus() != "stopped";
        });
        if (alldown) {
            interval = setInterval(self.checkDown, 5000);
        } else {
            self.executeGroupControl({'com':'dep_restart', 'arg': false, 'clear_group':true});
        }
    };

    self.sleep = function (milliseconds) {
      var start = new Date().getTime();
      for (var i = 0; i < 1e7; i++) {
        if ((new Date().getTime() - start) > milliseconds){
          break;
        }
      }
    };

    self.clearGroupControl = function () {
        ko.utils.arrayForEach(self.applicationStateArray(), function(applicationState) {
            if (self.groupControl.indexOf(applicationState) > -1) {
                self.groupControl.remove(applicationState);
            }
        });
    };

    self.filteredGroupControl = function () {
        ko.utils.arrayForEach(self.filteredItems(), function(applicationState) {
            if (self.groupControl.indexOf(applicationState) == -1) {
                self.groupControl.push(applicationState);
            }
        });
    };

    // Sorting
    self.activeSort = ko.observable(self.headers[3]); //set the default sort by start time
    self.holdSortDirection = ko.observable(true); // hold the direction of the sort on updates
    self.sort = function (header, initialRun) {
        if (header.title == "Control") { return }  // ignore sorting on Control header

        // initialRun == true if self.sort is called on page initialization 
        if (typeof initialRun == "undefined" || typeof initialRun == "object") initialRun = false;

        //if this header was just clicked a second time...
        if (self.activeSort() == header && !self.holdSortDirection() && !initialRun) {
            header.asc(!header.asc()); // ...toggle the direction of the sort
        } else {
            self.activeSort(header); // first click, remember it
        }

        var prop = self.activeSort().sortPropertyName;

        var ascSort = function (a, b) {
            var aprop = ko.unwrap(a[prop]);
            var bprop = ko.unwrap(b[prop]);
            return aprop < bprop ? -1 : aprop > bprop ? 1 : aprop == bprop ? 0 : 0;
        };
        var descSort = function (a, b) {
            return ascSort(b, a);
        };
        var sortFunc = self.activeSort().asc() ? ascSort : descSort;

        self.applicationStateArray.sort(sortFunc);
        if (!initialRun) self.holdSortDirection(false);
    };

    self.clearSearch = function () {
        self.textFilter("");
    };

    self.sortByTime = function() {
        var timeheader = {title: 'Time', sortPropertyName: 'mtime', asc: ko.observable(true)};
        self.activeSort(timeheader);
        self.sort(self.activeSort(), false);
    };

    // Filtering from the search bar
    self.filteredItems = ko.dependentObservable(function() {
        var filter = self.textFilter().toLowerCase();
        // check for enabled custom filters, otherwise use global appStates array
        var ret;
        if (!filter && self.customFilters.enabled().length == 0) {
            ret = self.applicationStateArray();
        } 
        else if(self.customFilters.enabled().length > 0) {
            ret = ko.utils.arrayFilter(self.customFilters.allMatchedItems(), function(item) {
                var re = new RegExp(filter, "i");
                return (item.configurationPath.match(re) || item.applicationHost().match(re));
            });
        } else {
            ret = ko.utils.arrayFilter(self.applicationStateArray(), function(item) {
                var re = new RegExp(filter, "i");
                return (item.configurationPath.match(re) || item.applicationHost().match(re));
            });
        }

        //filter for time last
        return ko.utils.arrayFilter(ret, function(item) {
            if(self.customFilters.filterByTime()){
                return (item.mtime > self.customFilters.time());
            }else{
                return true;
            }
        });
    }, self);

    self.filterBy = function(param) {
        self.textFilter(param);
    };

    // hiding/showing all dependencies
    self.showingAllDependencies = ko.observable(false);
    self.expandAllDependencies = function() {
        self.showingAllDependencies(true);
    };
    self.collapseAllDependencies = function() {
        self.showingAllDependencies(false);
    };

    self.toggleAllDependencies = ko.computed(function() {
        if (self.showingAllDependencies()) {
            ko.utils.arrayForEach(self.applicationStateArray(), function(appState) {
                appState.showDependencies(true);
            });
        }
        else {
            ko.utils.arrayForEach(self.applicationStateArray(), function(appState) {
                appState.showDependencies(false);
            });
        }
    });

    // view toggling
    self.currentView = ko.observable(self);
    self.views = ko.observableArray([]);
    self.views.push(self);

    // dependency maps
    self.dependencyMaps = new DependencyMaps(self);

    // create new app state
    self.createApplicationState = function(data) {
        return new ApplicationState(data, self)
    };

    // handle updates from web server
    self.handleApplicationStatusUpdate = function (update) {
        // Search the array for row with matching path
        
        if (update.delete) {
            self.applicationStateArray.remove(function(currentRow) {
                return currentRow.configurationPath == update.configuration_path;
            });
        }
        else{
            var row = ko.utils.arrayFirst(self.applicationStateArray(), function (currentRow) {
                return currentRow.configurationPath == update.configuration_path;
            });
            if (row) {
                row.applicationStatus(update.application_status);
                row.startTime(update.start_time);
                row.applicationHost(update.application_host);
                row.errorState(update.error_state);
                row.mode(update.local_mode);
                row.mtime = Date.now();
            }
            else { 
                // add new item to array
                var newRow = self.createApplicationState(update);
                self.applicationStateArray.push(newRow);
            }
        }
    };

    self.handleApplicationDependencyUpdate = function (message) {
        $.each(message.application_dependencies, function() {
            var update = this;
            var row = ko.utils.arrayFirst(self.applicationStateArray(), function (currentRow) {
                return currentRow.configurationPath == update.configuration_path;
            });
            if (row) {
                row.setRequires(update)
            }
        });
    };

    self.reloadCaches = function () {
        if (confirm("Please confirm you want to clear and reload all server side caches by pressing OK.")) {
            var dict = {
                "command" : "all",
                "user": self.login.elements.username()
            };
            self.applicationStateArray.removeAll();
            $.post("/api/cache/reload/", dict, function(data){
                alert(data);
            }).fail(function(data) {
                alert( "Error Posting Clear Cache " + JSON.stringify(data));
            });
        }
    };

    var onApplicationStatesSuccess = function (data) {
        var table = $.map(data.application_states, function (row) {
            return self.createApplicationState(row)
        });

        self.applicationStateArray(table);
        // sort initially on descending start time - initial run so give true param
        self.sort(self.activeSort(), true);
    };

    var onApplicationStatesError = function (data) {
        alert('An Error has occurred while loading the application states.');
    };

    self.loadApplicationStates = function () {
        return service.nonAsyncGet('api/application/states/',
                           onApplicationStatesSuccess, 
                           onApplicationStatesError);
    };

    var onApplicationDependenciesError = function (data) {
        alert('An Error has occurred while loading the application dependencies.');
    };

    self.loadApplicationDependencies = function () {
        return service.nonAsyncGet('api/application/dependencies/',
                           self.handleApplicationDependencyUpdate, 
                           onApplicationDependenciesError);
    };

}});
