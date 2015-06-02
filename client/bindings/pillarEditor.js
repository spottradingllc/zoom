define(
    [
        'knockout',
        'jquery',
        'jsonlint'
    ], 
    function(ko, $) {
        var getPillarModel = function(bindingContext) {
            if (bindingContext.$parents[2].constructor.name === 'pillarModel') {
                return bindingContext.$parents[2];
            }
            else {
                return bindingContext.$parents[3];
            }
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
                var editing = ko.unwrap(valueAccessor());
                var pillarModel = getPillarModel(bindingContext);
                if (editing) {
                    pillarModel.tableEditing = true;
                }
                var hasProjectIndex = pillarModel.checkedNodes.indexOf(bindingContext.$parent);
                var assocIndex = pillarModel.queriedNodes().indexOf(bindingContext.$parent);
                // only update if the project exists!
                if (!editing && element.value !== "Project Does Not Exist" && element.value !== "Select a project") {
                    var project = bindingContext.$parents[1].proj_name;
                    var key = bindingContext.$data;
                    var parsed = element.value;
                    // don't pass to the parser if null - parser will return and we want to allow null?
                    if (typeof element.value !== 'undefined' && element.value !== "") { 
                        try {
                            parsed = jsonlint.parse(element.value)
                        } catch(err) {
                            swal("Invalid JSON", err.message, 'error');

                            return;
                        }
                    }

                    try {
                        // keep it at null if nothing is there
                        if (element.value !== "" && hasProjectIndex !== -1) {
                            pillarModel.checkedNodes()[hasProjectIndex].edit_pillar()[project][key] = parsed;
                        }
                        if (element.value !== "" && assocIndex !== -1) {
                            pillarModel.queriedNodes()[assocIndex].edit_pillar()[project][key] = parsed;
                        }
                    }catch (err) {
                        //TODO: ignore - may not be updated
                    }

                }
                if (!editing && pillarModel.tableEditing) {
                    // tell all others that we're done editing
                    pillarModel.doneEditing(bindingContext.$parent);
                    pillarModel.tableEditing = false;
                }
            }
        };

        ko.bindingHandlers.updateLatest = {
            update: function(element, valueAccessor, allBindings, viewModel, bindingContext) {
                // have to use the valueaccessor in order for update to be called
                var edit = ko.unwrap(valueAccessor());
                var pillarModel = getPillarModel(bindingContext);

                element.text = pillarModel.getValues(bindingContext.$parent, bindingContext.$parents[1], bindingContext.$data);
                if (element.text !== "Project Does Not Exist" && element.text !== "Select a project") {
                    var project = bindingContext.$parents[1].proj_name;
                    var key = bindingContext.$data;
                    $(element).text(JSON.stringify(bindingContext.$parent.edit_pillar()[project][key]));
                }
            }
        };
    }
);
