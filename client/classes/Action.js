define(['knockout', 'classes/predicateFactory'],
    function(ko, Factory) {
        return function Action(parent) {
            var self = this;
            self.isAction = true;
            self.expanded = ko.observable(false);
            self.ID = ko.observable(null);
            self.staggerpath = ko.observable(null);
            self.staggertime = ko.observable(null);
            self.modeControlled = ko.observable(null);
            self.disabled = ko.observable(null);
            self.pdEnabled = ko.observable(null);
            self.predicates = ko.observableArray();

            self.parentComponent = parent;
            self.actionVisible = ko.computed(function() {
                if (self.ID() != null) {
                    var aID = self.ID().toLowerCase();
                    return (aID === 'start' || aID === 'restart');
                }
                else {
                    return true;
                }
            });

            self.title = ko.computed(function() {
                return 'Action ' + self.ID();
            });

            self.addPredicate = function(type) {
                var pred = Factory.newPredicate(self, type);
                self.expanded(true);
                self.predicates.push(pred);
            };

            self.remove = function() {
                parent.actions.remove(self);
            };

            self.toggleExpanded = function(expand) {
                if (typeof expand !== 'undefined') {
                    self.expanded(expand);
                }
                else {
                    self.expanded(!self.expanded());
                }
                ko.utils.arrayForEach(self.predicates(), function(predicate) {
                    predicate.toggleExpanded(self.expanded());
                });
            };

            var getErrors = function() {
                // return only errors related to this object
                var errors = [];

                if (self.ID() === null) {
                    errors.push('Action ID cannot be null.');
                }

                return errors;
            };

            self.error = ko.computed(function() {
                var e = getErrors();
                return e.join(', ');
            });

            self.validate = function() {
            // return errors for this object and all child objects
                var allErrors = getErrors();

                ko.utils.arrayForEach(self.predicates(), function(predicate) {
                    allErrors = allErrors.concat(predicate.validate());
                });

                return allErrors;
            };

            var checkNull = function(param) {
                return (param !== null && param !== '');
            };

            self.createActionXML = function() {
                var XML = '<Action ';
                XML = XML.concat('id="' + self.ID() + '" ');

                if (checkNull(self.staggerpath())) {
                    XML = XML.concat('staggerpath="' + self.staggerpath() + '" ');
                }
                if (checkNull(self.staggertime())) {
                    XML = XML.concat('staggertime="' + self.staggertime() + '" ');
                }
                if (checkNull(self.modeControlled())) {
                    XML = XML.concat('mode_controlled="' + self.modeControlled() + '" ');
                }
                if (checkNull(self.disabled())) {
                    XML = XML.concat('disabled="' + self.disabled() + '" ');
                }
                if (checkNull(self.pdEnabled())) {
                    XML = XML.concat('pd_enabled="' + self.pdEnabled() + '" ');
                }

                XML = XML.concat('><Dependency>');

                // create XML for predicates
                for (var i = 0; i < self.predicates().length; i++) {
                    XML = XML.concat(self.predicates()[i].createPredicateXML());
                }

                var footer = '</Dependency></Action>';
                XML = XML.concat(footer);

                return XML;
            };

            self.loadXML = function(node) {
                self.ID(node.getAttribute('id'));
                self.staggerpath(node.getAttribute('staggerpath'));
                self.staggertime(node.getAttribute('staggertime'));
                self.modeControlled(node.getAttribute('mode_controlled'));
                self.disabled(node.getAttribute('disabled'));
                self.pdEnabled(node.getAttribute('pd_enabled'));

                var dependency = node.getElementsByTagName('Dependency')[0];
                if (dependency !== null) {
                    self.predicates.removeAll();
                    var child = Factory.firstChild(dependency);
                    while (child !== null) {
                        var type = child.getAttribute('type');
                        var predicate = Factory.newPredicate(self, type);
                        predicate.loadXML(child);
                        self.predicates.push(predicate);
                        child = Factory.nextChild(child);
                    }
                }
            };
        };
    });
