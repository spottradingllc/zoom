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
        return function pillarModel(login) {
    
            var self = this;
            self.login = login;

            self.servers = ko.observableArray([]);
            self.allInfo = ko.observableArray([]);//.extend({rateLimit: 100});
            self.checked_servers = ko.observableArray([]).extend({rateLimit: 100});
            self.show_allInfo = ko.observableArray([]);
            self.allProjects = ko.observableArray([]);
            self.allKeys= ko.observableArray([]);
            self.missingProject = ko.observableArray([]);
            self.hasProject = ko.observableArray([]);

            self.searchVal = ko.observable(""); 
            self.fieldOneVal = ko.observable("").extend({uppercase: true});
            self.selectedOption = ko.observable("Modify Pillar(s)").extend({rateLimit: 100});
            self.selectedProject = ko.observable("").extend({notify: "always"});
            self.selectedKey = ko.observable("").extend({notify: "always"});
            self.new_key = ko.observable("");
            self.new_value = ko.observable("");
            self.new_project = ko.observable("");
            self.edit_value = ko.observable("");
            self.selectedModify = ko.observable("Existing project");

            self.pillarOptions = ko.observableArray(["Modify Pillar(s)", "Create Pillar", "Delete Pillar(s)", "View Pillar(s)"]);
            self.modifyOptions = ko.observableArray(["Existing project", "New project"]);
            self.new_pairs = ko.observableArray([{"key": "subtype", "value": ""}, {"key": "version", "value": ""}]); 
            self.domain = ".spottrading.com";
            self.alphaNum = /^[a-zA-Z0-9]+$/;

            function _assoc(server_name, pillar_data) {
                var self = this;
                self.name = server_name;
                self.pillar = pillar_data;
                self.checked = ko.observable(false);
                self.prior = false;
                self.projects = new Object();
                // _assoc object also has dynamically created 
            };

            self.resetFields = function () {
                self.selectedProject(null);
                self.selectedKey(null);
                self.new_key("");
                self.new_value("");
                self.new_project("");
                self.edit_value("");
                self.allKeys([]);
            } 

            self.refreshTable = function(_assoc) {
                self.allKeys([]);
                self.allProjects([]);
                self.addProjects(_assoc);
                self.missingProject([]);
                self.hasProject([]);
            };

            $(document).on('change keyup keydown paste cut', '.textarea', function() {
                $(this).height(0).height(this.scrollHeight);
            }).find('textarea').change();

            $(document).on('click', '#allDrop', function() {
                self.selectedProject($(this).text());
                // reset so it can be calculated for the new project
                self.allKeys([]);
                self.missingProject([]);
                self.hasProject([]);
            });

            $(document).on('click', '#allKey', function() {
                self.selectedKey($(this).text());
            });

            self.toggleSearch = function() {
                $('#searchPane').toggle(200);
            };

            self.removeQuery = function() {
                self.searchVal("");
            };

            self.addPair = function() {
                self.new_pairs.push({"key": "", "value": ""});
            };

            self.validateNewPair = ko.computed(function() {
                if (self.new_key() !== "" && !self.alphaNum.test(self.new_key())) {
                    swal("Error", "Your key cannot contain non-alphanumerics", 'error');
                    self.new_key("");
                    return false;
                }

                return true;
            });

            self.validateNewProject = function() {
                if (self.new_project() === ""){
                    swal("Error", "Please enter a project name", 'error');
                    return false;
                }
                ko.utils.arrayForEach(self.new_pairs(), function(pair){
                    if (pair.key !== "" && !self.alphaNum.test(pair.key)){
                        swal("Error", "Your key cannot contain non-alphanumerics", 'error');
                        pair.key = "";
                        return false;
                    }
                });               
                return true;
            };

            self.get_values = function (_assoc, field) {
                var ret = "";
                if (typeof self.selectedProject() === 'undefined' || self.selectedProject() === null)
                    return "Select a project";
                try {
                    ret = _assoc.projects[self.selectedProject()]()[field];
                    if (self.hasProject().indexOf(_assoc) === -1)
                        self.hasProject().push(_assoc);
                } catch(err) {
                    if (err.name === 'TypeError') {
                        ret = "Project Does Not Exist";
                        if (self.missingProject().indexOf(_assoc) === -1)
                            self.missingProject().push(_assoc);
                    }
                    else
                        ret = "An unexpected error occured";
                }

                return ret;
            };

            self.JSONcreateProject = function (_assoc) {
                var proj_name = self.new_project();
                var pairs = {};
                ko.utils.arrayForEach(self.new_pairs(), function(pair) {
                    pairs[pair.key] = pair.value;
                });

                _assoc.pillar[self.new_project()] = pairs;
            };

            self.JSONupdate = function(_assoc, update_type) {
                if (update_type === 'value')
                    _assoc.pillar[self.selectedProject()][self.selectedKey()] = self.edit_value();
                else if (update_type === 'key')
                    _assoc.pillar[self.selectedProject()][self.new_key()] = self.new_value();
            }


            self.uncheckAll = function() {
                ko.utils.arrayForEach(self.allInfo(), function(_assoc) {
                    _assoc.checked(false);
                });
            };
            
            // Performance issues, currently limited to 8 selected
            self.checkAll= function(check) {
                if (self.show_allInfo().length > 8){
                    swal("Sorry", "Please narrow-down your search results to less than 8 visible servers.", 'Error');
                    return;
                }
                var arrayCopy = self.show_allInfo();
                for(var inc = 0; inc < arrayCopy.length; inc++){
                    arrayCopy[inc].checked(true);
                };
                self.show_allInfo(arrayCopy);
                self.show_allInfo.valueHasMutated();
            };

            self.salt_minion_update = function (ko_array_to_update) {
                var all = "";
                // create comma-delimited 'list' to send
                var first = true;
                ko.utils.arrayForEach(ko_array_to_update(), function(_assoc) {
                    if (!first)
                        all += "," + _assoc.name;
                    else {
                        all += _assoc.name;
                        first = false;
                    }
                });
                console.log("List sent to salt: " + all);


                $('#loadVisual').modal('show');
                
                var cmds = {
                    'fun': 'saltutil.refresh_pillar',
                    'expr_form': 'list',
                    'tgt': all, 
                    //'fun': 'test.ping',
                    'username': 'salt',
                    'password': 'salt',
                    'eauth': 'pam'
                }
                $.ajax({
                    url: "http://saltStaging:8000/run",
                    type: 'POST',
                    data: cmds,
                    headers: {'Accept': 'application/json'}
                })
                .fail(function(data) {
                    $('#loadVisual').modal('hide');
                    console.log("Failed to login to salt master");
                })
                .done(function(data) {
                    $('#loadVisual').modal('hide');
                    console.log("Success " + data.return[0]);
                });

            };
           
            self.api_post_json = function (_assoc, update_salt, ko_array_to_update) {
                
                var _projdata = {
                    "minion": _assoc.name, 
                    "data": _assoc.pillar
                };

                var uri = "api/pillar/"
                //console.log(JSON.stringify(_projdata));

                $.ajax({
                    type: "POST",
                    url: uri,
                    data: JSON.stringify(_projdata),
                    dataType: 'json',
                })
                .fail(function(data) {
                    swal("Error", "The data failed to update. Error message: " + data, 'error');
                })
                .success(function(data) {
                    self.updateChecked('post');

                    if(update_salt) self.salt_minion_update(self.hasProject, ko_array_to_update);
                })
            };
           
            // only used for pillar creation 
            self.api_post = function (type, minion, project) {
                var uri = "api/pillar/" + minion + self.domain;

                $.post(uri, function(){
                })
                .fail(function(data) {
                    console.log("failed to create new pillar for a new minion");
                    swal("failed to create", JSON.stringify(data), 'error');
                })
                .done(function(data) {
                    swal("Success!", "A new " + type + " has been added.", 'success');
                    self.loadServers();
                });
            };

            self.api_delete = function(level_to_delete) {
                var num_left = self.hasProject().length;
                ko.utils.arrayForEach(self.hasProject(), function(_assoc) {
                    var uri = "api/pillar/" + _assoc.name;
                    if (level_to_delete === "project" || level_to_delete === "key")
                        uri += "/" + self.selectedProject();
                    if (level_to_delete === "key")
                        uri += "/" + self.selectedKey();
                    console.log("URI sent to server: " + uri);
                    $.ajax({
                        url: uri,
                        type: "DELETE",
                    })
                    .fail(function(data) { 
                        console.log("failed to delete the server(s)" + data);
                        swal("Failed", "Delete failed", 'error'); 
                    })
                    .done(function(data) { 
                        // if the last one, notify on it only
                        if (num_left === 1){
                            swal("Success", "Successfully deleted", 'success'); 
                            self.salt_minion_update(self.hasProject);
                        }
                        num_left--;
                        console.log("delete successful");
                        //var message = "Successfully deleted ";

                        if (level_to_delete === 'pillar'){
                        //    message+=_assoc.name
                            self.loadServers();
                        }
                        else if (level_to_delete === 'key'){
                            self.updateChecked(level_to_delete);
                            self.selectedKey(null);
                        }
                        else { //project
                            self.updateChecked(level_to_delete);
                            self.selectedProject(null);
                        }
                    });
                });
            };

            self.switchViewToProject = function (project_name) {
                if (typeof project_name === 'undefined')
                    console.log("no project");
                else { 
                    self.selectedProject(project_name);
                    self.selectedModify("Existing project");
                }
            };

            self.delPillar= function() {
                swal({
                    title: "Confirm",
                    text: "Are you sure you want to delete " + self.checked_servers().length + " servers and ALL of their pillar data?",
                    showCancelButton: true,
                    confirmButtonText: "Yes"
                }, 
                function(isConfirm){
                    if (isConfirm) {
                        var left = self.checked_servers().length;
                        ko.utils.arrayForEach(self.checked_servers(), function(_assoc) {
                            var uri = "api/pillar/" + _assoc.name;

                            $.ajax({
                                url: uri,
                                type: "DELETE",
                            })
                            .fail(function(data) {
                                swal("Delete Failed", "Failed to delete pillar(s)", 'error');
                            })
                            .done(function(data) {
                                if (left === 1) {
                                    swal("Delete successful", "Pillar(s) deleted", 'success');
                                    self.loadServers();
                                    self.salt_minion_update(self.checked_servers);
                                }
                                left--; 
                            })
                        });
                    }
                });
            };
                
            self.createProjectWrapper = function(data) {
                ko.utils.arrayForEach(self.checked_servers(), function(_assoc) {
                    if (typeof _assoc.projects[data] !== "undefined"){
                        swal("Warning", "Project already exists on " + _assoc.name, 'error');
                    }
                    else if (self.validateNewProject()){
                        self.JSONcreateProject(_assoc);
                        self.api_post_json(_assoc, true, self.checked_servers);
                        self.switchViewToProject(data);
                    }
                });
            };

            self.updateProjectWrapper = function(update_type, data_type) {
                var alertText = "";
                var alertTitle = "";
                if (self.missingProject().length > 0) {
                    alertText = self.missingProject().length + " server(s) are missing the " + data_type + ", proceed to " + update_type + " anyway?";
                    alertTitle = "Hmm...";
                }
                else {
                    alertText = "Are you sure you want to " + update_type + " the " + data_type + " on " + self.hasProject().length + " servers?";
                    alertTitle = "Confirm";
                }
                swal({
                    title: alertTitle,
                    text: alertText,
                    showCancelButton: true,
                    confirmButtonText: "Yes"
                }, 
                function(isConfirm){
                    if (isConfirm) {
                        if (update_type === 'delete')  
                            self.api_delete(data_type);
                        else {
                            var refresh_salt = false;
                            for (var each in self.hasProject()) {
                                if (each === (self.hasProject().length-1).toString()) {
                                    refresh_salt = true;
                                }
                                self.JSONupdate(self.hasProject()[each], data_type);
                                self.api_post_json(self.hasProject()[each], refresh_salt, self.hasProject); 
                            }
                        }
                    }
                });
            };

            self.addProjects = function(_assoc) {
                for (var each in _assoc.pillar){
                    if (self.allProjects.indexOf(each) < 0){
                        //console.log(each);
                        self.allProjects.push(each);
                    }
                }
                try { 
                    for (var each in _assoc.pillar[self.selectedProject()]){
                        if (self.allKeys.indexOf(each) < 0){
                            self.allKeys.push(each);
                        }
                    }
                } catch(err) {
                    if (err.name === "TypeError")
                        console.log("Race condition, not an issue");
               
                }

            };

                
            self.objProjects = function (_assoc) {
                //delete existing!!!
                _assoc.projects = [];
                for (var each in _assoc.pillar){
                    _assoc.projects[each] = ko.observable("");
                    _assoc.projects[each](_assoc.pillar[each]);
                }
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
                                 self.objProjects(_assoc);
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

                            // selected project may no longer be in the all projects array
                            var proj_exist = ko.utils.arrayFirst(self.allProjects(), function(project) {
                                return project === self.selectedProject();
                            });

                            if (!proj_exist) { 
                                self.selectedProject(null);
                                self.selectedKey(null);
                            }

                            _assoc.prior = false;
                            // if this is the last to be un-checked, reset all fields
                            if (self.checked_servers().length == 0){
                                self.resetFields();
                            }
                        }
                    }
                });
            });

            self.show_allInfo = ko.computed(function() {
                var query = self.searchVal().toLowerCase();
                if (query === ""){
                    return self.allInfo();
                }
                return ko.utils.arrayFilter(self.allInfo(), function(_assoc) {
                    //TODO: is this necessary?
                    try {
                        //return if the project exists
                        for (var each in _assoc.projects){
                            if (each.toLowerCase().indexOf(query) >= 0){
                                return _assoc;
                            }
                        }
                    } catch (err){
                        if (err.type === "TypeErr"){
                            console.log("Proj DNE");
                        }
                        else {
                            console.log(err);
                        }
                    } 

                    return _assoc.name.toLowerCase().indexOf(query) >= 0;
                });
            }, self);


            
            self.updateAllAdditions = function() {
                ko.utils.arrayForEach(self.servers(), function (server_name) {
                    var serverAlreadyExists = false;
                    //console.log(server_name);
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

            self.updateAllDeletions = function() {
                ko.utils.arrayForEach(self.allInfo(), function (_assoc) {
                    var serverAlreadyExists = false;
                    //TODO: getting undefined here for some reason????
                    if (typeof _assoc !== "undefined"){
                        ko.utils.arrayForEach(self.servers(), function (name) {
                            if (_assoc.name === name)
                                serverAlreadyExists = true;
                        });
                        if (!serverAlreadyExists)
                            self.allInfo.remove(_assoc);
                    }
                });
            };
                            
            
            self.updateChecked = function (data_type) {
                // maintain previously selected project even after updating
                var prevSelect = self.selectedProject();
                ko.utils.arrayForEach(self.checked_servers(), function (_alloc) {
                    $.ajax({
                        url: "api/pillar/" + _alloc.name,
                        type: "GET",
                    })
                    .fail(function(data) {
                        swal("Error", "There was an error retrieving SELECTED pillar data", 'error');
                    })
                    .done(function(data) {
                        // set in API, makes sure that we delete when a minion no longer exists.
                        if (data.DOES_NOT_EXIST){
                            self.allInfo.remove(_alloc);
                            self.checked_servers.remove(_alloc);
                        }
                        else {
                            var index = self.allInfo.indexOf(_alloc);
                            var index2 = self.checked_servers.indexOf(_alloc);
                            _alloc.pillar = data;

                            self.allInfo.replace(self.allInfo()[index], _alloc);
                            self.refreshTable(_alloc);
                        }
                                                
                        self.selectedProject(prevSelect);

                        //update selected data if necessary
                        if (data_type === 'project') {
                            self.selectedProject(null);
                            self.selectedKey(null);
                        }
                        else if (data_type === 'key') 
                            self.selectedKey(null);
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
                        swal("Error", "There was an error retrieving pillar data", 'error'); 
                    })
                    .done(function(data) {
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
                self.servers(data);
                self.updateAllAdditions();
                self.updateAllDeletions();
                self.updateChecked('get_list');
            };
            
            var onFailure = function() {
                console.log('failed to get list of servers');
            };

            self.loadServers = function () {
                service.get('api/pillar/list_servers/', onSuccess, onFailure);
            };   
        };
    });
