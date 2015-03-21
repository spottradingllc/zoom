define(['knockout', 'model/constants'], function(ko, constants) {
    return function DependencyModel(applicationStateArray, parentAppState) {
        var self = this;

        self.upstream = ko.observableArray([]).extend({rateLimit: 2000});
        self.downstream = ko.observableArray([]).extend({rateLimit: 2000});
        self.time = ko.observableArray([]).extend({rateLimit: 2000});
        self.other = ko.observableArray([]).extend({rateLimit: 2000});

        self.showDependencies = ko.observable(false);

        // Dependency bubbling
        self.toggleDependencies = function() {
            self.showDependencies(!self.showDependencies());
        };

        self.handleUpdate = function(update) {
            self.upstream.removeAll();
            parentAppState.mtime = Date.now();
            if (parentAppState.applicationHost() === '') { return; }
            self.downstream(update.downstream);

            update.dependencies.forEach(function(entry) {
                var neverFound = true;
                var predType = entry.type;
                var path = entry.path;
                var operational = entry.operational;

                // if path = /foo, match both /foo/bar and /foo/baz
                if (predType === constants.predicateTypes.ZooKeeperHasGrandChildren) {
                    ko.utils.arrayForEach(applicationStateArray(), function(applicationState) {
                        if (applicationState.configurationPath.substring(0, path.length) === path) {
                            self.upstream.push(applicationState);
                            neverFound = false;
                        }
                    });
                }
                else if (predType === constants.predicateTypes.ZooKeeperHasChildren) {
                    var applicationState = ko.utils.arrayFirst(applicationStateArray(), function(applicationState) {
                        return (path === applicationState.configurationPath);
                    });
                    if (applicationState) {
                        neverFound = false;
                        self.upstream.push(applicationState);
                    }
                }
                else if (predType === constants.predicateTypes.Time || predType === constants.predicateTypes.ZookeeperGoodUntilTime) {
                    neverFound = false;
                    self.time.push(path);
                }
                // if this predicate type exists in arrayMapping
                else {
                    // push path to appropriate array based on predicate type
                    self.other.push(path);
                    neverFound = false;
                }

                // Since the server only gets applications located in /spot/software/state/application,
                // this handles applications outside of that path that were added in the configuration
                if (neverFound) {
                    // 'simulate' an applicationState object - /classes/DependencyMaps and this file rely
                    // on having these attributes, at a minimum. We just want to display the missing app
                    // so this should be OK - but not ideal
                    var showAsMissing = {
                        'componentId': path,
                        'configurationPath': path,
                        'applicationStatusClass': constants.glyphs.unknownQMark,
                        'applicationStatusBg': constants.colors.unknownGray,
                        'applicationStatus': ko.observable(constants.applicationStatuses.unknown),
                        'predType': predType,
                        'requires': ko.observableArray([]),
                        'errorState': ko.observable(constants.errorStates.unknown)
                    };
                    self.upstream.push(showAsMissing);
                }
            });
        };

        self.timeComponent = ko.computed(function() {return self.time().length > 0});

        self.dependencyClass = ko.computed(function() {
            if (typeof self.upstream() === 'undefined') {return ''} // not sure why this happens...

            if (self.upstream().length === 0) { return ''; }
            else if (self.showDependencies()) { return 'caret'; }
            else { return 'caret-left'; }
        });

        self.dependencyVisible = ko.computed(function () {
            if (typeof self.upstream() === 'undefined') {return ''} // not sure why this happens...

            return (self.upstream().length > 0 && self.showDependencies());
        });

        self.dependencyPointer = ko.computed(function() {
            if (self.dependencyClass() !== '') { return 'pointer'; }
            else { return ''; }
        });

    };
});