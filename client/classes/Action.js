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
            self.predicates = ko.observableArray();

            self.parentComponent = parent;
            self.actionVisible = ko.computed(function() {
                if (self.ID() != null) {
                    return self.ID().toLowerCase() === 'start';
                }
                else {
                    return false
                }
            });

            self.error = ko.computed(function() {
                if (self.predicates().length < 1) {
                    // TODO Decide what actions are required
                    return 'You have to have a predicate';
                }
                else {
                    return '';
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

            self.validate = function() {
                var valid = true;

                if (self.error() !== '') {
                    valid = false;
                }
                if (self.ID() === null) {
                    self.expandUp();
                    valid = false;
                }
                for (var i = 0; i < self.predicates().length; i++) {
                    if (!self.predicates()[i].validate()) {
                        valid = false;
                    }
                }

                if (!valid) {
                    self.expandUp();
                }
                return valid;
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
