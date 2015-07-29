define(['jquery', 'knockout', 'model/constants'], function($, ko, constants) {
    return function CustomFilter(parent, appStateModel) {
        var self = this;
        // trickle-down dictionaries
        self.parameters = {
            applicationStatus: 'applicationStatus',
            configurationPath: 'configurationPath',
            applicationHost: 'applicationHost',
            errorState: 'errorState',
            dependency: 'dependency',
            upstream: 'upstream',
            downstream: 'downstream'
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

        self.filterOptions = ko.observableArray([
            {'term': String([constants.errorStates.ok, constants.errorStates.started, constants.errorStates.stopped]), 'glyph': constants.glyphs.thumpsUp, 'desc': 'Working as expected'},
            {'term': constants.errorStates.starting, 'glyph': constants.glyphs.startingRetweet, 'desc': 'Apps that are starting'},
            {'term': constants.errorStates.stopping, 'glyph': constants.glyphs.stoppingDown, 'desc': 'Apps that are stopping.'},
            {'term': constants.errorStates.error, 'glyph': constants.glyphs.errorWarning, 'desc': 'Apps that have failed to start/stop'},
            {'term': constants.errorStates.unknown, 'glyph': constants.glyphs.unknownQMark, 'desc': 'Apps whose sentinel is disconnected from Zookeeper'},
            {'term': self.searchTerms.grayed, 'glyph': constants.glyphs.grayed, 'desc': 'Apps that are grayed out'},
            {'term': self.searchTerms.pdDisabled, 'glyph': constants.glyphs.pdWrench, 'desc': 'Apps that have Zoom PagerDuty alerts disabled'},
            {'term': self.searchTerms.readOnly, 'glyph': constants.glyphs.readOnly, 'desc': 'Apps that are read only (not started in Zoom)'},
            {'term': constants.errorStates.staggered, 'glyph': constants.glyphs.staggeredClock, 'desc': 'Apps that are staggered'},
            {'term': constants.errorStates.notify, 'glyph': constants.glyphs.notifyExclamation, 'desc': 'Apps that have crashed.'},
            {'term': constants.errorStates.invalid, 'glyph': constants.glyphs.invalidTrash, 'desc': 'Apps that are invalid (do not match anything in their sentinel configs)'}
        ]);

        // member variables and getters/setters
        self.filterName = ko.observable('');
        self.parameter = ko.observable('');
        self.searchTerm = ko.observable('');
        self.searchTerm.extend({ rateLimit: { method: "notifyWhenChangesStop", timeout: 500 } });
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

        self.glyph = ko.computed(function() {
            var fb = ko.utils.arrayFirst(self.filterOptions(), function(f) {return f.term === self.searchTerm()});
            if (fb !== null) { return fb.glyph }
            else {return ""}
        });

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
                // array passed in for 'ok' filter as searchTerm
                if (self.searchTerm().indexOf(appParameter) > -1 && !self.inversed()) {
                    self.pushMatchedItem(appState);
                }
                else if (self.searchTerm().indexOf(appParameter) === -1 && self.inversed()) {
                    self.pushMatchedItem(appState);
                }
            }
        };

        self.applyBoolFilter = function(param, appState) {
            // assuming these are ko.observables that are booleans
            if (appState[param]() && !self.inversed()) {
                self.pushMatchedItem(appState);
            }
            else if (!appState[param]() && self.inversed()) {
                self.pushMatchedItem(appState);
            }
        };

        self.applyDependencyFilter = function(appState) {
            if (self.parameter() === self.parameters.upstream && !self.inversed()) {
                ko.utils.arrayForEach(appState.dependencyModel.upstream(), function(requirement) {
                    if (requirement.state.configurationPath.indexOf(self.searchTerm()) > -1 && !self.inversed()) {
                        self.pushMatchedItem(appState);
                    }
                });
            }
            else if (self.parameter() === self.parameters.downstream && !self.inversed()) {
                ko.utils.arrayForEach(appState.dependencyModel.downstream(), function(dependent) {
                    if (dependent.indexOf(self.searchTerm()) > -1 && !self.inversed()) {
                        self.pushMatchedItem(appState);
                    }
                });
            }
            else if (self.parameter() === self.parameters.upstream && self.inversed()) {
                // generate an array of the config paths of each requirement
                var requirementConfigPaths = ko.utils.arrayMap(appState.dependencyModel.upstream(), function(requirement) {
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
            else { // (self.parameter() == 'downstream' && self.inversed()) case
                // generate an array of the config paths of each dependent
                ko.utils.arrayMap(appState.dependencyModel.downstream(), function(dependent) {
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
                swal('Missing filter name', 'You must enter a filter name in order to save the filter remotely.', 'error');
            }
            else {
                $.post('/api/filters/', dict, function(data) {
                    swal(data);
                }).fail(function(data) {
                    var res = JSON.parse(data.responseText);
                    swal('Error Posting Save Filter', res.errorText, 'error');
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
                swal(returnData);
            }).fail(function(data) {
                var res = JSON.parse(data.responseText);
                swal('Error Posting Delete Filter', res.errorText, 'error');
            });

        };

        self.canBeAlteredRemotely = ko.computed(function() {
            return !!(self.parameter() !== '' && self.searchTerm() !== '');
        });
    };
});
