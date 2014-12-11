define(['knockout'],
    function(ko) {
        return function LogicPredicate(Factory, predType, parent) {
            var self = this;
            self.expanded = ko.observable(false);
            self.predType = predType;
            self.title = self.predType.toUpperCase();
            self.predicates = ko.observableArray();

            self.parent = parent;
            self.isLogicalPred = true;

            self.addPredicate = function(type) {
                var pred = Factory.newPredicate(self, type);
                self.expanded(true);
                self.predicates.unshift(pred);  // add to front of array
            };

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
                ko.utils.arrayForEach(self.predicates(), function(predicate) {
                    predicate.toggleExpanded(self.expanded());
                });
            };

            var getErrors = function() {
                // return only errors related to this object
                var errors = [];

                if (self.predType === 'not' && self.predicates().length !== 1) {
                    errors.push('NOT Predicate accepts exactly one child predicate.');
                }
                else if (self.predType === 'or' && self.predicates().length < 2) {
                    errors.push('OR Predicate needs two or more child predicates.');
                }
                else if (self.predType === 'and' && self.predicates().length < 2) {
                    errors.push('AND Predicate needs two or more child predicates.');
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

            self.createPredicateXML = function() {
                var XML = '';
                var header = '<Predicate type="' + self.predType + '">';
                XML = XML.concat(header);

                for (var i = 0; i < self.predicates().length; i++) {
                    XML = XML.concat(self.predicates()[i].createPredicateXML());
                }

                var footer = '</Predicate>';
                XML = XML.concat(footer);

                return XML;
            };

            self.loadXML = function(node) {
                self.predicates.removeAll();
                var child = Factory.firstChild(node);
                while (child !== null) {
                    var type = child.getAttribute('type');
                    var predicate = Factory.newPredicate(self, type);
                    predicate.loadXML(child);
                    self.predicates.push(predicate);
                    child = Factory.nextChild(child);
                }

            };
        };
    });
