function LoginModel(service, ko, sammyApp) {
    var self = this;

    self.elements = {
        username: ko.observable(""),
        password: ko.observable(""),
        showError: ko.observable(false),
        error: ko.observable(""),
        readWrite: ko.observable(false),
        authenticated: ko.observable(false)
    };

    self.advertise = ko.computed(function(){
        if(self.elements.authenticated()){
            return self.elements.username()
        }
        else{
            return "Sign In";
        }
    });

    var setUserFromCookie = function () {
        self.elements.username(service.getCookie("username"));
        if (service.getCookie("read_write")) {
            self.elements.readWrite(true)
        }

        if (self.elements.username() && self.elements.readWrite()) {
            self.elements.authenticated(true)
        }
    };

    // If there is a cookie w/ a username, consider the user to be authenticated
    setUserFromCookie();

    self.submit = function () {
        var params = {
            username: self.elements.username(),
            password: self.elements.password()
        };

        return service.post('login', params, onSuccess, onFailure);
    };


    self.reset = function () {
        self.elements.username("");
        self.elements.password("");
        self.elements.authenticated(false);
        self.submit();
    };


    var onSuccess = function(data) {
        setUserFromCookie();
        return sammyApp.app().setLocation('#/application_state');
    };


    var onFailure = function(data) {
        console.log(JSON.stringify(data));
        return alert(JSON.stringify(data));
    };

}
