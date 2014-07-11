import httplib
import json
# import ldap
import logging

import tornado.escape
import tornado.gen
import tornado.web


class LoginHandler(tornado.web.RequestHandler):
    #@tornado.gen.coroutine
    def post(self):
        request = json.loads(self.request.body)  # or '{"login": {}}'
        logging.info(request)

        try:
            username = self._parse_username(request['username'])
            password = request['password']

            # connect to ldap server
            #ldap_object = ldap.initialize('ldap://SPOTDC01:389')

            # synchronous bind
            #ldap_object.simple_bind_s(username, password)

            self.write(json.dumps({'message': "Login successful"}))

        except ldap.INVALID_CREDENTIALS as e:
            self.set_status(httplib.UNAUTHORIZED)
            self.write(json.dumps({'errorText': 'Invalid username or password'}))
            logging.error('Invalid username or password')

        except ldap.LDAPError as e:
            if isinstance(e.message, dict) and 'desc' in e.message:
                self.set_status(httplib.GATEWAY_TIMEOUT)
                self.write(json.dumps({'errorText': e.message['desc']}))
                logging.error(e.message['desc'])
            else:
                logging.error(e)

        except Exception as e:
            self.set_status(httplib.INTERNAL_SERVER_ERROR)
            self.write(json.dumps({'errorText': 'Internal Error'}))
            logging.error(e)

        self.set_header('Content-Type', 'application/json')


    def _parse_username(self, username):
        if username.find("@") > 0:
            return username
        else:
            return username + '@' + 'spottrading.com'