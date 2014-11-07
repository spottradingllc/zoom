define(['knockout'], function(ko) {
    return function DependencyModel(applicationStateArray, parentAppState) {
        var self = this;

        self.unknown = ko.observableArray([]).extend({rateLimit: 2000});
        self.holiday = ko.observableArray([]).extend({rateLimit: 2000});
        self.weekend = ko.observableArray([]).extend({rateLimit: 2000});
        self.zookeepergooduntiltime = ko.observableArray([]).extend({rateLimit: 2000});
        self.requires = ko.observableArray([]).extend({rateLimit: 2000});
        self.showDependencies = ko.observable(false);

        // maps a predicate type to an observable array
        var arrayMapping = {
            'holiday': self.holiday,
            'weekend': self.weekend,
            'zookeepergooduntiltime': self.zookeepergooduntiltime,
            'time': self.zookeepergooduntiltime,
            'zookeeperhaschildren': self.requires,
            'zookeeperhasgrandchildren': self.requires
        };

        // Dependency bubbling
        self.toggleDependencies = function() {
            self.showDependencies(!self.showDependencies());
        };

        self.handleUpdate = function(update) {
            parentAppState.mtime = Date.now();
            if (parentAppState.applicationHost() === '') { return; }

            // clear all dependencies
            for (var key in arrayMapping) {
                if (arrayMapping.hasOwnProperty(key)) {
                    arrayMapping[key].removeAll();
                }
            }

            update.dependencies.forEach(function(entry) {
                var neverFound = true;
                var predType = entry.type;
                var path = entry.path;

                // if path = /foo, match both /foo/bar and /foo/baz
                if (predType === 'zookeeperhasgrandchildren') {
                    ko.utils.arrayForEach(applicationStateArray(), function(applicationState) {
                        if (applicationState.configurationPath.substring(0, path.length) === path) {
                            self.requires.push(applicationState);
                            neverFound = false;
                        }
                    });
                }
                else if (predType === 'zookeeperhaschildren') {
                    var applicationState = ko.utils.arrayFirst(applicationStateArray(), function(applicationState) {
                        return (path === applicationState.configurationPath);
                    });
                    if (applicationState) {
                        neverFound = false;
                        self.requires.push(applicationState);
                    }
                }
                // if this predicate type exists in arrayMapping
                else if (typeof arrayMapping[predType] !== 'undefined') {
                    // push path to appropriate array based on predicate type
                    arrayMapping[predType].push(path);
                    neverFound = false;
                }
                else {
                    neverFound = false;
                }

                // Since the server only gets applications located in /spot/software/state/application,
                // this handles applications outside of that path that were added in the configuration
                if (neverFound) {
                    // 'simulate' an applicationState object - /classes/DependencyMaps and this file rely
                    // on having these attributes, at a minimum. We just want to display the missing app
                    // so this should be OK - but not ideal
                    var showAsMissing = {
                        'configurationPath': path,
                        'applicationStatusClass': parentAppState.glyphs.unknownQMark,
                        'applicationStatusBg': parentAppState.colors.unknownGray,
                        'applicationStatus': ko.observable(parentAppState.applicationStatuses.unknown),
                        'predType': predType,
                        'requires': ko.observableArray([]),
                        'errorState': ko.observable(parentAppState.errorStates.unknown)
                    };
                    self.requires.push(showAsMissing);
                }
            });
        };

        self.requirementsAreUp = ko.computed(function() {
            if (self.requires().length > 0) {
                for (var i = 0; i < self.requires().length; i++) {
                    if (self.requires()[i].applicationStatus() === parentAppState.applicationStatuses.stopped) {
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
            ko.utils.arrayForEach(applicationStateArray(), function(applicationState) {
                if (applicationState.dependencyModel.requires().indexOf(parentAppState) > -1) {
                    dependencies.push(applicationState);
                }
            });

            return dependencies().slice();
        }).extend({rateLimit: 2000});

        self.dependencyClass = ko.computed(function() {
            if (self.requires().length === 0 &&
                self.requiredBy().length === 0 &&
                self.holiday().length === 0 &&
                self.weekend().length === 0 &&
                self.zookeepergooduntiltime().length === 0) {
                return '';
            }
            else if (self.showDependencies()) {
                return 'caret';
            }
            else {
                return 'caret-left';
            }
        });

        self.dependencyPointer = ko.computed(function() {
            if (self.dependencyClass() !== '') {
                return 'pointer';
            }
            else {
                return '';
            }
        });
    };
});