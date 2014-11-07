define( [
        'knockout',
        'plugins/router',
        'service',
        'jquery',
        'model/environmentModel',
        'model/adminModel',
        'model/GlobalMode',
        'model/customFilterModel',
        'bindings/uppercase',
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

            self.show_pillar = ko.observable("");
            self.searchVal = ko.observable(""); 
            self.fieldOneVal = ko.observable("").extend({uppercase: true});
            self.selectedOption = ko.observable("");
            self.selectedProject = ko.observable("").extend({notify: 'always'});
            self.new_version = ko.observable("");
            self.new_subtype = ko.observable("");
            self.new_project = ko.observable("");

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
                // _assoc object also has dynamically created 
            };

            self.subtype_get = function (data, field) {
                try {
                    return data[self.selectedProject()]()[field];
                } catch(err) {
                    if (err.name === 'TypeError')
                        return "Project Does Not Exist";
                    else
                        return "An unexpected error occured";
                }
            };

            self.unselectAll = function() {
                ko.utils.arrayForEach(self.allInfo(), function(_assoc){
                    _assoc.checked(false);
                });
            };
           
                
            self.api_put = function (type, data) {
                ko.utils.arrayForEach(self.checked_servers(), function(_assoc) {
                    var uri = "api/pillar/" + _assoc.name + "/" + self.selectedProject() + "/" + type + "/" + data;

                    $.ajax({
                        url: uri,
                        type: "PUT",
                    })
                    .fail(function(data) {
                        console.log("failed to update data");
                    })
                    .done(function(data) {
                        console.log("successfully updated data");
                        self.updateChecked();
                    });
                });
            };

            self.createProjectWrapper = function(data) {
                ko.utils.arrayForEach(self.checked_servers(), function(_assoc) {
                    if (typeof _assoc[data] !== "undefined"){
                        alert("project already exists on " + _assoc.name);
                    }
                    else
                        self.api_post("project", _assoc.name, data);
                });
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

            self.addProjects = function(_assoc) {
                for (var each in _assoc.pillar){
                    if (self.allProjects.indexOf(each) < 0){
                        //console.log(each);
                        self.allProjects.push(each);
                    }
                }
            };

            self.objProjects = function (_assoc) {
                for (var each in _assoc.pillar){
                    _assoc[each] = ko.observable("");
                    _assoc[each](_assoc.pillar[each]);
                }
            };

            self.updateChecked2 = function () {
                ko.utils.arrayForEach(self.checked_servers(), function(_assoc) {
                    self.addProjects(_assoc);
                    self.objProjects(_assoc);
                });
            };
            
            self.checked_server_data = ko.computed(function() {
                ko.utils.arrayForEach(self.allInfo(), function(_assoc) {
                    if (_assoc.checked()){
                        if (!_assoc.prior){
                            self.addProjects(_assoc);
                            self.checked_servers.push(_assoc);
                            _assoc.prior = true;
                        }
                        else {
                            self.allProjects([]);
                            ko.utils.arrayForEach(self.checked_servers(), function(_assoc) {
                                 self.addProjects(_assoc);
                            });
                        }
                    }
                    else if (!_assoc.checked()) {
                        if (_assoc.prior){
                           // remove from the array based on the server name
                           self.checked_servers.remove(_assoc);
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
            self.api_post = function (type, minion, project) {
                var uri = "api/pillar/" + minion;
                if (type === "project")
                    uri += "/" + project;
                else
                    uri += self.domain;

                $.post(uri, function(){
                })
                .fail(function(data) {
                    console.log("failed to create new pillar for a new minion");
                })
                .done(function(data) {
                    console.log("succeeded making new pillar");
                    if (type === "project") self.updateChecked();
                    else if (type === "pillar") self.loadServers(false);
                });
            };

            self.api_delete = function(level_to_delete) {
                var response = confirm("Delete project for " + self.checked_servers().length + " servers?");
                if (response) {
                    ko.utils.arrayForEach(self.checked_servers(), function(_assoc) {
                        var uri = "api/pillar/" + _assoc.name;
                        if (level_to_delete === "project")
                            uri += "/" + self.selectedProject();

                        $.ajax({
                            url: uri,
                            type: "DELETE",
                        })
                        .fail(function(data) { 
                            console.log("failed to delete the server(s)");
                        })
                        .done(function(data) { 
                            console.log("successful");
                            if (level_to_delete === 'pillar')
                                self.loadServers(false);
                            else
                                self.updateChecked();
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


            
            self.updateAll = function() {
                ko.utils.arrayForEach(self.servers(), function (server_name) {
                    var serverAlreadyExists = false;
                    console.log(server_name);
                    ko.utils.arrayForEach(self.allInfo(), function (_assoc) {
                        if (server_name === _assoc.name) {
                            self.getPillar(_assoc, false)
                            serverAlreadyExists = true;
                        }
                    });
                    if (serverAlreadyExists === false){
                        self.getPillar(server_name, true);
                        //get pillar and create new _assoc object, push onto allInfo
                    }
                });
            };
            
            self.updateChecked = function () {
                // maintain previously selected project even after updating
                var prevSelect = self.selectedProject();
                ko.utils.arrayForEach(self.checked_servers(), function (_alloc) {
                    $.get("api/pillar/" + _alloc.name, function () {
                    })
                    .fail(function(data) {
                        console.log("error getting pillar");
                    })
                    .done(function(data) {
                        console.log("succeeded getting pillar");
                        var index = self.allInfo.indexOf(_alloc);
                        var index2 = self.checked_servers.indexOf(_alloc);
                        _alloc.pillar = data;
                        
                        self.allInfo.replace(self.allInfo()[index], _alloc);
                        self.checked_servers.replace(self.allInfo()[index2], _alloc);
                        self.updateChecked2();
                        self.selectedProject(prevSelect);
                    });

                });

            };

            self.getPillar = function(objOrName, create_new) {
                //TODO: error handling for http get
                    var uri = "api/pillar/";
                    if (create_new) uri += objOrName;
                    else uri += objOrName.name;

                    $.get(uri, function (){
                    })
                    .fail(function(data) {
                        console.log("failed to get server pillars");
                    })
                    .done(function(data) {
                        /* 
                        if ($.isEmptyObject(data)){
                            console.log("Pillar data is empty for server: " + server);
                            console.log(data);
                        }
                        else {*/
                            //var entry = {'name': server, 'pillar': data};
                            if (create_new){
                                var entry = new _assoc(objOrName, data);
                                self.objProjects(entry);  
                                self.allInfo.push(entry);
                            }
                            else {
                                var indexAll = self.allInfo.indexOf(objOrName);
                                var indexChecked = self.checked_servers.indexOf(objOrName);
                                objOrName.pillar = data;
                                self.objProjects(objOrName);
                                self.allInfo.replace(self.allInfo()[indexAll], objOrName);
                                if (indexChecked !== -1){
                                    self.checked_servers.replace(self.checked_servers()[indexChecked], objOrName);
                                }
                                //update in checked_servers as well as allInfo
                            }
                    });
            };

            var onSuccess = function (data) { 
                console.log(data);
                self.servers(data);
                self.updateAll();
            };

            var onSuccessNew = function (data) { 
                console.log(data);
                self.servers(data);
                ko.utils.arrayForEach(self.servers(), function(server) {
                    self.getPillar(server, true);
                });
            };
            
            var onFailure = function() {
                console.log('failed to get list of servers');
            };

            self.loadServers = function (load_new) {
                if (load_new)
                    service.get('api/pillar/list_servers/', onSuccessNew, onFailure);
                else
                    service.get('api/pillar/list_servers/', onSuccess, onFailure);
            };   
        };
    });
