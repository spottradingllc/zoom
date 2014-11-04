define(['knockout', 'jquery', 'classes/Component', 'vkbeautify'],
    function(ko, $, Component) {

        return function TreeViewModel(parent) {
            var self = this;
            self.components = ko.observableArray();

            self.statePaths = (function() {
                var paths = [];
                $.ajax({
                    url: '/api/application/states/',
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

            self.addComponent = function() {
                self.components.push(new Component(self));
            };

            self.clear = function() {
                self.components.removeAll();
            };

            self.validate = function() {
                var valid = true;
                for (var i = 0; i < self.components().length; i++) {
                    if (!self.components()[i].validate()) {
                        valid = false;
                    }
                }

                if (!valid) {
                    alert('Red areas indicate errors');
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
