define( [
        'knockout',
        'service',
        'jquery',
        'model/constants'
    ],
    function(ko, service, $, constants) {
        return function toolsModel(login) {
            var self = this;
            self.login = login;
            self.oldPath = ko.observable('');
            self.newPath = ko.observable(constants.zkPaths.appStatePath);

            self.setOldPath = function(path){
                self.oldPath(path)
            };
            
	        self.setNewPath = function(path){
                self.newPath(path)
            };

            self.showPaths = function() {
                var paths_dict = {
                    'oldPath': self.oldPath(),
                    'newPath': self.newPath()
                };
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
                        closeOnConfirm: false
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
                                            text: self.path_message(data.config_dict),
                                            closeOnConfirm: false,
                                            allowOutsideClick: true
                                        });
                                    },
                                    error: function(data) {
                                        swal({
                                            title:"Error!",
                                            text: data.responseJSON.errorText,
                                            closeOnConfirm: false
                                        });
                                    }
                                });
                        } else {
                            return;
                        }
                    })
                }
            };

            // function for creating a string with a list
            self.path_message = function(path_dict){
                var message = 'Replaced for paths: \n';
                ko.utils.arrayForEach(path_dict, function(path)  {
                    message = message + path + '\n';
                });
                return message
            };

        }
    });
    
