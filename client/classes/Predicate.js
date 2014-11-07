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
                    return predLower === 'process';
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
                var action = getAction(self.parent);

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

            self.error = ko.computed(function() {
                // TODO Flag errors that aren't empty field
                return '';
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

            self.validate = function() {
                var valid = true;
                if (self.error() !== '') {
                    valid = false;
                }
                if (self.predType() === null) {
                    valid = false;
                }
                if (!valid) {
                    self.expandUp();
                }
                return true;
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
                XML = XML.concat('></Predicate>');

                return XML;
            };

            self.loadXML = function(node) {
                self.predType(node.getAttribute('type'));
                self.interval(node.getAttribute('interval'));
                self.command(node.getAttribute('command'));
                self.path(node.getAttribute('path'));
            };
        };
    });
