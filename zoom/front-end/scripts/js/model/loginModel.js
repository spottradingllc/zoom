define(['knockout', 'jquery', 'service', 'sammyApp'],
function(ko, $, service, sammyApp) {

    var impl;
    impl = {};


    impl.elements = {
        username: ko.observable(""),
        password: ko.observable(""),
        showError: ko.observable(false),
        error: ko.observable("")
    };


    impl.reset = function () {
        impl.elements.username("");
        impl.elements.password("");
    };


    impl.submit = function (params) {
//        console.log(JSON.stringify(params));

        return service.post('login', params, onSuccess, onFailure);
    };


    var onSuccess = function(data) {
//        console.log(JSON.stringify(data));

        return sammyApp.app().setLocation('#/application_state');
    };


    var onFailure = function(data) {
//        console.log(JSON.stringify(data));

        return alert('onFailure');
    };


    return {
        model: function() {

            impl.reset();

            return impl;
        }
    };
});
