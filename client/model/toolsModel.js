define( [
        'knockout',
        'service',
        'jquery',
        'model/pillarApiModel',
        'model/saltModel',
        'bindings/uppercase'
    ],
    function(ko, service, $) {
        return function toolsModel(login) {
            var self = this;
            self.oldPath = ko.observable('');
            self.newPath = ko.observable('');
            self.path = ko.observable(null);

            self.setOldPath = function(path){
                self.oldPath(path)
            }


            self.showPaths = function() {
                console.log('old path: ' + self.oldPath())
                console.log('new path: ' + self.newPath())

                var paths_dict = {
                    'oldPath': self.oldPath(),
                    'newPath': self.newPath()
                }

                if (self.oldPath() === '' || self.newPath() === ''){
                    swal('Please specify both paths!');
                }
                else if (self.oldPath() === self.newPath()){
                    swal('Paths are the same! Not Replacing');
                }
                else{
                    swal({
                        title: 'Please double check!',
                        text: 'Replace old path: ' + self.oldPath() + '\n with new path: ' + self.newPath() + '?',
                        type: "warning",
                        showCancelButton: true,
                        confirmButtonColor: "#DD6B55",
                        confirmButtonText: "Yes, Replace it!",
                        closeOnConfirm: true
                    },
                    function(isConfirm){
                        if (isConfirm) {
                           $.ajax({
                                    url: '/tools/refactor_path/',
                                    async: true,
                                    data: paths_dict,
                                    type: 'POST',
                                    success: function(data){
                                        swal({
                                            title:"Success!",
                                            text: data.server_list,
                                            closeOnConfirm: false

                                        });
                                    },
                                    error: function(data) {
                                        swal('Error! Path does not exist: ' + self.oldPath());
                                    }
                                });
                        } else {
                            return
                        }
                    })
                }
            }


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



            self.pathOptions = ko.computed(function() {
                var paths = self.statePaths;

                if (self.path() === null || self.path() === '') { return paths; }

                return ko.utils.arrayFilter(paths, function(path) {
                    return path.indexOf(self.path()) !== -1;
                });
            });




        }
    })
    