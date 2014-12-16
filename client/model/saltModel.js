define([
        'knockout',
        'jquery',
    ],
    function(ko, $) {
        return function saltModel(pillarModel) {
            var self = this;

            var _valdata = function(update_list, pillar_lookup, update_type, data_type, project, zk) {
                var self = this;
                self.list = update_list;
                self.pillar = pillar_lookup;
                self.type = update_type;
                self.data = data_type;
                self.project = project;
            };

            var checkObjContents = function(obj1, obj2) {
                var ret = true;
                for (var each in obj1) {
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

            self.validate = function(update_list, pillar_lookup, update_type, data_type, project) {
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
                }

                else { //create/update/delete key/value/project
                    run_func = "pillar.items";
                }
                
                var _pass = new _valdata(target, pillar_lookup, update_type, data_type, project);

                $('#validateVisual').modal('show');
                var cmds = {
                    'fun': run_func,
                    'expr_form': 'list',
                    'tgt': target,
                    'username': 'salt',
                    'password': 'salt',
                    'eauth': 'pam',
                    'client': 'local'
                };

                $.ajax({
                    url: "http://saltStaging:8000/run",
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
                        var showSuccess = false;

                        // check if we get an empty object - failure!!
                        if ($.isEmptyObject(dataset)) {
                            validationFailure = true;
                        }

                        // any sort of update
                        if (this.args.data !== 'node') {
                            try {
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

                        }
                        else { // create or delete a node
                            try {
                                if (this.args.type === 'preCreate') {
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
                                    // make sure zkpillar is gone
                                    for (var server in dataset) { 
                                        if (typeof dataset[server][zk] !== "undefined") {
                                            validationFailure = true;
                                            errorMsg = "ZK Pillar was not deleted";
                                        }
                                    }
                                }
                                else if (this.args.type === 'postCreate') {
                                    // make sure zkpillar is there
                                    if (typeof (dataset[this.args.list][zk]) === "undefined") {
                                        validationFailure = true;
                                        errorMsg = "ZK Pillar does not exist";
                                    }
                                    else {
                                        showSuccess = true;
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
                        }
                        
                        $('#validateVisual').modal('hide');
                        $('body').removeClass('modal-open');
                        $('.modal-backdrop').remove();

                        if (validationFailure) {
                            swal("Fatal", "Validation error: " + errorMsg, 'error');
                        }
                        if (showSuccess) {
                            swal("Success", "External pillar zookeeper node created.", 'success');
                        }
                    });
            };

            self.updateMinion = function(array_to_update, single_update, update_type, data_type, project) {
                var all = "";
                var first = true;

                var pillar_lookup = {};

                // creating a single node...
                if (single_update) {
                    all = array_to_update;
                }
                else {
                    array_to_update.forEach(function(_assoc) {
                        // create a salt-readable list for sending through the API
                        if (!first) {
                            all += "," + _assoc.name;
                        }
                        else {
                            all += _assoc.name;
                            first = false;
                        }
                        // we need a way of determining if the pillar is updated and has the correct
                        // data in salt!
                        pillar_lookup[_assoc.name] = _assoc.edit_pillar;
                    });
                }

                $('#loadVisual').modal('show');

                // KILL update for testing!!
                //$('#loadVisual').modal('hide');
                //self.validate(all, pillar_lookup, update_type, data_type, project);

                var cmds = {
                    'fun': 'saltutil.refresh_pillar',
                    'expr_form': 'list',
                    'tgt': all,
                    'username': 'salt',
                    'password': 'salt',
                    'eauth': 'pam'
                };

                $.ajax({
                    url: "http://saltStaging:8000/run",
                    type: 'POST',
                    data: cmds,
                    headers: {'Accept': 'application/json'}
                })
                    .fail(function(data) {
                        $('#loadVisual').modal('hide');
                        swal("Critical", "Salt was not able to update - pillar will not be applied", 'error');
                    })
                    .done(function(data) {
                        $('#loadVisual').modal('hide');
                        self.validate(all, pillar_lookup, update_type, data_type, project);
                    });

            };
        };
    }
);
