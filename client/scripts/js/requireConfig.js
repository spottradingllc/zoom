require.config({
    // By default, load any module IDs from front-end/scripts/js ...
    baseUrl: 'front-end/scripts/js',

    // ...Except if the module ID is a 3rd-party library, then load it
    // from the front-end/scripts/js/lib directory.
    //
    // Path configuration is relative to "baseUrl", and never includes
    // a ".js" extension since paths configuration could be for a directory.
    paths: {
        libs: './libs',
        jquery: '//code.jquery.com/jquery-2.1.1',
        knockout: '//cdnjs.cloudflare.com/ajax/libs/knockout/3.1.0/knockout-min',
        bootstrap: './libs/bootstrap.min',
        sammy: '//cdnjs.cloudflare.com/ajax/libs/sammy.js/0.7.4/sammy.min',
        d3: '//cdnjs.cloudflare.com/ajax/libs/d3/3.4.11/d3.min'
    }
});
