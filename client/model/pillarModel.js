define( [
        'knockout',
        'plugins/router',
        'service',
        'jquery',
        'model/environmentModel',
        'model/adminModel',
        'model/GlobalMode',
        'model/customFilterModel',
    ],
    function(ko, router, service, $,  environment, admin, GlobalMode,
             CustomFilterModel) {
        return function pillarModel() {
    
            var self = this;

            self.servers = ko.observableArray([]);
            self.allInfo = ko.observableArray([]);
            self.checked_servers = ko.observableArray([]);
            self.show_allInfo = ko.observableArray([]);
            self.allProjects = ko.observableArray([]);
            self.missingProject = ko.observableArray([]);

            self.show_pillar = ko.observable("");
            self.searchVal = ko.observable(""); 
            self.fieldOneVal = ko.observable("");
            self.selectedOption = ko.observable("");
            self.selectedProject = ko.observable("");

            self.pillarOptions = ko.observableArray(["","Modify Pillar(s)", "Create Pillar", "Delete Pillar(s)"]);
            self.domain = ".spottrading.com";

            function _proj(subtype, version){
                self.subtype = subtype;
                self.version = version;
            };

            function _assoc(server_name, pillar_data) {
                var self = this;
                self.name = server_name;
                self.pillar = pillar_data;
                self.checked = ko.observable(false);
                self.prior = false;
                self.projects = []; //type _proj
                // for future use
                //self.other = [];
            };

            self.show_pillar = ko.computed(function() {
                var get_last = [];
                var length;
                length = self.checked_servers().length;
                get_last = self.checked_servers()[length-1];
                if (get_last != undefined){
                    console.log(get_last);
                    return get_last.pillar;
                }
            }, self);

            self.getJSONLevel = function(source, dest) {
                /* 
                :type source: object 
                :type dest: array
                */ 

                for (var elt in source){
                    dest.push(elt);
                }
            };

            self.findMissing = ko.computed(function() {
                ko.utils.arrayForEach(self.checked_servers(), function(_assoc) {
                    var flag = false;
                    for (var each in _assoc.projects){
                        if (typeof self.selectedProject() != "undefined"){
                            
                            if (_assoc.projects[each] === self.selectedProject()) {
                                flag = true;
                            }
                        }
                        else flag = true;
                    }
                    if (!flag){
                        if (self.missingProject.indexOf(_assoc) < 0) {
                            self.missingProject.push(_assoc);
                        }
                    }
                });
            });



            self.addProjects = function(_assoc) {
                for (var each in _assoc.projects){
                    if (self.allProjects.indexOf(_assoc.projects[each]) < 0){
                        console.log(_assoc.projects[each]);
                        self.allProjects.push(_assoc.projects[each]);
                    }
                }
            };

            self.diff_and_show = ko.computed(function() {
                var firstRun = true;
                var compare = "";
                ko.utils.arrayForEach(self.allInfo(), function(_assoc) {
                    if (_assoc.checked()){
                        if (!_assoc.prior){
                            self.getJSONLevel(_assoc.pillar, _assoc.projects);
                            self.addProjects(_assoc);
                            self.checked_servers.push(_assoc);
                            _assoc.prior = true;
                        } 
                        if (firstRun){
                            firstRun = false;
                            compare = _assoc.pillar;
                        }
                        else {
                            if (ko.toJSON(compare) != ko.toJSON(_assoc.pillar)){
                                console.log("not the same!");
                            }    
                        }
                    }
                    else {
                        if (_assoc.prior){
                           // remove from the array based on the server name
                           self.checked_servers.remove(_assoc);
                           self.missingProject([]);
                           //TODO: remove all each time and re-calculate based on what is now selected
                           self.allProjects([]);
                           ko.utils.arrayForEach(self.checked_servers(), function(_assoc) {
                                self.addProjects(_assoc);
                           });

                           _assoc.prior = false;
                        }
                    }
                });
            });

            // calls create minion from api
            self.newPillar = function () {
                console.log(self.fieldOneVal());
                $.post("api/pillar/" + self.fieldOneVal() + self.domain, function(){
                })
                .fail(function(data) {
                    console.log("failed to create new pillar for a new minion");
                })
                .done(function(data) {
                    console.log("succeeded making new pillar");
                });
            };

            self.delPillar = function() {
                var response = confirm("Delete pillar for " + self.checked_servers().length + " servers?");
                if (response) {
                    ko.utils.arrayForEach(self.checked_servers(), function(_assoc) {
                        $.get("api/pillar/delete/" + _assoc.name, function() {
                        })
                        .fail(function(data) { 
                            console.log("failed to delete the server(s)");
                        })
                        .done(function(data) { 
                            console.log("successful");
                        });
                    });
                }
                else return;
            };

            self.show_allInfo = ko.computed(function() {
                var query = self.searchVal().toLowerCase();
                if (query === ""){
                    return self.allInfo();
                }
                return ko.utils.arrayFilter(self.allInfo(), function(_assoc) {
                    if (_assoc.name.toLowerCase().indexOf(query) >= 0){
                        console.log("found match: " + _assoc.name.toLowerCase());
                    }
                    return _assoc.name.toLowerCase().indexOf(query) >= 0;
                });
            }, self);

            self.associatePillars = ko.computed(function() {
                //TODO: error handling for http get
                ko.utils.arrayForEach(self.servers(), function(server) {
                    $.get("api/pillar/" + server, function (){
                    })
                    .fail(function(data) {
                        console.log("failed to get server pillars");
                    })
                    .done(function(data) {
                        if ($.isEmptyObject(data)){
                            console.log("Pillar data is empty for server: " + server);
                            console.log(data);
                        }
                        else {
                            //var entry = {'name': server, 'pillar': data};
                            var entry = new _assoc(server, data);
                            self.allInfo.push(entry);
                        }
                    });

                });
            });

            var onSuccess = function (data) { 
                console.log(data);
                self.servers(data);
            };
            
            var onFailure = function() {
                console.log('failed to get list of servers');
            };

            self.loadServers = function () {
                service.get('api/pillar/list_servers/', onSuccess, onFailure);
            };   
        

        };
    });
