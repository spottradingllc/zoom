define( [
        'knockout',
        'service',
        'jquery',
        'model/pillarApiModel',
        'model/saltModel',
        'model/constants',
        'bindings/uppercase',
        'bindings/pillarEditor'

    ],
    function(ko, service, $, pillarApiModel, saltModel, constants) {
        return function pillarModel(login, admin) {
    
            var self = this;
            self.login = login;
            self.adminModel = admin;

            // stores list of node names returned from API
            self.nodeNames = [];

            // nodes with their associated data in _assoc
            self.allNodes = ko.observableArray([]);//.extend({rateLimit: 100});

            // nodes from allNodes that should be shown based on the current query
            self.queriedNodes = ko.observableArray([]);

            // nodes from allNodes that are checked
            self.checkedNodes = ko.observableArray([]);//.extend({rateLimit: 100});

            // nodes from allNodes that are currently opened for editing
            self.editingNodes = ko.observableArray([]);
            
            // all projects for a  
            self.allProjects = ko.observableArray([]);
            self.selectedProjects = ko.observableArray([]);
            self.allKeys= ko.observableArray([]);
            self.new_pairs = ko.observableArray([{"key": "subtype", "value": null}, {"key": "version", "value": null}]);

            self.searchVal = ko.observable("");
            self.newNodeName= ko.observable("").extend({uppercase: true});
            self.selectedOption = ko.observable("Modify Pillar(s)").extend({rateLimit: 100});
            self.new_project = ko.observable("");
            self.keyProject = ko.observable("");
            self.selectedProject = ko.observable("");
            self.selectedAssoc = ko.observable("");
            self.successAlert = ko.observable(false);
            self.indivAction = ko.observable(false);

            self.pillarApiModel = new pillarApiModel(self);
            self.saltModel = new saltModel(self);

            self.tableEditing = false;
            var alphaNum = /^[a-zA-Z0-9]+$/;

            self._assoc = function(server_name, pillar_data) {
                var self = this;
                self.name = server_name;
                self.pillar = ko.observable(pillar_data);
                self.edit_pillar = ko.observable("");
                self.projects = {};
                self.projArray = ko.observableArray([]);
                self.star = ko.observable(constants.glyphs.emptyStar);
                self.checked = ko.observable(false);
                self.editable = ko.observable(false);
                self.prior = false;
            };

            self._proj = function(name) {
                var self = this;
                self.proj_name = name;
                self.keys = ko.observableArray([]);
                self.edit_keys = ko.observableArray([]);
                self.hasProject = [];
                self.new_key = ko.observable("");
                self.editing = ko.observable(false);
                // need a way of keeping track of the number of servers
                // which have that project, when it reaches zero: remove
                self.freq = 0;
            };

            self.uncheckAll = function() {
                self.checkedNodes([]);
                ko.utils.arrayForEach(self.allNodes(), function(_assoc) {
                    _assoc.checked(false);
                    _assoc.star(constants.glyphs.emptyStar);
                    _assoc.prior = false;
                });
            };

            self.updateSelected = ko.computed({
                read: function() {
                    return self.selectedProject;
                },
                write: function(newVal) {
                    if (newVal) {
                        self.selectedProject(newVal);
                    }
                }
            });

            self.checkAll = function() {
                if (self.queriedNodes().length > 8){
                    swal("Sorry", "Please narrow-down your search results to less than 8 visible hosts.", 'error');
                    return;
                }
                ko.utils.arrayForEach(self.queriedNodes(), function(_assoc) {
                    self.handleSelect(_assoc);
                });
            };

            self.projectList = function(_assoc) {
                var project_list = [];
                $.each(_assoc.pillar(), function(proj_name) {
                    project_list.push(proj_name);
                });
                return project_list.join(", ");
            };

            var resetFields = function () {
                self.new_project("");
                self.allKeys([]);
                self.checkedNodes([]);
            };

            self.refreshTable = function(_assoc) {
                self.allKeys([]);
                self.selectedProjects([]);
                addProjects(_assoc, self.selectedProjects);
            };

            self.removeQuery = function() {
                self.searchVal("");
            };

            self.addPair = function() {
                self.new_pairs.push({"key": null, "value": null});
            };

            self.removePair = function() {
                if (self.new_pairs().length > 0) {
                    var remove = self.new_pairs.pop();
                    self.new_pairs.remove(remove);
                }
            };

            ko.computed( function() {
                if (self.new_project() !== "" && !alphaNum.test(self.new_project())) {
                    swal("Error", "Your project name cannot contain non-alphnumerics", 'error');
                    self.new_project(self.new_project().replace(/[\W_]+/g, ""));
                    return false;
                }
                return true;
            });

            var validateNewProject = function(type) {
                if (type === 'new') {
                    if (self.new_project() === "") {
                        swal("Error", "Please enter a project name", 'error');
                        return false;
                    }
                }

                if (typeof type === 'undefined') {
                    swal("Error", "Select an existing project", 'error');
                    return false;
                }

                var ret = true;

                $.extend(true, [], self.new_pairs());
                ko.utils.arrayForEach(self.new_pairs(), function(pair){
                    if (pair.key !== "" && !alphaNum.test(pair.key)){
                        swal("Error", "Your key cannot contain non-alphanumerics", 'error');
                        pair.key = "";
                        ret = false;
                    }
                    if (typeof pair.value !== 'undefined' && pair.value !== "") {
                        try {
                            // make sure we can parse it later
                            JSON.parse(pair.value);
                        } catch(err) {
                            swal("Error", "Please make sure your values consist of valid JSON", 'error');
                            ret = false;
                        }
                    }

                });
                return ret;
            };

            self.getValues = function (_assoc, _proj, field) {
                var ret = "";
                try {
                    ret = JSON.stringify(_assoc.projects[_proj.proj_name]()[field]);
                    if (_proj.hasProject.indexOf(_assoc) === -1)
                        _proj.hasProject.push(_assoc);
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
                var index = self.checkedNodes.indexOf(_assoc);
                self.checkedNodes()[index].editable(true);
            };

            self.doneEditing = function (_updatingassoc) {
                ko.utils.arrayForEach(self.checkedNodes(), function(_assoc) {
                    if (_assoc !== _updatingassoc) {
                        if (_assoc.editable) _assoc.editable(false);
                    }
                });
            };

            self.showEdit = function(html_proj) {
                html_proj.editing(true);
                // get latest pillar data and place into edit_pillar:
                // deep copy
                ko.utils.arrayForEach(self.checkedNodes(), function(_assoc) {
                    _assoc.edit_pillar($.extend(true, {}, _assoc.pillar()));
                });
                // deep copy equivalent
                html_proj.edit_keys([]);
                ko.utils.arrayForEach(html_proj.keys(), function(key) {
                    html_proj.edit_keys.push(key);
                });
            };

            self.showEditInline = function(_assoc) {
                _assoc.edit_pillar($.extend(true, {}, _assoc.pillar()));
                ko.utils.arrayForEach(_assoc.projArray(), function (_proj) {
                    _proj.editing(true);
                    _proj.edit_keys([]);
                    ko.utils.arrayForEach(_proj.keys(), function(key) {
                        _proj.edit_keys.push(key);
                    });
                });
            };

            self.showModal = function(modal_id, _proj, indivAction) {
                getAllProjects();
                self.indivAction(false);
                if (typeof indivAction !== 'undefined'){
                    if (indivAction === true){
                        self.indivAction(true);
                    }
                }
                if (modal_id === 'addKey') {
                    self.keyProject(_proj);
                }
                $('#'+modal_id).modal('show');
            };

            self.closeModal = function(modal_id) {
                $('#'+modal_id).modal('hide');
            };

            self.cancelEditing = function(obj, group) {
                if (group !== true) {
                    ko.utils.arrayForEach(obj.projArray(), function (_proj) {
                        _proj.editing(false);
                    });
                }
                else {
                    obj.editing(false);
                }
            };

            self.visualUpdate = function(update_type, data_type, _proj, key) {
                if (update_type === 'create') {
                    if (data_type === 'key') {
                        var new_key = _proj.new_key();

                        if (new_key === "") {
                            swal("Error", "Please enter a value for the new key", 'error');
                            return;
                        }
                        else if (!alphaNum.test(_proj.new_key())) {
                            swal("Error", "Project keys must be alphanumeric", 'error');
                            return;
                        }
                        _proj.hasProject.forEach(function(_assoc) {
                            _assoc.edit_pillar()[_proj.proj_name][new_key] = null;
                        });
                        _proj.edit_keys.push(new_key);
                        self.closeModal('addKey');
                    }
                }
                else if (update_type === 'delete') {
                    if (data_type === 'key') {
                        _proj.hasProject.forEach(function(_assoc) {
                            delete _assoc.edit_pillar()[_proj.proj_name][key];
                        });
                        var i = _proj.edit_keys.indexOf(key);
                        // delete and update entire array
                        _proj.edit_keys.splice(i, 1);
                    }
                    else if (data_type === 'project') {
                        _proj.hasProject.forEach(function(_assoc) {
                            delete _assoc.edit_pillar()[_proj.proj_name];
                        });
                    }
                }
            };

            var JSONcreateProject = function (_assoc, project_name) {
                var pairs = {};
                ko.utils.arrayForEach(self.new_pairs(), function(pair) {
                    pairs[pair.key] = JSON.parse(pair.value);
                });
                // deep copy
                _assoc.edit_pillar($.extend(true, {}, _assoc.pillar()));
                _assoc.edit_pillar()[project_name] = pairs;
            };

            self.projectWrapper = function(project_name, single, modalToHide) {
                var left = self.checkedNodes().length;
                var refresh_salt = false;

                // validate once, even if multiple servers since using the same data.
                if (validateNewProject(project_name) === false) return;

                if (typeof modalToHide !== "undefined") {
                    $("#"+modalToHide).modal('hide');
                }

                var doesNotAlreadyExist = function(_assoc, num_remaining) {
                    if (typeof _assoc.projects[project_name] !== "undefined") {
                        swal("Warning", "Project already exists on " + _assoc.name, 'error');
                        num_remaining--;
                        return false;
                    }
                    else return true;
                };
                if (single === true) {
                    if (doesNotAlreadyExist(self.selectedAssoc())){
                        JSONcreateProject(self.selectedAssoc(), project_name);
                        var singleItemArr = [];
                        singleItemArr.push(self.selectedAssoc());
                        self.pillarApiModel.api_post_json(self.selectedAssoc(), true, singleItemArr, 'project', project_name);
                    }
                }
                else {
                    ko.utils.arrayForEach(self.checkedNodes(), function (_assoc) {
                        if (doesNotAlreadyExist(_assoc, left)) {
                            // only refresh salt after the last one is updated
                            if (left == 1) {
                                refresh_salt = true;
                            }
                            left--;
                            JSONcreateProject(_assoc, project_name);
                            self.pillarApiModel.api_post_json(_assoc, refresh_salt, self.checkedNodes(), 'project', project_name);
                        }
                    });
                }
            };

            self.updateProjectWrapper = function(update_type, data_type, _proj, key) {
                var alertText = "";
                var alertTitle = "";
                if (_proj.hasProject.length < self.checkedNodes()) {
                    alertText = "Only " + _proj.has_project().length + " host(s) have the " + data_type + ", proceed to " + update_type + " anyway?";
                    alertTitle = "Hmm...";
                }
                else {
                    alertText = "Are you sure you want to " + update_type + " the " + data_type + " on " +  _proj.hasProject.length + " hosts?";
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
                        self.closeModal('groupEditModal');
                        if (update_type === 'delete') {
                            // need to update the edit_pillar first!
                            self.visualUpdate(update_type, data_type, _proj, key);
                            self.pillarApiModel.api_delete(data_type, _proj, key);
                        }
                        else {
                            var refresh_salt = false;
                            for (var each in _proj.hasProject) {
                                // ONLY send the salt refresh command after the last post has been made, to avoid spamming the salt master
                                if (each === (_proj.hasProject.length-1).toString()) {
                                    refresh_salt = true;
                                }
                                self.pillarApiModel.api_post_json(_proj.hasProject[each], refresh_salt, _proj.hasProject, data_type);
                            }
                        }
                    }
                });
            };

            var addProjects = function(_assoc, koArray) {
                $.each(_assoc.pillar(), function(proj_name, keyVals) {
                    var found = false;
                    for (var i in koArray()) {
                        if (koArray()[i].proj_name === proj_name) {
                            koArray()[i].freq++;
                            found = true;
                        }
                    }
                    if (!found) {
                        var new_proj = new self._proj(proj_name);
                        new_proj.freq = 1;
                        $.each(keyVals, function(key) {
                            new_proj.keys.push(key);
                        });
                        koArray.push(new_proj);
                    }
                });
            };

            // Determine all projects available before showing the modal
            var getAllProjects = function() {
                ko.utils.arrayForEach(self.allNodes(), function(_assoc) {
                    addProjects(_assoc, self.allProjects);
                });
            };

            self.createObjForProjects = function (_assoc) {
                //delete existing!!!
                _assoc.projects = {};
                for (var each in _assoc.pillar()){
                    _assoc.projects[each] = ko.observable("");
                    _assoc.projects[each](_assoc.pillar()[each]);
                }
            };

            self.handleSelect = function(_assoc) {
                    if (!_assoc.prior){
                        addProjects(_assoc, self.selectedProjects);
                        _assoc.star(constants.glyphs.filledStar);
                        self.checkedNodes.push(_assoc);
                        _assoc.prior = true;
                        self.createObjForProjects(_assoc);
                    }
                    else if (_assoc.prior){
                        self.checkedNodes.remove(_assoc);
                        //TODO: significant performance hit
                        self.selectedProjects([]);
                        ko.utils.arrayForEach(self.checkedNodes(), function(_assoc) {
                            addProjects(_assoc, self.selectedProjects);
                        });

                        _assoc.prior = false;
                        // if this is the last to be un-checked, reset all fields
                        if (self.checkedNodes().length === 0){
                            resetFields();
                        }
                        _assoc.star(constants.glyphs.emptyStar);

                    }
            };

            self.handleAction = function(_assoc, action_type) {
                self.selectedAssoc(_assoc);
                if (action_type === 'existing') {
                    self.showModal('existingModal', null, true);
                }
                else if (action_type === 'new') {
                    self.showModal('newModal', null, true);
                }
            };

            self.toggleEdit = function(_assoc, refresh) {
                if ((_assoc.projArray().length === 0) || refresh) {
                    if (refresh) {
                        _assoc.projArray([]);
                    }
                    $.each(_assoc.pillar(), function(projects, keyVals) {
                        var new_proj = new self._proj(projects);
                        $.each(keyVals, function(key) {
                                new_proj.keys.push(key);
                        });
                        _assoc.projArray.push(new_proj);
                    });
                    self.editingNodes.push(_assoc);
                    self.showEditInline(_assoc);
                }
                else {
                    self.editingNodes.remove(_assoc);
                    _assoc.projArray([]);
                }
            };

            self.refreshEdit = function() {
                ko.utils.arrayForEach(self.editingNodes(), function(_assoc) {
                    self.toggleEdit(_assoc, true);
                });
            };

            self.queriedNodes= ko.computed(function() {
                var query = self.searchVal().toLowerCase();
                if (query === ""){
                    return self.allNodes();
                }
                return ko.utils.arrayFilter(self.allNodes(), function(_assoc) {
                    try {
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
            });
        };
    });
