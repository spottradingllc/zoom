define( [
        'knockout',
        'plugins/router',
        'durandal/composition',
        'service',
        'jquery',
        'model/pillarApiModel',
        'model/saltModel',
        'bindings/uppercase'
    ],
    function(ko, router, composition, service, $, pillarApiModel, saltModel) {
        return function pillarModel(login) {
    
            var self = this;
            self.login = login;

            self.servers = ko.observableArray([]);
            self.allInfo = ko.observableArray([]);//.extend({rateLimit: 100});
            self.checked_servers = ko.observableArray([]);//.extend({rateLimit: 100});
            self.show_allInfo = ko.observableArray([]);
            self.allProjects = ko.observableArray([]);
            self.allKeys= ko.observableArray([]);
            self.missingProject = ko.observableArray([]);

            self.pillarOptions = ko.observableArray(["Modify Pillar(s)", "Create Pillar", "View Pillar(s)"]);//, "Delete Pillar(s)" ]);
            self.modifyOptions = ko.observableArray(["Existing project", "New project"]);
            self.new_pairs = ko.observableArray([{"key": "subtype", "value": ""}, {"key": "version", "value": ""}]); 


            self.searchVal = ko.observable(""); 
            self.fieldOneVal = ko.observable("").extend({uppercase: true});
            self.selectedOption = ko.observable("Modify Pillar(s)").extend({rateLimit: 100});
            self.selectedModify = ko.observable("Existing project");
            self.new_key = ko.observable("");
            self.new_value = ko.observable("");
            self.new_project = ko.observable("");
            self.edit_value = ko.observable("");
            self.saltValFail = ko.observable("");

            self.alphaNum = /^[a-zA-Z0-9]+$/;

            self.pillarApiModel = new pillarApiModel(self);
            self.saltModel = new saltModel(self);

            self._assoc = function(server_name, pillar_data) {
                var self = this;
                self.name = server_name;
                self.pillar = pillar_data;
                self.edit_pillar = {};
                self.checked = ko.observable(false);
                self.prior = false;
                self.projects = {};
                self.editable = ko.observable(false);
            };

            self._proj = function(name) {
                var self = this;
                self.proj_name = name;
                self.keys = ko.observableArray([]);
                self.edit_keys = ko.observableArray([]);
                self.hasProject = ko.observableArray([]);
                self.new_key = ko.observable("");
                self.editing = ko.observable(false);
                // need a way of keeping track of the number of servers
                // which have that project, when it reaches zero: remove
                self.freq = 0;
            };

            var resetFields = function () {
                self.new_project("");
                self.allKeys([]);
            };

            self.refreshTable = function(_assoc) {
                self.allKeys([]);
                self.allProjects([]);
                addProjects(_assoc);
                self.missingProject([]);
            };

            $(document).on('change keyup keydown paste cut', '.textarea', function() {
                $(this).height(0).height(this.scrollHeight);
            }).find('textarea').change();

            $(document).on('click', '#mainTable', function() {
                $("#mainTable").popover('show');
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

            self.removePair = function() {
                if (self.new_pairs().length > 2) {
                    var remove = self.new_pairs.pop();
                    self.new_pairs.remove(remove);
                }
            };

            self.validateNewPair = ko.computed( function() {
                if (self.new_key() !== "" && !self.alphaNum.test(self.new_key())) {
                    swal("Error", "Your key cannot contain non-alphanumerics", 'error');
                    self.new_key("");
                    return false;
                }
                if (self.new_project() !== "" && !self.alphaNum.test(self.new_project())) {
                    swal("Error", "Your project name cannot contain non-alphnumerics", 'error');
                    self.new_project("");
                    return false;
                }

                return true;
            });
            
            var validateNewProject = function() {
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


            self.getValues = function (_assoc, _proj, field) {
                var ret = "";
                try {
                    ret = _assoc.projects[_proj.proj_name]()[field];
                    if (_proj.hasProject().indexOf(_assoc) === -1)
                        _proj.hasProject().push(_assoc);
                } catch(err) {
                    if (err.name === 'TypeError') {
                        ret = "Project Does Not Exist";
                    }
                    else
                        ret = "An unexpected error occured";
                }

                return ret;
            };

            self.makeEditable = function (_assoc) {
                // find this _assoc in checked servers...
                var index = self.checked_servers.indexOf(_assoc);
                self.checked_servers()[index].editable(true);
            };

            var doneEditing = function (_updatingassoc) {
                ko.utils.arrayForEach(self.checked_servers(), function(_assoc) {
                    if (_assoc !== _updatingassoc) {
                        if (_assoc.editable) _assoc.editable(false); 
                    }
                });
            };

            var tableEditing = false;

            self.showEditTable = ko.observable(false);

            self.showEdit = function(html_proj) {
                html_proj.editing(true);
                // get latest pillar data and place into edit_pillar:
                // deep copy
                ko.utils.arrayForEach(self.checked_servers(), function(_assoc) {
                    _assoc.edit_pillar = $.extend(true, {}, _assoc.pillar);
                });

                // deep copy equivalent
                html_proj.edit_keys([]);
                ko.utils.arrayForEach(html_proj.keys(), function(key) {
                    html_proj.edit_keys.push(key);
                });
            };

            self.cancelEditing = function(html_proj) {
                html_proj.editing(false);
            };
                        
            ko.bindingHandlers.updateEdit = {
                init: function(element, valueAccessor, allBindings) {
                    $(element).focus(function() {
                        var value = valueAccessor();
                        value(true);
                    });
                    $(element).focusout(function() {
                        var value = valueAccessor();
                        value(false);
                    });
                },
                update: function(element, valueAccessor, allBindings, viewModel, bindingContext) {
                    $(element).focusin(function() {
                        var value = valueAccessor();
                        value(true);
                    });

                    var editing = ko.unwrap(valueAccessor());
                    if (editing) tableEditing = true;

                    var index = self.checked_servers.indexOf(bindingContext.$parent);

                    // only update if the project exists!
                    if (element.value !== "Project Does Not Exist" && element.value !== "Select a project") {
                        var project = bindingContext.$parents[1].proj_name;
                        var key = bindingContext.$data;
                        self.checked_servers()[index].edit_pillar[project][key] = element.value;
                    }

                    if (!editing && tableEditing) {
                        // tell all others that we're done editing
                        doneEditing(bindingContext.$parent);
                        tableEditing = false;
                    }
                }
            };

            ko.bindingHandlers.updateLatest = {
                update: function(element, valueAccessor, allBindings, viewModel, bindingContext) {
                    // have to call in order for this to update
                    var edit = ko.unwrap(valueAccessor());
                    // check what getvalues returns first
                    element.text = self.getValues(bindingContext.$parent, bindingContext.$parents[1], bindingContext.$data);
                    if (element.text !== "Project Does Not Exist" && element.text !== "Select a project") {
                        var project = bindingContext.$parents[1].proj_name;
                        var key = bindingContext.$data;
                        $(element).text(bindingContext.$parent.edit_pillar[project][key]);
                    }
                }
            };

            self.visualUpdate = function(update_type, data_type, _proj, key) {
                if (update_type === 'create') {
                    if (data_type === 'key') {
                        var new_key = _proj.new_key();
                        if (new_key === "") {
                            swal("Error", "Please enter a value for the new key", 'error');
                            return
                        }
                        ko.utils.arrayForEach(_proj.hasProject(), function(_assoc) {
                            // essentially the same as json update
                            _assoc.edit_pillar[_proj.proj_name][new_key] = "";
                        });
                        _proj.edit_keys.push(new_key);
                    }
                }
                else if (update_type === 'delete') {
                    if (data_type === 'key') {
                        ko.utils.arrayForEach(_proj.hasProject(), function(_assoc) {
                            delete _assoc.edit_pillar[_proj.proj_name][key];
                        });
                        var i = _proj.edit_keys.indexOf(key);
                        _proj.edit_keys.splice(i, 1); 
                    }
                }
            }; 

            var JSONcreateProject = function (_assoc) {
                var pairs = {};
                ko.utils.arrayForEach(self.new_pairs(), function(pair) {
                    pairs[pair.key] = pair.value;
                });

                _assoc.edit_pillar = $.extend(true, {}, _assoc.pillar);
                _assoc.edit_pillar[self.new_project()] = pairs;
            };

            var JSONupdate = function(_assoc, update_type, project) {
                if (update_type === 'key')
                    _assoc.pillar[self.selectedProject()][self.new_key()] = self.new_value();
            };

            self.uncheckAll = function() {
                ko.utils.arrayForEach(self.allInfo(), function(_assoc) {
                    _assoc.checked(false);
                });
            };

            self.checkAll = function() {
                if (self.show_allInfo().length > 8){
                    swal("Sorry", "Please narrow-down your search results to less than 8 visible servers.", 'error');
                    return;
                }
                ko.utils.arrayForEach(self.show_allInfo(), function(_assoc) {
                    _assoc.checked(true);
                });
            };
            
            var switchViewToProject = function(project_name) {
                if (typeof project_name === 'undefined')
                    console.log("no project");
                else { 
                    self.selectedModify("Existing project");
                }
            };

            self.createProjectWrapper = function(data) {
                var left = self.checked_servers().length;
                var refresh_salt = false;
                ko.utils.arrayForEach(self.checked_servers(), function(_assoc) {
                    if (typeof _assoc.projects[data] !== "undefined"){
                        swal("Warning", "Project already exists on " + _assoc.name, 'error');
                        left--;
                    }
                    else if (validateNewProject()){
                        // only refresh salt after the last one is updated 
                        if (left == 1) refresh_salt = true; 
                        left--;
                        JSONcreateProject(_assoc);
                        self.pillarApiModel.api_post_json(_assoc, refresh_salt, self.checked_servers, 'project');
                        switchViewToProject(data);
                    }
                });
            };

            self.updateProjectWrapper = function(update_type, data_type, _proj, key) {
                var alertText = "";
                var alertTitle = "";
                if (_proj.hasProject().length < self.checked_servers()) {
                    alertText = "Only " + _proj.has_project().length + " server(s) have the " + data_type + ", proceed to " + update_type + " anyway?";
                    alertTitle = "Hmm...";
                }
                else {
                    alertText = "Are you sure you want to " + update_type + " the " + data_type + " on " +  _proj.hasProject().length + " servers?";
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
                            self.pillarApiModel.api_delete(data_type, _proj, key);
                        else {
                            var refresh_salt = false;
                            for (var each in _proj.hasProject()) {
                                if (each === (_proj.hasProject().length-1).toString()) {
                                    refresh_salt = true;
                                }
                                if (data_type !== 'wholeTable') JSONupdate(_proj.hasProject()[each], data_type);
                                // ONLY send the salt refresh command after the last post has been made, to avoid spamming the salt master
                                self.pillarApiModel.api_post_json(_proj.hasProject()[each], refresh_salt, _proj.hasProject, data_type);
                            }
                        }
                    }
                });
            };

            var addProjects = function(_assoc) {
                $.each(_assoc.pillar, function(proj_name, keyVals) {
                    var found = false;
                    for (var i in self.allProjects()) {
                        if (self.allProjects()[i].proj_name === proj_name) {
                            self.allProjects()[i].freq++; 
                            found = true;
                        }
                    } 
                    if (!found) {
                        var new_proj = new self._proj(proj_name);
                        new_proj.freq = 1;
                        $.each(keyVals, function(key, value) {
                            new_proj.keys.push(key);
                        }); 
                        
                        self.allProjects.push(new_proj);
                    }
                });
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
                            addProjects(_assoc);
                            self.checked_servers.push(_assoc);
                            _assoc.prior = true;
                        }
                        else {
                            /*self.allProjects([]);
                            ko.utils.arrayForEach(self.checked_servers(), function(_assoc) {
                                 addProjects(_assoc);
                                 self.objProjects(_assoc);
                            });*/
                        }
                    }
                    else if (!_assoc.checked()) {
                        if (_assoc.prior){
                            // remove from the array based on the server name
                            self.checked_servers.remove(_assoc);
                            //TODO: remove all each time and re-calculate based on what is now selected
                            self.allProjects([]);
                            ko.utils.arrayForEach(self.checked_servers(), function(_assoc) {
                                addProjects(_assoc);
                            });

                            _assoc.prior = false;
                            // if this is the last to be un-checked, reset all fields
                            if (self.checked_servers().length == 0){
                                resetFields();
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

            var updateAllAdditions = function() {
                ko.utils.arrayForEach(self.servers(), function (server_name) {
                    var serverAlreadyExists = false;
                    ko.utils.arrayForEach(self.allInfo(), function (_assoc) {
                        if (server_name === _assoc.name) {
                            self.pillarApiModel.getPillar(_assoc, false);
                            serverAlreadyExists = true;
                        }
                    });
                    if (serverAlreadyExists === false){
                        self.pillarApiModel.getPillar(server_name, true);
                        //get pillar and create new _assoc object, push onto allInfo
                    }
                });
            };

            var updateAllDeletions = function() {
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
                            
            var onSuccess = function (data) {
                self.servers(data);
                updateAllAdditions();
                updateAllDeletions();
                self.pillarApiModel.updateChecked();
            };
            
            var onFailure = function() {
                console.log('failed to get list of servers');
            };

            self.loadServers = function () {
                service.get('api/pillar/list_servers/', onSuccess, onFailure);
            };   
        };
    });
