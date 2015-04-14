define(['knockout', 'jquery', 'classes/Component', 'model/adminModel', 'vkbeautify'],
    function(ko, $, Component, admin) {

        return function TreeViewModel(parent) {
            var self = this;
            self.components = ko.observableArray();
            self.adminModel = admin;
            self.pagerDutyServices = {};

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

            // will fill in self.pagerDutyServices when the call finishes
            $.ajax({
                url: '/api/pagerduty/services/',
                success: function(data) {
                    self.pagerDutyServices = JSON.parse(data);
                },
                async: true
            });

            var parseXMLforComponent = function(data) {
                var parser = new DOMParser();
                var xmlDoc = parser.parseFromString(data, 'text/xml');
                var comps = xmlDoc.getElementsByTagName('Component');
                for (var i = 0; i < comps.length; i++) {
                    var comp = new Component(self);
                    comp.loadXML(comps[i]);
                    self.components.unshift(comp);  // add to front of array
                }
            };

            self.addComponent = function() {
                // set default component to have the actions we care about
                var data = '<Component id="" type="application" script="" ><Actions><Action id="start" mode_controlled="True" ><Dependency><Predicate type="and"><Predicate type="not"><Predicate type="ZookeeperNodeExists" path="/spot/software/signal/killall" /></Predicate><Predicate type="not"><Predicate type="process" interval="5" /></Predicate></Predicate></Dependency></Action><Action id="stop" mode_controlled="True"><Dependency><Predicate type="ZookeeperNodeExists" path="/spot/software/signal/killall" /></Dependency></Action><Action id="register"><Dependency><Predicate type="process" interval="5" /></Dependency></Action><Action id="unregister"><Dependency><Predicate type="not"> <Predicate type="process" interval="5" /></Predicate></Dependency></Action><Action id="ensure_running"><Dependency><Predicate type="and"><Predicate type="TimeWindow" begin="08:30:00" end="15:15:00" weekdays="0-4" ></Predicate><Predicate type="not"><Predicate type="process" interval="5" /></Predicate></Predicate></Dependency></Action></Actions></Component>';
                parseXMLforComponent(data)
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

                parent.sentinelConfig(vkbeautify.xml(XML));
            };

            self.loadXML = function() {
                var data = parent.sentinelConfig();
                self.clear();
                parseXMLforComponent(data)
            };

        };
    });