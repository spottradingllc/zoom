function ApplicationStateModel(service, ko, $) {
    var self = this;

    self.applicationStates = ko.observableArray([]);
    self.textFilter = ko.observable("");

    self.headers = [
        {title: 'Up/Down', sortPropertyName: 'applicationStatus', asc: ko.observable(true)},
        {title: 'Configuration Path', sortPropertyName: 'configurationPath', asc: ko.observable(true)},
        {title: 'Host', sortPropertyName: 'applicationHost', asc: ko.observable(true)},
        {title: 'Start Time', sortPropertyName: 'startTime', asc: ko.observable(false)},
        {title: 'Status', sortPropertyName: 'errorState', asc: ko.observable(true)},
        {title: 'Control', sortPropertyName: 'control', asc: ko.observable(true)}
    ];

    // functions/variables for group control of agents
    self.groupControl = ko.observableArray([]);
    self.executeGroupControl = function (com) {
        var confirmString = ["Please confirm that you want to send a " + com + " command to the ",
                self.groupControl().length + " selected agents by pressing OK."].join('\n');
        confirmString = confirmString.replace(/(\r\n|\n|\r)/gm, "");

        if (confirm(confirmString)) {
            ko.utils.arrayForEach(self.groupControl(), function(applicationState) {
                var dict = {"configurationPath": applicationState.configurationPath,
                            "applicationHost": applicationState.applicationHost,
                            "command": com};

                if (applicationState.isHostEmpty()) {
                    alert("Skipping the agent with configuration path " + application.configurationPath + ": empty host.");
                }
                else {
                    $.post("/api/control_agent/", dict);
                }
            });
        }
    };

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
        var filter = new CustomFilter(ko, self);
        self.customFilters.push(filter);
    };
    self.clearAllFilters = function() {
        self.customFilters.removeAll();
    }

    // Filtering from the search bar
    self.filteredItems = ko.dependentObservable(function() {
        var filter = self.textFilter().toLowerCase();
        // check for enabled custom filters, otherwise use global appStates array
        if (!filter && self.enabledCustomFilters().length == 0) {
            return self.applicationStates();
        } 
        else if(self.enabledCustomFilters().length > 0) {
            return ko.utils.arrayFilter(self.customFilteredItems(), function(item) {
                var re = new RegExp(filter, "i");
                return (item.configurationPath.match(re) || item.applicationHost().match(re));
            });
        } else {
            return ko.utils.arrayFilter(self.applicationStates(), function(item) {
                var re = new RegExp(filter, "i");
                return (item.configurationPath.match(re) || item.applicationHost().match(re));
            });
        }
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

    var onApplicationStatesSuccess = function (data) {
        var table = $.map(data.application_states, function (row) {
            return new ApplicationState(ko, row, self)
        });

        self.applicationStates(table);

        // sort initially on descending start time
        self.sort(self.activeSort());
    };

    var onApplicationStatesError = function (data) {
        alert('An Error has occurred while loading the application states.');
    };

    self.loadApplicationStates = function () {
        return service.get('api/get_application_states/', onApplicationStatesSuccess, onApplicationStatesError);
    };

    self.loadApplicationStates();  // load initial data

}
