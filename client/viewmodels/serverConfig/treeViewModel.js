define(['knockout', 'jquery', 'classes/Component', 'model/adminModel', 'vkbeautify'],
    function(ko, $, Component, admin) {

        return function TreeViewModel(parent) {
            var self = this;
            self.components = ko.observableArray();
            self.adminModel = admin;

            self.statePaths = (function() {
                var paths = [];
                $.ajax({
                    url: '/api/application/states',
                    success: function(data) {
                        ko.utils.arrayForEach(data.application_states, function(state) {
                            paths.push(state.configuration_path);
                        });
                    },
                    async: false
                });
                paths.sort();
                return paths;
            }());  // run immediately, and store as an array

            self.pagerDutyServices = function() {
                var pd_dict
                $.ajax({
                    url: '/api/pagerduty/services/',
                    success: function(data) {
                        pd_dict = JSON.parse(data);
                    },
                    async: false
                });
                return pd_dict
            }();

            self.addComponent = function() {
                self.components.push(new Component(self));
            };

            self.clear = function() {
                self.components.removeAll();
            };

            self.validate = function() {
                var valid = true;
                var errors = [];

                ko.utils.arrayForEach(self.components(), function(component) {
                    errors = errors.concat(component.validate());
                });

                if (errors.length > 0) {
                    swal({
                        title: 'I find your lack of config validity...disturbing.',
                        text: errors.join('\n'),
                        imageUrl: 'images/vadar.jpg'
                    });
                    valid = false;
                }

                return valid;
            };

            self.createXML = function() {
                var XML = '';
                var header = [
                    '<?xml version="1.0" encoding="UTF-8"?>',
                    '<Application>',
                    '<Automation>'
                ].join('\n');
                header = header.replace(/(\r\n|\n|\r)/gm, '');
                XML = XML.concat(header);

                for (var i = 0; i < self.components().length; i++) {
                    XML = XML.concat(self.components()[i].createComponentXML());
                }

                var footer = '</Automation></Application>';
                XML = XML.concat(footer);

                parent.serverConfig(vkbeautify.xml(XML));
            };

            self.loadXML = function() {
                var data = parent.serverConfig();
                self.clear();
                var parser = new DOMParser();
                var xmlDoc = parser.parseFromString(data, 'text/xml');
                var comps = xmlDoc.getElementsByTagName('Component');
                for (var i = 0; i < comps.length; i++) {
                    var comp = new Component(self);
                    comp.loadXML(comps[i]);
                    self.components.push(comp);
                }
            };

        };
    });
