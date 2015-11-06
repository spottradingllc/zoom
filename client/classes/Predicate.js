define(['knockout'],
    function(ko) {
        return function Predicate(parent) {
            var self = this;
            self.parent = parent;
            self.expanded = ko.observable(true);
            self.predType = ko.observable(null);
            self.interval = ko.observable(null);
            self.command = ko.observable(null);
            self.path = ko.observable(null);
            self.begin = ko.observable(null);
            self.end = ko.observable(null);
            self.weekdays = ko.observable(null);
            self.operational = ko.observable(null);
            self.ephemeralOnly = ko.observable(null);
            self.apiUrl = ko.observable(null);
            self.verb = ko.observable(null);
            self.expectedCode = ko.observable(null);

            self.isLogicalPred = false;

            self.pathVisible = ko.computed(function() {
                if (self.predType() != null) {
                    var predLower = self.predType().toLowerCase();
                    return predLower.slice(0, 'zookeeper'.length) === 'zookeeper';
                }
                else {
                    return true;
                }
            });
            self.intervalVisible = ko.computed(function() {
                if (self.predType() != null) {
                    var predLower = self.predType().toLowerCase();
                    return ['process', 'health', 'api'].indexOf(predLower) !== -1
                }
                else {
                    return true;
                }
            });
            self.commandVisible = ko.computed(function() {
                if (self.predType() != null) {
                    var predLower = self.predType().toLowerCase();
                    return predLower === 'health';
                }
                else {
                    return true;
                }
            });
            self.beginEndVisible = ko.computed(function() {
                if (self.predType() != null) {
                    var predLower = self.predType().toLowerCase();
                    return predLower === 'timewindow';
                }
                else {
                    return true;
                }
            });
            self.URLVisible = ko.computed(function() {
                if (self.predType() != null) {
                    var predLower = self.predType().toLowerCase();
                    return predLower === 'api';
                }
                else {
                    return true;
                }
            });

            // recursively search for parent action
            var getAction = function(obj) {
                if (typeof obj === 'undefined' || typeof obj.parent === 'undefined') {
                    return null;
                }
                else if (obj.parent && obj.parent.isAction) {
                    return obj.parent;
                }
                else {
                    // we haven't found it yet. Keep trying
                    return getAction(obj.parent);
                }
            };

            self.pathOptions = ko.computed(function() {
                var action = getAction(self);

                if (action === null) { return []; }

                var paths = action.parentComponent.TreeViewModel.statePaths;

                if (self.path() === null || self.path() === '') { return paths; }

                return ko.utils.arrayFilter(paths, function(path) {
                    return path.indexOf(self.path()) !== -1;
                });
            });

            self.setType = function(type) {
                self.interval(null);
                self.command(null);
                self.path(null);
                self.predType(type);
            };

            self.title = ko.computed(function() {
                return 'Predicate ' + self.predType() + ' ' + self.path();
            });

            self.remove = function() {
                self.parent.predicates.remove(self);
            };

            self.toggleExpanded = function(expand) {
                if (typeof expand !== 'undefined') {
                    self.expanded(expand);
                }
                else {
                    self.expanded(!self.expanded());
                }
            };

            var getErrors = function() {
                // return only errors related to this object
                var errors = [];

                if (self.predType() === null) {
                    errors.push('Predicate type cannot be null.');
                }
                else if (self.predType().toLowerCase() === 'api' && self.apiUrl() === null) {
                    errors.push('URL cannot be null for the API predicate.');
                }
                else if (self.predType().toLowerCase().indexOf('zookeeper') !== -1 && !self.path()) {
                    errors.push('The Zookeeper predicates cannot have an empty path.')
                }
                return errors;
            };

            self.error = ko.computed(function() {
                var e = getErrors();
                return e.join(', ');
            });

            self.validate = function() {
                return getErrors();
            };

            self.createPredicateXML = function() {
                var XML = '<Predicate ';
                XML = XML.concat('type="' + self.predType() + '" ');

                if (self.path() !== null) {
                    XML = XML.concat('path="' + self.path() + '" ');
                }
                if (self.interval() !== null) {
                    XML = XML.concat('interval="' + self.interval() + '" ');
                }
                if (self.command() !== null) {
                    XML = XML.concat('command="' + self.command() + '" ');
                }
                if (self.begin() !== null) {
                    XML = XML.concat('begin="' + self.begin() + '" ');
                }
                if (self.end() !== null) {
                    XML = XML.concat('end="' + self.end() + '" ');
                }
                if (self.weekdays() !== null) {
                    XML = XML.concat('weekdays="' + self.weekdays() + '" ');
                }
                if (self.operational() !== null) {
                    XML = XML.concat('operational="' + self.operational() + '" ');
                }
                if (self.ephemeralOnly() !== null) {
                    XML = XML.concat('ephemeral_only="' + self.ephemeralOnly() + '" ');
                }
                if (self.apiUrl() !== null) {
                    XML = XML.concat('url="' + self.apiUrl() + '" ');
                }
                if (self.verb() !== null) {
                    XML = XML.concat('verb="' + self.verb() + '" ');
                }
                if (self.expectedCode() !== null) {
                    XML = XML.concat('expected_code="' + self.expectedCode() + '" ');
                }

                XML = XML.concat('></Predicate>');

                return XML;
            };

            self.loadXML = function(node) {
                self.predType(node.getAttribute('type'));
                self.interval(node.getAttribute('interval'));
                self.command(node.getAttribute('command'));
                self.path(node.getAttribute('path'));
                self.begin(node.getAttribute('begin'));
                self.end(node.getAttribute('end'));
                self.weekdays(node.getAttribute('weekdays'));
                self.operational(node.getAttribute('operational'));
                self.ephemeralOnly(node.getAttribute('ephemeral_only'));
                self.apiUrl(node.getAttribute('url'));
                self.verb(node.getAttribute('verb'));
                self.expectedCode(node.getAttribute('expected_code'));

            };
        };
    });
