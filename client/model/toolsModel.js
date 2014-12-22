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


            // recursively search for parent action
            var getAction = function(obj) {
                if (typeof obj === 'undefined' || typeof obj.parent === 'undefined') {
                    return null;
                }
                else if (obj.parent && obj.parent.isAction) {
                    return obj.parent;
                }
                else {
                    // we haven't found it yet. Keep trying
                    return getAction(obj.parent);
                }
            };

            self.pathOptions = ko.computed(function() {
                console.log('check check')
                var action = getAction(self);

                if (action === null) { return []; }

                var paths = action.parentComponent.TreeViewModel.statePaths;

                if (self.path() === null || self.path() === '') { return paths; }

                return ko.utils.arrayFilter(paths, function(path) {
                    return path.indexOf(self.path()) !== -1;
                });
            });




        }
    })
    