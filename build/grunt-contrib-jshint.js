module.exports = function(grunt) {
  'use strict';

  grunt.config.set('jshint', {
    build: {
      options: {
        jshintrc: '.jshintrc'
      },
      src: ['*.js', 'build/**/*.js']
    },
    app: {
      options: {
        jshintrc: 'client/.jshintrc'
      },
      src: ['client/bindings/*.js',
            'client/classes/**/*.js',
            'client/model/*.js',
            'client/viewmodels/**/*.js',
            'client/views/*.js',
            'client/*.js']
    }
  });

  grunt.loadNpmTasks('grunt-contrib-jshint');
};
