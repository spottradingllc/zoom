define(['jquery', 'knockout', 'sammy'],
function($, ko, sammy) {

    var app;
    app = {};

    return {
        initialize: function () {
            app = sammy();

            var appViewModel = {
                view: ko.observable("default"),
                viewModel: ko.observable(""),
                render: ko.observable(false)
            };

            app.after(function () {
                var context;
                context = this;

                appViewModel.render(false);
                appViewModel.view(context.view);
                appViewModel.viewModel(context.viewModel);

                return appViewModel.render(true);
            });

            ko.applyBindings(appViewModel);

            return app;
        },

        app: function () {
            return app;
        }
    };
});
