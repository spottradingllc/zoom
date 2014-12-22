define( [
        'knockout',
        'service',
        'jquery',
        'model/pillarApiModel',
        'model/saltModel',
        'bindings/uppercase'
    ],
    function(ko, service, $, pillarApiModel, saltModel) {
        return function toolsModel(login) {
            var self = this;
            self.oldPath = ko.observable();
            self.newPath = ko.observable();

            self.showPaths = function() {
                console.log(self.oldPath())
                console.log(self.newPath())

                var paths_dict = {
                    'oldPath': self.oldPath(),
                    'newPath': self.newPath()
                }

                $.ajax({
                    url: '/tools/refactor_path/',
                    async: false,
                    data: paths_dict,
                    type: 'POST',
                    success: function(data){
                        swal('Success: ' + data);
                    },
                    error: function(data) {
                        swal('Error! Path does not exist: ' + self.oldPath());
                    }
                });

            }

        }
    })
    