define(['knockout', 'service' ], function (ko, service) {

    var login = new Object();

    login.elements = {
        username: ko.observable(""),
        password: ko.observable(""),
        showError: ko.observable(false),
        error: ko.observable(""),
        readWrite: ko.observable(false),
        authenticated: ko.observable(false)
    };

    login.advertise = ko.computed(function(){
        if(login.elements.authenticated()){
            return login.elements.username()
        }
        else{
            return "Sign In";
        }
    });

    login.setUserFromCookie = function () {
        this.elements.username(service.getCookie("username"));
        if (service.getCookie("read_write")) {
            this.elements.readWrite(true)
        }

        if (this.elements.username() && this.elements.readWrite()) {
            this.elements.authenticated(true)
        }
    };

    login.onSuccess = function(data) {
        this.login.setUserFromCookie();
    };

    login.onFailure = function(data) {
        console.log(JSON.stringify(data));
        return alert(JSON.stringify(data));
    };

    login.submit = submit;
    function submit() {
        console.log(this)

        var params = {
            username: this.elements.username(),
            password: this.elements.password()
        };

        return service.post('login', params, this.onSuccess, this.onFailure);
    };

    login.reset = function () {
        this.elements.username("");
        this.elements.password("");
        this.elements.authenticated(false);
        this.submit();
    };
    return login;
});
