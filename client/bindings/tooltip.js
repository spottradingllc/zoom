define(['knockout', 'jquery'],
function(ko, $) {

/******* TOOLTIP BUTTON BINDING *******/
ko.bindingHandlers.tooltip = {
        init: function(element, valueAccessor, allBindingsAccessor, viewModel, bindingContext) {
            var valueUnwrapped = ko.utils.unwrapObservable(valueAccessor());
            $(element).tooltip({
                title: valueUnwrapped
            })}
};
/****** END TOOLTIP BUTTON BINDING *******/

});

