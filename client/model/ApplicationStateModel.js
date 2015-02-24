define(
    [
        'knockout',
        'plugins/router',
        'service',
        'jquery',
        'jq-throttle',
        'model/environmentModel',
        'model/adminModel',
        'model/GlobalMode',
        'model/customFilterModel',
        'classes/ApplicationState',
        'classes/applicationStateArray',
        'classes/dependency-maps/DependencyMaps'
    ],
    function(ko, router, service, $, jqthrottle, environment, admin, GlobalMode,
             CustomFilterModel, ApplicationState, ApplicationStateArray, DependencyMaps) {
        return function ApplicationStateModel(login) {
            var self = this;
            self.login = login;
            self.admin = admin;
            self.globalMode = GlobalMode;
            self.applicationStateArray = ApplicationStateArray;
            self.textFilter = ko.observable('');
            self.textFilter.extend({ rateLimit: { method: "notifyWhenChangesStop", timeout: 700 } });
            self.environment = environment; 
            self.name = 'Application State Table';
            self.passwordConfirm = ko.observable('');
            self.options = {};
            self.buttonLabel = ko.observable('');
            self.groupMode = ko.observable(false);
            self.clickedApp = ko.observable({});
            self.customFilters = new CustomFilterModel(self);
            self.appsToShow = ko.observableArray([]);
            self.forceRestart = ko.observable(false);
            self.showRestartCheckbox = ko.observable(false);

            self.headers = [
                {title: 'Up/Down', sortPropertyName: 'applicationStatus', asc: ko.observable(true)},
                {title: 'Application ID', sortPropertyName: 'configurationPath', asc: ko.observable(true)},
                {title: 'Host', sortPropertyName: 'applicationHost', asc: ko.observable(true)},
                {title: 'Trigger Time', sortPropertyName: 'triggerTime', asc: ko.observable(false)},
                {title: 'Completion Time', sortPropertyName: 'completionTime', asc: ko.observable(false)},
                {title: 'Status', sortPropertyName: 'errorState', asc: ko.observable(true)},
                {title: 'Control', sortPropertyName: 'control', asc: ko.observable(true)},
                {title: 'Admin', sortPropertyName: 'admin', asc: ko.observable(true)}
            ];

            // callback for groupCheckModal to set forcedRestart to false, password input to empty string,
            // remove "incorrect password" popover if shown, collapse the Advanced Option accordion
            $(document).on('show.bs.modal', '#groupCheckModal', function() {
                self.forceRestart(false);
                self.passwordConfirm('')
                $('#passwordFieldG').popover('destroy');
                $("#advancedOptionsBody").collapse('hide');
            });

            self.showHeader = function(index) {
                if (self.headers[index].title === 'Control' && !self.login.elements.authenticated()) {
                    return false;
                }
                return !(self.headers[index].title === 'Admin' && !self.admin.enabled());

            };

            self.showSentinelConfig = function(hostname) {
                router.navigate('#config/' + hostname(), {trigger: true });
            };

            // control agent
            self.isHostEmpty = function() {
                if (self.clickedApp.applicationHost === '') {
                    swal('Cannot control an agent with an empty host.');
                    return true;
                }
                else {
                    return false;
                }
            };

            self.executeSingleControl = function(options) {
                if (!self.isHostEmpty()) {
                    var dict = {
                        'componentId': self.clickedApp().componentId,
                        'applicationHost': self.clickedApp().applicationHost,
                        'command': options.com,
                        'stay_down': options.stay_down,
                        'user': self.login.elements.username()
                    };
                    $.post('/api/agent/', dict, function() {
                        $('#groupCheckModal').modal('hide');
                    })
                        .fail(function(data) {
                            swal('Error Posting ControlAgent.', JSON.stringify(data), 'error');
                        });
                }
                self.clearGroupControl();
            };

            // Takes in 'options' as an argument and actually sends a command to the server
            self.executeGroupControl = function(options) {
                ko.utils.arrayForEach(self.groupControl(), function(applicationState) {
                    var dict = {
                        'componentId': applicationState.componentId,
                        'configurationPath': applicationState.configurationPath,
                        'applicationHost': applicationState.applicationHost,
                        'command': options.com,
                        'stay_down': options.stay_down,
                        'user': self.login.elements.username()
                    };

                    if (self.isHostEmpty()) {
                        swal('Empty host', 'Skipping the agent with configuration path ' + applicationState.configurationPath);
                    }
                    else {
                        $.post('/api/agent/', dict).fail(function(data) {
                            swal('Error Posting Group Control.', JSON.stringify(data), 'error');
                        });
                    }
                });

                if (options.clear_group) {
                    self.clearGroupControl();
                }
            };

            // Replaces dep_restart by checking self.options. Will also call every other command by passing
            // through self.options to executeGroupControl or executeSingleControl
            // *Note*: 'ignore' is sent before 'stop' so that services on react won't start up if they stopped
            // before all the other selected services stopped.
            self.determineAndExecute = function() {
                // Command send to single server
                if (!self.groupMode()){
                    if (self.options.com === 'restart' && !self.forceRestart()) {
                        // dep_restart
                        self.executeSingleControl({'com': 'ignore', 'clear_group': true});
                        self.executeSingleControl({'com': 'stop', 'stay_down': false, 'clear_group': true});
                        self.checkStopped();
                    }
                    else {
                        self.executeSingleControl(self.options);
                    }
                }
                else {
                    if (self.options.com === 'restart' && !self.forceRestart()) {
                        // dep_restart
                        self.executeGroupControl({'com': 'ignore', 'clear_group': false});
                        self.executeGroupControl({'com': 'stop', 'stay_down': false, 'clear_group': false});
                        self.checkStopped();
                    }
                    else {
                        self.executeGroupControl(self.options);
                    }
                }

                $('#groupCheckModal').modal('hide');
            };

            self.disallowAction = function() {
                $('#passwordFieldG').popover('show');
            };

            // Re-checks password and provides success and failure functions to $.post
            self.submitAction = function() {
                // client-side blank password check
                if ('' === self.passwordConfirm()) {
                    return self.disallowAction();
                }

                var params = {
                    username: self.login.elements.username(),
                    password: self.passwordConfirm()
                };

                return $.post('/login', JSON.stringify(params), self.determineAndExecute).fail(self.disallowAction);
            };

            self.parseAppName = function(path) {
                if (typeof path === 'undefined') {
                    return;
                }

                return path.split('application/')[1];
            };

            // functions/variables for group control of agents
            self.groupControl = ko.observableArray([]);

            self.controlAgent = function(options, clickedApp) {
                // options.com: command
                // options.stay_down: stay_down

                // if no provided individual, this is a group
                if (typeof clickedApp === 'undefined') {
                    self.groupMode(true);
                }
                else {
                    self.clickedApp(clickedApp);
                    self.groupMode(false);
                }

                self.buttonLabel('Send ' + options.com.toUpperCase() + ' command');
                self.options = options;

                if (options.com == "restart") {
                    self.showRestartCheckbox(true)
                }
                else {
                    self.showRestartCheckbox(false)
                }

                $('#groupCheckModal').modal('show');
            };


            self.checkEnter = function(d, e) {
                if (e.which === 13) {
                    $('#Gsend').trigger('click');
                    return false;
                }
                return true;
            };

            // Checks if all groupControl services are down. Used in self.determineAndExecute
            var interval = 0;
            self.checkStopped = function() {
                clearInterval(interval);

                if (!self.groupMode()) {
                    var clickedAppState = self.getClickedAppState()
                    // true if app is not stopped and false if app is stopped
                    appsNotStopped = (clickedAppState.applicationStatus() !== 'stopped');
                }
                else{
                    var appsNotStopped = ko.utils.arrayFirst(self.groupControl(), function(item) {
                        return item.applicationStatus() !== 'stopped';
                    });
                }

                if (appsNotStopped) {
                    interval = setInterval(self.checkStopped, 5000);
                } else {
                    // all selected apps stopped
                    self.sendDepRestart()
                }
            };

            self.sendDepRestart = function() {
                // needs to sleep so that stop command gets put into the agent's queue first
                // TODO: a better alternative to ensure stop gets called first
                self.sleep(500)
                if (!self.groupMode()){
                    self.executeSingleControl({'com': 'dep_restart', 'stay_down': false, 'clear_group': true});
                }
                // no need to send swal alert for single service. Just send dep_restart right away
                else if (self.groupControl().length === 1){
                     self.executeGroupControl({'com': 'dep_restart', 'stay_down': false, 'clear_group': true});
                }
                else{
                    swal('Dependency Restart', 'All selected applications are now shut down. These applications will react to changes in ZooKeeper and start up organically.');
                    self.executeGroupControl({'com': 'dep_restart', 'arg': false, 'clear_group': true});
                }
            };

            self.sleep = function(milliseconds) {
                var start = new Date().getTime();
                for (var i = 0; i < 1e7; i++) {
                    if ((new Date().getTime() - start) > milliseconds) {
                        break;
                    }
                }
            };

            // Returns the Application State of the single service to check if the status is down
            // before sending a dep_restart to avoid race condition
            self.getClickedAppState = function() {
                var clickedAppState
                ko.utils.arrayForEach(self.applicationStateArray(), function(item){
                    if (item.componentId == self.clickedApp().componentId){
                        clickedAppState = item
                    }
                })
                // TODO: if clickedAppState is empty
                return clickedAppState
            };


            self.clearGroupControl = function() {
                ko.utils.arrayForEach(self.applicationStateArray(), function(applicationState) {
                    if (self.groupControl.indexOf(applicationState) > -1) {
                        self.groupControl.remove(applicationState);
                    }
                });
            };

            self.filteredGroupControl = function() {
                ko.utils.arrayForEach(self.filteredItems(), function(applicationState) {
                    if (self.groupControl.indexOf(applicationState) === -1) {
                        self.groupControl.push(applicationState);
                    }
                });
            };

            // Sorting
            self.activeSort = ko.observable(self.headers[4]); // set the default sort by start time
            self.holdSortDirection = ko.observable(true); // hold the direction of the sort on updates
            self.sort = function(header, initialRun) {
                if (header.title === 'Control') {
                    return;
                }  // ignore sorting on Control header

                // initialRun == true if self.sort is called on page initialization
                if (typeof initialRun === 'undefined' || typeof initialRun === 'object') {
                    initialRun = false;
                }

                // if this header was just clicked a second time...
                if (self.activeSort() === header && !self.holdSortDirection() && !initialRun) {
                    header.asc(!header.asc()); // ...toggle the direction of the sort
                } else {
                    self.activeSort(header); // first click, remember it
                }

                var prop = self.activeSort().sortPropertyName;

                var ascSort = function(a, b) {
                    var aprop = ko.unwrap(a[prop]);
                    var bprop = ko.unwrap(b[prop]);
                    return aprop < bprop ? -1 : aprop > bprop ? 1 : aprop === bprop ? 0 : 0;
                };
                var descSort = function(a, b) {
                    return ascSort(b, a);
                };
                var sortFunc = self.activeSort().asc() ? ascSort : descSort;

                self.applicationStateArray.sort(sortFunc);
                if (!initialRun) {
                    self.holdSortDirection(false);
                }
            };

            self.clearSearch = function() {
                self.textFilter('');
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
                if (!filter && self.customFilters.enabled().length === 0) {
                    ret = self.applicationStateArray();
                }
                else if (self.customFilters.enabled().length > 0) {
                    ret = ko.utils.arrayFilter(self.customFilters.allMatchedItems(), function(item) {
                        var re = new RegExp(filter, 'i');
                        return (item.configurationPath.match(re) || item.applicationHost().match(re));
                    });
                } else {
                    ret = ko.utils.arrayFilter(self.applicationStateArray(), function(item) {
                        var re = new RegExp(filter, 'i');
                        return (item.configurationPath.match(re) || item.applicationHost().match(re));
                    });
                }

                // filter for time last
                return ko.utils.arrayFilter(ret, function(item) {
                    if (self.customFilters.filterByTime()) {
                        return (item.mtime > self.customFilters.time());
                    } else {
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
                ko.utils.arrayForEach(self.applicationStateArray(), function(appState) {
                    appState.dependencyModel.showDependencies(true);
                });
                self.showingAllDependencies(true);
            };
            self.collapseAllDependencies = function() {
                ko.utils.arrayForEach(self.applicationStateArray(), function(appState) {
                    appState.dependencyModel.showDependencies(false);
                });
                self.showingAllDependencies(false);
            };

            // view toggling
            self.currentView = ko.observable(self);
            self.views = ko.observableArray([]);
            self.views.push(self);
            
            self.displaySize = ko.observable("");
            
            self.numRows = function () {
                // if the object in the current view has the same name as self
                if (self.currentView().constructor.name === self.constructor.name){
                    var totalY = $(window).height();
                    var rowY = 32; //each row is roughly 32 px high
                    var newSize = totalY/rowY;

                    // only update if new size is larger than current
                    if (newSize > self.displaySize()){
                        self.displaySize(newSize);
                    }
                }
            };

            self.numRows();

            $(window).resize($.throttle(300, self.numRows));

            self.showOnlyVisible = ko.computed(function () {
                    self.appsToShow(self.filteredItems().slice(0, self.displaySize()));
            });
            
            self.autoLoad = $(document).bind('mousewheel', function() {
                    if (self.currentView().constructor.name === self.constructor.name){
                    var diff = $(window).scrollTop() + $(window).height() - $(document).height();
                    // when zoomed, the diff can sometimes drift as far as 2 pixels off
                    // root cause is not known - but likely a Chrome bug
                    // http://bit.ly/1szF52q
                    if (diff > -3) {
                            // add a few rows
                            var add_size = 3;
                            var new_size = 0;
                            new_size = self.displaySize() + add_size;
                            self.displaySize(Math.min(self.applicationStateArray().length, new_size)); 
                        }
                    }
            });


            // dependency maps
            self.dependencyMaps = new DependencyMaps(self);

            // create new app state
            self.createApplicationState = function(data) {
                return new ApplicationState(data, self);
            };

            // handle updates from web server
            self.handleApplicationStatusUpdate = function(update) {
                // Search the array for row with matching path

                if (update.delete) {
                    self.applicationStateArray.remove(function(currentRow) {
                        return currentRow.configurationPath === update.configuration_path;
                    });
                }
                else {
                    var row = ko.utils.arrayFirst(self.applicationStateArray(), function(currentRow) {
                        return currentRow.configurationPath === update.configuration_path;
                    });
                    if (row) {
                        row.applicationStatus(update.application_status);
                        row.completionTime(update.completion_time);
                        row.triggerTime(update.trigger_time);
                        row.applicationHost(update.application_host);
                        row.errorState(update.error_state);
                        row.mode(update.local_mode);
                        row.mtime = Date.now();
                        row.loginUser(update.login_user);
                        row.readOnly(update.read_only);
                        row.lastCommand(update.last_command);
                        row.pdDisabled(update.pd_disabled);
                        row.grayed(update.grayed);
                        row.platform(update.platform);
                    }
                    else {
                        // add new item to array
                        var newRow = self.createApplicationState(update);
                        self.applicationStateArray.push(newRow);
                    }
                }
            };

            self.handleApplicationDependencyUpdate = function(message) {
                $.each(message.application_dependencies, function() {
                    var update = this;
                    var row = ko.utils.arrayFirst(self.applicationStateArray(), function(currentRow) {
                        return currentRow.configurationPath === update.configuration_path;
                    });
                    if (row) {
                        row.dependencyModel.handleUpdate(update);
                    }
                });
            };

            self.reloadCaches = function() {
                if (confirm('Please confirm you want to clear and reload all server side caches by pressing OK.')) {
                    var dict = {
                        'command': 'all',
                        'user': self.login.elements.username()
                    };
                    self.applicationStateArray.removeAll();
                    $.post('/api/cache/reload/', dict, function(data) {
                        swal(data);
                    }).fail(function(data) {
                        swal('Error Posting Clear Cache.', JSON.stringify(data), 'error');
                    });
                }
            };

            var onApplicationStatesSuccess = function(data) {
                var table = $.map(data.application_states, function(row) {
                    return self.createApplicationState(row);
                });

                self.applicationStateArray(table);
                // sort initially on descending start time - initial run so give true param
                self.sort(self.activeSort(), true);
            };

            var onApplicationStatesError = function(data) {
                swal('Well shoot...', 'An Error has occurred while loading the application states.', 'error');
            };

            self.loadApplicationStates = function() {
                return service.synchronousGet('api/application/states',
                    onApplicationStatesSuccess,
                    onApplicationStatesError);
            };

            var onApplicationDependenciesError = function(data) {
                swal('Well shoot...', 'An Error has occurred while loading the application dependencies.', 'error');
            };

            self.loadApplicationDependencies = function() {
                return service.synchronousGet('api/application/dependencies',
                    self.handleApplicationDependencyUpdate,
                    onApplicationDependenciesError);
            };

        };
    });
