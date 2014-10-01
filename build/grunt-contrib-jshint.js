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
        jshintrc: 'src/.jshintrc'
      },
      src: ['client/**/*.js']
    }
  });

  grunt.loadNpmTasks('grunt-contrib-jshint');
};
