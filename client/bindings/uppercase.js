define(['knockout'], 
function(ko) {

/******* CAPITALIZATION EXTENDER *******/
ko.extenders.uppercase = function(target, option) {
    target.subscribe(function(newValue) {
        target(newValue.toUpperCase());
    });
    return target;
};
/****** END CAPITALIZATION EXTENDER *******/

});
