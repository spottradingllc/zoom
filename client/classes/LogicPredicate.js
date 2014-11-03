define(['knockout'],
    function(ko) {
        return function LogicPredicate(Factory, predType) {
            var self = this;
            self.expanded = ko.observable(false);
            self.predType = predType;
            self.title = self.predType.toUpperCase();
            self.predicates = ko.observableArray();

            self.isLogicalPred = true;

            self.addPredicate = function(type) {
                var pred = Factory.newPredicate(self, type);
                self.expanded(true);
                self.predicates.push(pred);
            };


            self.error = ko.computed(function() {
                if (self.predType === 'not' && self.predicates().length !== 1) {
                    return 'NOT excepts exactly one predicate';
                }
                else if (self.predType === 'or' && self.predicates().length < 2) {
                    return 'OR needs two or more predicates';
                }
                else if (self.predType === 'and' && self.predicates().length < 2) {
                    return 'AND needs two or more predicates';
                }
                else {
                    return '';
                }
            });

            self.remove = function() {
                self.parent.predicates.remove(self);
            };

            self.expandUp = function() {
                self.expanded(true);
                self.parent.expandUp();
            };

            self.validate = function() {
                var valid = true;
                if (self.error() !== '') {
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
