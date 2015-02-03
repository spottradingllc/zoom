define(['jquery', 'knockout'], function($, ko) {
    return function CustomFilter(parent, appStateModel) {
        var self = this;
        // trickle-down dictionaries
        self.parameters = {
            applicationStatus: 'applicationStatus',
            configurationPath: 'configurationPath',
            applicationHost: 'applicationHost',
            errorState: 'errorState',
            dependency: 'dependency',
            requires: 'requires',
            requiredBy: 'requiredBy',
            weekend: 'weekend'
        };

        self.searchTerms = {
            running: 'running',
            stopped: 'stopped',
            unknown: 'unknown',
            ok: 'ok',
            starting: 'starting',
            stopping: 'stopping',
            error: 'error',
            pdDisabled: 'pdDisabled',
            grayed: 'grayed',
            readOnly: 'readOnly'
        };

        // member variables and getters/setters
        self.filterName = ko.observable('');
        self.parameter = ko.observable('');
        self.searchTerm = ko.observable('');
        self.enabled = ko.observable(false);
        self.inversed = ko.observable(false);
        self.matchedItems = ko.observableArray([]);

        self.tearDown = function() {
            self.searchTerm('');
            self.enabled(false);
            self.inversed(false);
            self.matchedItems.removeAll();
        };

        self.setParameter = function(param) {
            self.parameter(param);
            self.tearDown();
        };

        self.setSearchTerm = function(term) {
            self.searchTerm(term);
        };

        // tear down the filter whenever the search term is blank
        self.searchTerm.subscribe(function(term) {
            self.enabled(true);
            if (term == '') {
                self.tearDown();
            }
        });

        self.toggleEnabled = function() {
            self.enabled(!self.enabled());
        };

        self.toggleInversed = function() {
            self.inversed(!self.inversed());
        };

        self.deleteFilter = function() {
            parent.all.remove(self);
        };

        self.openFilter = function() {
            parent.all.push(self);
        };

        // Filtering operations
        self.pushMatchedItem = function(item) {
            // push only unique items
            if (self.matchedItems.indexOf(item) === -1) {
                self.matchedItems.push(item);
            }
        };

        self.applyFilter = ko.computed(function() {
            self.matchedItems.removeAll();

            if (self.enabled() && appStateModel.applicationStateArray) {
                // check each application state for matches, perform appropriate filtering technique
                ko.utils.arrayForEach(appStateModel.applicationStateArray(), function(appState) {

                    if (self.parameter() === self.parameters.applicationStatus) {
                        self.applyLogicalFilter(appState.applicationStatus().toLowerCase(), appState);
                    }
                    else if (self.parameter() === self.parameters.configurationPath) {
                        self.applyLogicalFilter(appState.configurationPath, appState);
                    }
                    else if (self.parameter() === self.parameters.applicationHost) {
                        self.searchTerm(self.searchTerm().toUpperCase());
                        self.applyLogicalFilter(appState.applicationHost().toUpperCase(), appState);
                    }
                    else if (self.parameter() === self.parameters.weekend) {
                        self.applyWeekendFilter(appState);
                    }
                    else if (self.parameter() === self.parameters.errorState) {
                        // these are separate variables (do not map to errorState) but they are visible in the 'Status' column
                        if (self.searchTerm() === self.searchTerms.pdDisabled || self.searchTerm() === self.searchTerms.grayed ||
                            self.searchTerm() === self.searchTerms.readOnly) {
                            self.applyBoolFilter(self.searchTerm(), appState);
                        }
                        else {
                            self.applyLogicalFilter(appState.errorState().toLowerCase(), appState);
                        }

                    }
                    else { // perform dependency filtering
                        self.applyDependencyFilter(appState);
                    }
                });
            }
        });

        self.applyLogicalFilter = function(appParameter, appState) {
            if (typeof self.searchTerm() == 'string'){
                if (appParameter.indexOf(self.searchTerm()) > -1 && !self.inversed()) {
                    self.pushMatchedItem(appState);
                }
                else if (appParameter.indexOf(self.searchTerm()) === -1 && self.inversed()) {
                    self.pushMatchedItem(appState);
                }
            }
            else{
                // array passed in for 'ok' filter
                for (var i = 0; i < self.searchTerm().length; i++) {
                    if (appParameter.indexOf(self.searchTerm()[i]) > -1 && !self.inversed()) {
                        self.pushMatchedItem(appState);
                    }
                    else if (appParameter.indexOf(self.searchTerm()[i]) === -1 && self.inversed()) {
                        self.pushMatchedItem(appState);
                    }
                }
            }
        };


        self.applyWeekendFilter = function(appState) {
            var push = false;
            if (appState.dependencyModel.weekend().length > 0) {
                // if the item doesn't have 'NOT' in it, and it's not inversed, match it
                if (appState.dependencyModel.weekend()[0].indexOf('NOT') === -1 && !self.inversed()) {
                    push = true;
                }
                // if the item does have 'NOT' in it, and IS inversed, match it
                else if (appState.dependencyModel.weekend()[0].indexOf('NOT') > -1 && self.inversed()) {
                    push = true;
                }
            }
            else if (!self.inversed()) {  // if not specified, it can run on weekend
                push = true;
            }

            if (push) { self.pushMatchedItem(appState); }

        };

        self.applyBoolFilter = function (param, appState) {
            // assuming these are ko.observables that are booleans
            if (appState[param]() && !self.inversed()) {
                self.pushMatchedItem(appState);
            }
            else if (!appState[param]() && self.inversed()) {
                self.pushMatchedItem(appState);
            }
        };

        self.applyDependencyFilter = function(appState) {
            if (self.parameter() === self.parameters.requires && !self.inversed()) {
                ko.utils.arrayForEach(appState.dependencyModel.requires(), function(requirement) {
                    if (requirement.state.configurationPath.indexOf(self.searchTerm()) > -1 && !self.inversed()) {
                        self.pushMatchedItem(appState);
                    }
                });
            }
            else if (self.parameter() === self.parameters.requiredBy && !self.inversed()) {
                ko.utils.arrayForEach(appState.dependencyModel.requiredBy(), function(dependent) {
                    if (dependent.configurationPath.indexOf(self.searchTerm()) > -1 && !self.inversed()) {
                        self.pushMatchedItem(appState);
                    }
                });
            }
            else if (self.parameter() === self.parameters.requires && self.inversed()) {
                // generate an array of the config paths of each requirement
                var requirementConfigPaths = ko.utils.arrayMap(appState.dependencyModel.requires(), function(requirement) {
                    return requirement.state.configurationPath;
                });

                // check if any required config path contains the search term
                var matchingConfigPath = ko.utils.arrayFirst(requirementConfigPaths, function(configPath) {
                    return (configPath.indexOf(self.searchTerm()) > -1);
                });

                // if no required config path contains the search term, push the application state
                if (!matchingConfigPath) {
                    self.pushMatchedItem(appState);
                }
            }
            else { // (self.parameter() == 'requiredBy' && self.inversed()) case
                // generate an array of the config paths of each dependent
                ko.utils.arrayMap(appState.dependencyModel.requiredBy(), function(dependent) {
                    return dependent.configurationPath;
                });

                // if no dependent config path contains the search term, push the application state
                if (!matchingConfigPath) {
                    self.pushMatchedItem(appState);
                }
            }
        };

        // Operations for remote saving/deleting
        self.saveFilterRemotely = function() {
            var dict = {
                operation: 'add',
                name: self.filterName(),
                loginName: appStateModel.login.elements.username(),
                parameter: self.parameter(),
                searchTerm: self.searchTerm(),
                inversed: self.inversed()
            };

            if (self.filterName() === '') {
                alert('You must enter a filter name in order to save the filter remotely.');
            }
            else {
                $.post('/api/filters/', dict, function(data) {
                    alert(data);
                }).fail(function(data) {
                    alert('Error Posting Save Filter ' + JSON.stringify(data));
                });
            }
        };

        self.deleteFilterRemotely = function() {
            var dict = {
                operation: 'remove',
                name: self.filterName(),
                loginName: appStateModel.login.elements.username(),
                parameter: self.parameter(),
                searchTerm: self.searchTerm(),
                inversed: self.inversed()
            };
            $.post('/api/filters/', dict, function(returnData) {
                alert(returnData);
            }).fail(function(data) {
                alert('Error Posting Delete Filter ' + JSON.stringify(data));
            });

        };

        self.canBeAlteredRemotely = ko.computed(function() {
            return !!(self.parameter() !== '' && self.searchTerm() !== '');
        });
    };
});
