define([
        'knockout',
        'jquery',
        'service',
        'model/environmentModel'
    ],
    function(ko, $, service, environment) {
        return function saltModel(pillarModel) {
            var self = this;

            var saltParams = {};
            var saltMaster = "";

            var onSuccess = function(data) {
                try {
                    saltParams = data.salt;
                    saltMaster = saltParams.uri;
                } catch(err) {
                    swal("Error", "Unable to parse Salt API parameters", 'error');
                }
            };

            var onFailure = function(data) {
                swal("Error", "Unable to retrieve Salt API parameters", 'error');
                console.log(data);
            };
                
            service.get('api/v1/saltmaster/', onSuccess, onFailure);

            var _valdata = function(update_list, pillar_lookup, update_type, data_type, project, _assocArray) {
                var self = this;
                self.list = update_list;
                self.pillar = pillar_lookup;
                self.type = update_type;
                self.data = data_type;
                self.project = project;
                self._assocArray = _assocArray;
            };

            var checkObjContents = function(obj1, obj2) {
                var ret = true;
                for (var each in obj1) {
                    // ignore 'zoom_version' as it is not in in the pillar path of zookeeper that we are updating
                    if (each === 'zoom_version') {
                        continue;
                    }
                    if (obj2.hasOwnProperty(each)) {
                        if (typeof obj1[each] === 'object') {
                            ret = checkObjContents(obj1[each], obj2[each]);
                        }
                        else if (obj1[each] !== obj2[each]) { 
                            ret = false;
                        }
                    }
                    else ret = false;
                }
                return ret;
            };

            self.validate = function(update_list, pillar_lookup, update_type, data_type, project, _assocArray) {
                var target = update_list;
                var run_func = "";
                var domain = ".spottrading.com";

                if (data_type === 'node') {
                    if (update_type === 'preCreate') {
                        run_func = "test.ping";
                        target += domain;
                    }
                    else if (update_type  === 'postCreate') {
                        run_func = "pillar.items";
                    }
                    else if (update_type === 'delete') {
                        run_func = "pillar.items";
                    }
                }

                else { //create/update/delete key/value/project
                    run_func = "pillar.items";
                }
                
                var _pass = new _valdata(target, pillar_lookup, update_type, data_type, project, _assocArray);

                $('#validateVisual').modal('show');
                var cmds = {
                    'fun': run_func,
                    'expr_form': 'list',
                    'tgt': target,
                    'username': saltParams.username,
                    'password': saltParams.password,
                    'eauth': 'pam',
                    'client': 'local'
                };

                $.ajax({
                    url: saltMaster,
                    type: 'POST',
                    data: cmds,
                    args: _pass,
                    headers: {'Accept': 'application/json'}
                })
                    .fail(function(data) {
                        swal("Error", "Failed to get data used to validate changes", 'error');
                        $('#validateVisual').modal('hide');
                    })
                    .done(function(data) {
                        // check if the data returned is correct
                        var validationFailure = false;
                        var errorMsg;
                        var dataset = data.return[0];
                        var zk = "zookeeper_pillar";
                        var zkPillar;

                        // check if we get an empty object - failure!!
                        if ($.isEmptyObject(dataset)) {
                            validationFailure = true;
                        }

                        try {                        
                            if (this.args.data !== 'node') {
                                for (var i in dataset) {
                                    if (dataset.hasOwnProperty(i)) {
                                        zkPillar = dataset[i][zk];
                                        // check if the pillars have the same value
                                        // ordering of the keys may be different thanks to python
                                        var expected_pillar = this.args.pillar[i];
                                        var val1 = checkObjContents(expected_pillar, zkPillar);
                                        var val2 = checkObjContents(zkPillar, expected_pillar);
                                        if (!val1 || !val2) {
                                            validationFailure = true;
                                            errorMsg = "Salt pillar and updated pillar do not match, manual refresh required";
                                        }
                                        // Override validation failure of empty object if that's what we expect
                                        if ($.isEmptyObject(expected_pillar) && $.isEmptyObject(zkPillar)) {
                                            validationFailure = false;
                                        }
                                    }
                                }
                            }
                            else { // create or delete a node
                                if (this.args.type === 'preCreate') {
                                    // hide the modal
                                    pillarModel.closeModal('addModal');
                                    // check if the ping is true
                                    if (!dataset[this.args.list]){
                                        validationFailure = true;
                                        errorMsg = "Server not found in Salt, please make sure this server is in Salt"
                                    }
                                    else {
                                        // actually create the node if ping returned - zk handles duplicates so unnecessary to check 
                                        pillarModel.pillarApiModel.api_post(this.args.list);
                                    }
                                }
                                else if (this.args.type === 'delete') {
                                    pillarModel.checkedNodes([]);
                                    // make sure zkpillar is gone
                                    for (var server in dataset) { 
                                        // external pillar will not be completely gone from salts perspective
                                        // still appears with zoom_version since it's not part of the path deleted
                                        if (!$.isEmptyObject(dataset[server][zk])) {
                                            validationFailure = true;
                                            errorMsg = "ZK Pillar may not have been deleted";
                                        }
                                        else validationFailure = false;
                                    }
                                }
                                else if (this.args.type === 'postCreate') {
                                    // make sure zkpillar is there
                                    if (typeof (dataset[this.args.list][zk]) === "undefined") {
                                        validationFailure = true;
                                        errorMsg = "ZK Pillar does not exist";
                                    }
                                }

                            } 
                        } catch(err) {
                            if (err.type === 'TypeErr') {
                                errorMsg = "TypeError caught, Salt config likely missing data";
                            }
                            else {
                                errorMsg = "Unexpected error caught: " + err.type;
                            }
                            validationFailure = true;
                        }
                        
                        $('#validateVisual').modal('hide');
                        // necessary due to switching contexts in async call above,
                        // not having access to validate visual fully
                        $('body').removeClass('modal-open');
                        $('.modal-backdrop').remove();

                        pillarModel.pillarApiModel.updateChecked(_assocArray);

                        if (validationFailure) {
                            swal("Error", "Validation error: " + errorMsg, 'error');
                        }
                        else {
                            // Show a successful confirmation for 1 second
                            $('#successAlert').fadeIn(250);
                            setTimeout(function() {
                                $('#successAlert').fadeOut(250);
                            }, 1000);
                        }
                    });
            };

            self.updateMinion = function(array_to_update, update_type, data_type, project) {
                var all = "";
                var first = true;

                var pillar_lookup = {};
                var refreshArray = ko.observableArray([]);

                if (typeof array_to_update !== 'string') {
                    array_to_update.forEach(function (_assoc) {
                        // create a salt-readable list for sending through the API
                        refreshArray = array_to_update;
                        if (!first) {
                            all += "," + _assoc.name;
                        }
                        else {
                            all += _assoc.name;
                            first = false;
                        }
                        // we need a way of determining if the pillar is updated and has the correct
                        // data in salt!
                        if (update_type === 'delete' && data_type === 'node'){
                            pillar_lookup[_assoc.name] = "";
                        }
                        else {
                            pillar_lookup[_assoc.name] = _assoc.edit_pillar();
                        }

                    });
                }
                // Creating node, no _assoc
                else {
                    all = array_to_update;
                }

                $('#loadVisual').modal('show');

                var cmds = {
                    'fun': 'saltutil.refresh_pillar',
                    'expr_form': 'list',
                    'tgt': all,
                    'username': saltParams.username,
                    'password': saltParams.password,
                    'eauth': 'pam'
                };

                $.ajax({
                    url: saltMaster,
                    type: 'POST',
                    data: cmds,
                    headers: {'Accept': 'application/json'}
                })
                    .fail(function(data) {
                        console.log(data);
                        $('#loadVisual').modal('hide');
                        swal("Critical", "Salt was not able to update - pillar will not be applied", 'error');
                    })
                    .done(function(data) {
                        $('#loadVisual').modal('hide');
                        self.validate(all, pillar_lookup, update_type, data_type, project, refreshArray);
                    });

            };
        };
    }
);
