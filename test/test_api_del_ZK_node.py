#!/usr/bin/python

import requests
import json
import sys

url1 = "http://chivlxstg153:8889/api/zookeeper/test/foo/bar1"
url2 = "http://chivlxstg153:8889/api/zookeeper/test/foo/bar2/1/2/3"

def getStatus(status_code, expected):
    codeBool = (status_code == requests.codes.ok)
    if codeBool != expected:
        print status_code
        print "Failed!"
    else:
        print status_code
        print "Succeeded!"

good_norecurse = {'username': 'distinctNameForLogging', 'recurse': 'False'}
good_recurse = {'username': 'distinctNameForLogging', 'recurse': 'True'}
bad_no_user = {'recurse': 'False'}
bad_bad_recurse = {'username': 'distinctNameForLogging', 'recurse': 'alse'}

r = requests.delete(url1, headers=bad_no_user)
getStatus(r.status_code, False)

r = requests.delete(url1, headers=bad_bad_recurse)
getStatus(r.status_code, False)

r = requests.delete(url2, headers=good_norecurse)
getStatus(r.status_code, True)

r = requests.delete(url1, headers=good_recurse)
getStatus(r.status_code, True)

