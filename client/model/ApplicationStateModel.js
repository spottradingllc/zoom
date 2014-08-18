define(['model/ApplicationState', 
        'classes/clsCustomFilter', 
        'classes/dependency-maps/clsDependencyMaps'],
function(ApplicationState, CustomFilter, DependencyMaps){
return function ApplicationStateModel(service, ko, $, login, d3) {
    var self = this;

    self.login = login;
    self.applicationStates = ko.observableArray([]);
    self.textFilter = ko.observable("");
    self.environment = ko.observable("--");
    self.name = "Application State Table";

    var operationTypes = {add: "add", remove: "remove"};

    self.headers = [
        {title: 'Up/Down', sortPropertyName: 'applicationStatus', asc: ko.observable(true)},
        {title: 'Configuration Path', sortPropertyName: 'configurationPath', asc: ko.observable(true)},
        {title: 'Host', sortPropertyName: 'applicationHost', asc: ko.observable(true)},
        {title: 'Start Time', sortPropertyName: 'startTime', asc: ko.observable(false)},
        {title: 'Status', sortPropertyName: 'errorState', asc: ko.observable(true)},
        {title: 'Control', sortPropertyName: 'control', asc: ko.observable(true)},
        {title: 'Delete', sortPropertyName: 'control', asc: ko.observable(true)}
    ];

//    functions/variables for group control of agents
    self.groupControl = ko.observableArray([]);
    self.executeGroupControl = function (options) {
        //options.com: command
        //options.arg: command argument
        //option.no_confirm: confirm bool
        if (options == undefined) options = {};
        var confirmString = ["Please confirm that you want to send a " + options.com + " command to the ",
                self.groupControl().length + " selected agents by pressing OK."].join('\n');
        confirmString = confirmString.replace(/(\r\n|\n|\r)/gm, "");

        if (!options.confirm || confirm(confirmString)) {
            ko.utils.arrayForEach(self.groupControl(), function(applicationState) {
                var dict = {
                    "componentId": applicationState.componentId,
                    "configurationPath": applicationState.configurationPath,
                    "applicationHost": applicationState.applicationHost,
                    "command": options.com,
                    "argument": options.arg,
                    "user": self.login.elements.username()
                };

                if (applicationState.isHostEmpty()) {
                    alert("Skipping the agent with configuration path " + application.configurationPath + ": empty host.");
                }
                else {
                    $.post("/api/agent/", dict).fail(function(data) {
                        alert( "Error Posting Group Control " + JSON.stringify(data));
                    });
                }
            });
        }
    };

    //Checks if all groupControl services are down. Used in self.executeDepRestart
    var interval = 0;
    self.checkDown = function (){
        clearInterval(interval);
        var alldown = ko.utils.arrayFirst(self.groupControl(), function(item){
            return item.applicationStatus() != "stopped";
        });
        if (alldown) {
            interval = setInterval(self.checkDown, 5000);
            return;
        } else {
            self.executeGroupControl({'com':'dep_restart', 'arg': false, 'confirm':false});
            return;
        }
    }

    self.executeDepRestart = function (com) {
        var confirmString = ["Please confirm that you want to send a " + com + " command to the ",
                self.groupControl().length + " selected agents by pressing OK."].join('\n');
        confirmString = confirmString.replace(/(\r\n|\n|\r)/gm, "");

        if (confirm(confirmString)) {
            self.executeGroupControl({'com':'ignore', 'arg':false, 'confirm':false});
            self.executeGroupControl({'com':'stop', 'arg': false, 'confirm':false});
            self.checkDown();
        }
    }

    self.sleep = function (milliseconds) {
      var start = new Date().getTime();
      for (var i = 0; i < 1e7; i++) {
        if ((new Date().getTime() - start) > milliseconds){
          break;
        }
      }
    }

    self.clearGroupControl = function () {
        ko.utils.arrayForEach(self.applicationStates(), function(applicationState) {
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
    self.sort = function (header) {
        if (header.title == "Control") { return }  // ignore sorting on Control header

        //if this header was just clicked a second time...
        if (self.activeSort() == header && !self.holdSortDirection()) {
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

        self.applicationStates.sort(sortFunc);
        self.holdSortDirection(false);
    };

    self.clearSearch = function () {
        self.textFilter("");
    };

    // Custom Filtering
    self.customFilters = ko.observableArray([]);

    self.enabledCustomFilters = ko.computed(function() {
        return ko.utils.arrayFilter(self.customFilters(), function(customFilter) {
            return customFilter.enabled();
        });
    });

    self.customFilteredItems = ko.computed(function () {
        // first aggregate all items from all custom filters
        var allCustomFilteredItems = ko.observableArray([]);
        ko.utils.arrayForEach(self.enabledCustomFilters(), function(customFilter) { // loop over all enabled filters
            ko.utils.arrayForEach(customFilter.customFilteredItems(), function(item) {
                if (allCustomFilteredItems.indexOf(item) == -1) {
                    // only push unique items
                    allCustomFilteredItems.push(item);
                }
            });
        });

        // take the intersection of all the custom filtered items
        var intersection = ko.observableArray(allCustomFilteredItems().slice());
        ko.utils.arrayForEach(allCustomFilteredItems(), function(filteredItem) { // loop over all items
            ko.utils.arrayForEach(self.enabledCustomFilters(), function(customFilter) { // loop over all filters
                if (customFilter.customFilteredItems().indexOf(filteredItem) == -1) {
                    // remove the item if it is missing in any filter
                    intersection(intersection.remove(function(item) {return item != filteredItem}));
                }
            });
        });

        return intersection().slice();
    });

    // rate-limit how often filtered items are populated
    self.customFilteredItems.extend({rateLimit: 500});

    self.addCustomFilter = function() {
        var filter = new CustomFilter(ko, $, self);
        self.customFilters.push(filter);
    };

    self.clearAllFilters = function() {
        self.customFilters.removeAll();
    };

    self.remoteCustomFilters = ko.observableArray([]);
    self.fetchAllFilters = function() {
        var dict = {loginName : self.login.elements.username()};

        if (self.login.elements.authenticated()) {
            self.remoteCustomFilters.removeAll();
            $.getJSON("/api/filters/", dict, function(data) {
                $.each(data, function(index, filterDict) { 
                    var filter = new CustomFilter(ko, $, self);
                    filter.filterName(filterDict["name"]);
                    filter.parameter(filterDict["parameter"]);
                    filter.searchTerm(filterDict["searchTerm"]);
                    filter.inversed(filterDict["inversed"]);
                    filter.enabled(false);

                    self.remoteCustomFilters.push(filter);
                });
            }).fail(function(data){
                alert("Failed Get for all Filters " + JSON.stringify(data));
            });
        }
    };

    self.getFiltersForUser = ko.computed(function() {
        if (self.login.elements.authenticated) {
            self.fetchAllFilters();
        }
        else {
            self.remoteCustomFilters.removeAll();
        }
    });

    // Setup default filters
    self.defaultFilters = ko.observableArray([]);

    var downFilter = new CustomFilter(ko, $, self);
    downFilter.filterName("Down");
    downFilter.parameter(downFilter.parameters.applicationStatus);
    downFilter.searchTerm(downFilter.searchTerms.stopped);
    self.defaultFilters.push(downFilter);



    var errorFilter = new CustomFilter(ko, $, self);
    errorFilter.filterName("Error");
    errorFilter.parameter(errorFilter.parameters.errorState);
    errorFilter.searchTerm(errorFilter.searchTerms.error);
    self.defaultFilters.push(errorFilter);

    self.time = ko.observable(Date.now());
    self.filterByTime = ko.observable(false);
    self.enableTimeFilter = function() {
        //Reset filter time on double click
        if (self.filterByTime()){
            self.time(Date.now());
        }
        self.filterByTime(true);
        self.sortByTime();
    };

    self.timeToolTip = ko.computed(function() {
        if (self.filterByTime()){
            return "Click to clear old updates";
        }
        return "Click to enable update mode";
    });
    
    self.sortByTime = function() {
        var timeheader = {title: 'Time', sortPropertyName: 'mtime', asc: ko.observable(true)};
        self.activeSort(timeheader);
        self.sort(self.activeSort());
    };

    // Filtering from the search bar
    self.filteredItems = ko.dependentObservable(function() {
        var filter = self.textFilter().toLowerCase();
        // check for enabled custom filters, otherwise use global appStates array
        var ret;
        if (!filter && self.enabledCustomFilters().length == 0) {
            ret = self.applicationStates();
        } 
        else if(self.enabledCustomFilters().length > 0) {
            ret = ko.utils.arrayFilter(self.customFilteredItems(), function(item) {
                var re = new RegExp(filter, "i");
                return (item.configurationPath.match(re) || item.applicationHost().match(re));
            });
        } else {
            ret = ko.utils.arrayFilter(self.applicationStates(), function(item) {
                var re = new RegExp(filter, "i");
                return (item.configurationPath.match(re) || item.applicationHost().match(re));
            });
        }

        //filter for time last
        return ko.utils.arrayFilter(ret, function(item) {
            if(self.filterByTime()){
                return (item.mtime > self.time());
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
            ko.utils.arrayForEach(self.applicationStates(), function(appState) {
                appState.showDependencies(true);
            });
        }
        else {
            ko.utils.arrayForEach(self.applicationStates(), function(appState) {
                appState.showDependencies(false);
            });
        }
    });

    // view toggling
    self.currentView = ko.observable(self);
    self.views = ko.observableArray([]);
    self.views.push(self);

    // dependency maps
    self.dependencyMaps = new DependencyMaps(ko, $, d3, self);

    // create new app state
    self.createApplicationState = function(data) {
        return new ApplicationState(ko, data, self)
    };

    // handle updates from web server
    self.handleApplicationStatusUpdate = function (update) {
        // Search the array for row with matching path
        
        if (update.delete) {
            self.applicationStates.remove(function(currentRow) {
                return currentRow.configurationPath == update.configuration_path;
            });
        }
        else{
            var row = ko.utils.arrayFirst(self.applicationStates(), function (currentRow) {
                return currentRow.configurationPath == update.configuration_path;
            });
            if (row) {
                row.applicationStatus(update.application_status);
                row.startTime(update.start_time);
                row.applicationHost(update.application_host);
                row.errorState(update.error_state);
                row.mtime = Date.now();
            }
            else { 
                // add new item to array
                var newRow = self.createApplicationState(update);
                self.applicationStates.push(newRow);
            }
        }
    };

    self.handleApplicationDependencyUpdate = function (message) {
        $.each(message.application_dependencies, function() {
            var update = this;
            var row = ko.utils.arrayFirst(self.applicationStates(), function (currentRow) {
                return currentRow.configurationPath == update.configuration_path;
            });
            if (row) {
                row.setRequires(update)
            }
        });
    };

    self.fnReloadCaches = function () {
        if (confirm("Please confirm you want to clear and reload all server side caches by pressing OK.")) {
            var dict = {
                "command" : "all",
                "user": self.login.elements.username()
            };
            self.applicationStates.removeAll();
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

        self.environment(data.environment.toUpperCase());

        self.applicationStates(table);
        // sort initially on descending start time
        self.sort(self.activeSort());
    };

    var onApplicationStatesError = function (data) {
        alert('An Error has occurred while loading the application states.');
    };

    self.loadApplicationStates = function () {
        return service.get('api/application/states/',
                           onApplicationStatesSuccess, 
                           onApplicationStatesError);
    };

    var onApplicationDependenciesError = function (data) {
        alert('An Error has occurred while loading the application dependencies.');
    };

    self.loadApplicationDependencies = function () {
        return service.get('api/application/dependencies/',
                           self.handleApplicationDependencyUpdate, 
                           onApplicationDependenciesError);
    };

}});
