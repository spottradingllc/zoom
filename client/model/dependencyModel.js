define(['knockout', 'model/constants'], function(ko, constants) {
    return function DependencyModel(applicationStateArray, parentAppState) {
        var self = this;

        self.unknown = ko.observableArray([]).extend({rateLimit: 2000});
        self.holiday = ko.observableArray([]).extend({rateLimit: 2000});
        self.weekend = ko.observableArray([]).extend({rateLimit: 2000});
        self.zookeepergooduntiltime = ko.observableArray([]).extend({rateLimit: 2000});
        self.requires = ko.observableArray([]).extend({rateLimit: 2000});
        self.newRequires = ko.observableArray([]).extend({rateLimit: 2000});
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
//            parentAppState.mtime = Date.now();
//            if (parentAppState.applicationHost() === '') { return; }
//
//            // clear all dependencies
//            for (var key in arrayMapping) {
//                if (arrayMapping.hasOwnProperty(key)) {
//                    arrayMapping[key].removeAll();
//                }
//            }
//
//            update.dependencies.forEach(function(entry) {
//                var neverFound = true;
//                var predType = entry.type;
//                var path = entry.path;
//                var operational = entry.operational;
//
//                // if path = /foo, match both /foo/bar and /foo/baz
//                if (predType === constants.predicateTypes.ZooKeeperHasGrandChildren) {
//                    ko.utils.arrayForEach(applicationStateArray(), function(applicationState) {
//                        if (applicationState.configurationPath.substring(0, path.length) === path) {
//                            self.requires.push({'state': applicationState, 'operational': operational});
//                            neverFound = false;
//                        }
//                    });
//                }
//                else if (predType === constants.predicateTypes.ZooKeeperHasChildren) {
//                    var applicationState = ko.utils.arrayFirst(applicationStateArray(), function(applicationState) {
//                        return (path === applicationState.configurationPath);
//                    });
//                    if (applicationState) {
//                        neverFound = false;
//                        self.requires.push({'state': applicationState, 'operational': operational});
//                    }
//                }
//                // if this predicate type exists in arrayMapping
//                else if (typeof arrayMapping[predType] !== 'undefined') {
//                    // push path to appropriate array based on predicate type
//                    arrayMapping[predType].push({'state': path, 'operational': operational});
//                    neverFound = false;
//                }
//                else {
//                    neverFound = false;
//                }
//
//                // Since the server only gets applications located in /spot/software/state/application,
//                // this handles applications outside of that path that were added in the configuration
//                if (neverFound) {
//                    // 'simulate' an applicationState object - /classes/DependencyMaps and this file rely
//                    // on having these attributes, at a minimum. We just want to display the missing app
//                    // so this should be OK - but not ideal
//                    var showAsMissing = {
//                        'componentId': path,
//                        'configurationPath': path,
//                        'applicationStatusClass': constants.glyphs.unknownQMark,
//                        'applicationStatusBg': constants.colors.unknownGray,
//                        'applicationStatus': ko.observable(constants.applicationStatuses.unknown),
//                        'predType': predType,
//                        'requires': ko.observableArray([]),
//                        'errorState': ko.observable(constants.errorStates.unknown)
//                    };
//                    self.requires.push({'state': showAsMissing, 'operational': operational});
//                }
//            });
        };

        self.requirementsAreUp = ko.computed(function() {
//            if (self.requires().length > 0) {
//                for (var i = 0; i < self.requires().length; i++) {
//                    if (self.requires()[i].state.applicationStatus() === constants.applicationStatuses.stopped) {
//                        return false;
//                    }
//                }
//                return true;
//            }
//            else {
//                return true;
//            }
        });

        self.requiredBy = ko.computed(function() {
//            var dependencies = ko.observableArray([]);
//            // HATE HATE HATE this double loop. Need to move this processing to the server side.
//            ko.utils.arrayForEach(applicationStateArray(), function(applicationState) {
//                for (var i = 0; i < applicationState.dependencyModel.requires().length; i++) {
//                    if (applicationState.dependencyModel.requires()[i].state == parentAppState) {
//                        dependencies.push(applicationState);
//                        break;
//                    }
//                }
//            });
//
//            dependencies.sort();
//            return dependencies().slice();
        }).extend({rateLimit: 2000});

        self.dependencyClass = ko.computed(function() {
//            if (self.requires().length === 0 &&
//                self.holiday().length === 0 &&
//                self.weekend().length === 0 &&
//                self.zookeepergooduntiltime().length === 0) {
//                return '';
//            }
//            else
            if (self.showDependencies()) {
                return 'caret';
            }
            else {
                return 'caret-left';
            }
        });

        self.dependencyVisible = ko.computed(function () {
            return (
//                (
//                    self.requires().length > 0 ||
//                    self.zookeepergooduntiltime().length > 0 ||
//                    self.weekend().length > 0 ||
//                    self.holiday().length > 0
//                    ) &&
                self.showDependencies());
        });

        self.dependencyPointer = ko.computed(function() {
            if (self.dependencyClass() !== '') {
                return 'pointer';
            }
            else {
                return '';
            }
        });

        self.getDeps = ko.computed(function() {
            if (self.showDependencies()) {
                $.getJSON('/api/application/dependencies' + parentAppState.configurationPath, function(data) {
                    self.newRequires(data.dependencies);
                }).fail(function(data) {
                    swal('Failed GET for getDeps.', JSON.stringify(data), 'error');
                });
            }
        });
    };
});