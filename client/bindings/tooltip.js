define(['knockout', 'jquery'],
function(ko, $) {

/******* TOOLTIP BUTTON BINDING *******/
ko.bindingHandlers.tooltip = {
    init: function(element, valueAccessor) {
        var local = ko.utils.unwrapObservable(valueAccessor()),
            options = {};

        ko.utils.extend(options, ko.bindingHandlers.tooltip.options);
        ko.utils.extend(options, local);

        $(element).tooltip(options);

        ko.utils.domNodeDisposal.addDisposeCallback(element, function() {
            $(element).tooltip("destroy");
        });
    },
    options: {
        placement: "top",
        trigger: "hover",
        html: "true"
    }
};
/****** END TOOLTIP BUTTON BINDING *******/

});

