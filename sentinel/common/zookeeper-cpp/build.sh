#! /bin/bash

# clean
rm -rf ./lib

# create lib
mkdir -p ./lib

# let's do an out-of-source build
cd ./lib

# build library 
cmake ../ && make

# go to sample project
cd ../sample

# clean
rm -rf ./bin

# create bin
mkdir -p ./bin

# let's do an out-of-source build
cd ./bin

# build sample
cmake ../ && make

# copy dependencies
cp ../../config/log4cxx.config.xml ./

# go back to project root
cd ../..
