module.exports = function(grunt) {
  'use strict';

  grunt.config.set('clean', {
    build: {
      src: ['bower_components?', 'venv??', 'node_modules???']
    }
  });

  grunt.loadNpmTasks('grunt-contrib-clean');
};
