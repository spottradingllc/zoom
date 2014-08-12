define(['knockout', 'jquery'], 
function(ko, $) {

/******* RADIO BUTTON BINDING *******/
ko.bindingHandlers.radio = {
	init: function(element, valueAccessor, allBindings, viewModel, bindingContext) {
		$(element).click(function() {
			valueAccessor()(viewModel);
		});
	},
    update: function(element, valueAccessor, allBindings, viewModel, bindingContext) {
        var value = ko.unwrap(valueAccessor());
        if (viewModel == value) {
        	$(element).addClass("active");
        }
        else {
        	$(element).removeClass("active");
        }
    }
};
/****** END RADIO BUTTON BINDING *******/

});