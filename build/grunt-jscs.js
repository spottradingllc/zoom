module.exports = function(grunt) {
  'use strict';

  grunt.config.set('jscs', {
    build: {
      options: {
        config: '.jscsrc'
      },
      files: {
        src: ['*.js', 'build/**/*.js']
      }
    },
    app: {
      options: {
        config: '.jscsrc'
      },
      files: {
        src: ['*.js', 'client/**/*.js']
      }
    }
  });

  grunt.loadNpmTasks('grunt-jscs');
};
