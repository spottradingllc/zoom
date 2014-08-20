define(['knockout','./loginModel'], 
function (ko, login) {

    var sudo = new Object();

    sudo._login = login
    sudo._enabled = ko.observable(false);
    sudo.disable = function(){
        sudo._enabled(false);
    }
    sudo.enable = function(){
        if(login.elements.authenticated()){
            sudo._enabled(true);
        }
        else{
            alert("You must be logged in to use sudo");
        }
    }
    sudo.enabled = ko.computed(function(){
        if(login.elements.authenticated()){
            return sudo._enabled();
        }
        return false;
    });

    return sudo;
});
