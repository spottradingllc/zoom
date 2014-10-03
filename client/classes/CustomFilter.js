define(['jquery', 'knockout'], function($, ko) {
    return function CustomFilter(parent, appStateModel) {
        var self = this;
        // trickle-down dictionaries
        self.parameters = {
            applicationStatus: 'applicationStatus',
            configurationPath: 'configurationPath',
            applicationHost: 'applicationHost',
            triggerTime: 'triggerTime',
            completionTime: 'completionTime',
            errorState: 'errorState',
            dependency: 'dependency',
            requires: 'requires',
            requiredBy: 'requiredBy'
        };

        self.searchTerms = {
            running: 'running',
            stopped: 'stopped',
            unknown: 'unknown',
            ok: 'ok',
            starting: 'starting',
            stopping: 'stopping',
            error: 'error'
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
                    else if (self.parameter() === self.parameters.triggerTime) {
                        self.applyLogicalFilter(appState.triggerTime().toLowerCase(), appState);
                    }
                    else if (self.parameter() === self.parameters.completionTime) {
                        self.applyLogicalFilter(appState.completionTime().toLowerCase(), appState);
                    }
                    else if (self.parameter() === self.parameters.errorState) {
                        self.applyLogicalFilter(appState.errorState().toLowerCase(), appState);
                    }
                    else { // perform dependency filtering
                        self.applyDependencyFilter(appState);
                    }
                });
            }
        });

        self.applyLogicalFilter = function(appParameter, appState) {
            if (appParameter.indexOf(self.searchTerm()) > -1 && !self.inversed()) {
                self.pushMatchedItem(appState);
            }
            else if (appParameter.indexOf(self.searchTerm()) === -1 && self.inversed()) {
                self.pushMatchedItem(appState);
            }
        };

        self.applyDependencyFilter = function(appState) {
            if (self.parameter() === self.parameters.requires && !self.inversed()) {
                ko.utils.arrayForEach(appState.requires(), function(requirement) {
                    if (requirement.configurationPath.indexOf(self.searchTerm()) > -1 && !self.inversed()) {
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
                var requirementConfigPaths = ko.utils.arrayMap(appState.requires(), function(requirement) {
                    return requirement.configurationPath;
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
