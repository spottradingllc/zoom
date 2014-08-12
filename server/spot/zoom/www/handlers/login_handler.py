import httplib
import json
import ldap
import logging

import tornado.escape
import tornado.gen
import tornado.web

from spot.zoom.www.utils.decorators import timethis


class LoginHandler(tornado.web.RequestHandler):

    @property
    def read_write_groups(self):
        return self.application.configuration.read_write_groups

    @property
    def ldap_url(self):
        return self.application.configuration.ldap_url

    #@tornado.gen.coroutine
    @timethis(__file__)
    def post(self):
        request = json.loads(self.request.body)  # or '{"login": {}}'

        try:
            user = request['username']
            password = request['password']

            if not user or not password:
                logging.info('No user or password set. Clearing cookie.')
                self.clear_cookie("username")
                self.clear_cookie("read_write")
                self.write(json.dumps({'message': "Logout successful"}))

            else:
                username = self._get_full_username(user)

                # connect to ldap server
                ldap_object = ldap.initialize(self.ldap_url)

                # synchronous bind
                ldap_object.simple_bind_s(username, password)

                base_dn = "OU=Production,OU=Spot Trading,DC=spottrading,DC=com"
                results = ldap_object.search_s(
                    base_dn,
                    ldap.SCOPE_SUBTREE,
                    filterstr='userPrincipalName={0}'.format(username))

                user_groups = results[0][1]['memberOf']

                # check if user is in the appropriate group to have read/write
                # access to the UI
                can_read_write = False
                for group in self.read_write_groups:
                    if group in user_groups:
                        can_read_write = True
                        break

                # set cookie(s) if login successful
                self.set_cookie("username", user)
                if can_read_write:
                    self.set_cookie("read_write", user)
                self.write(json.dumps({'message': "Login successful"}))

        except ldap.INVALID_CREDENTIALS:
            self.set_status(httplib.UNAUTHORIZED)
            self.write(json.dumps({'errorText': 'Invalid username or password'}))
            logging.error('Invalid username or password')

        except ldap.LDAPError as e:
            if isinstance(e.message, dict) and 'desc' in e.message:
                self.set_status(httplib.GATEWAY_TIMEOUT)
                self.write(json.dumps({'errorText': e.message['desc']}))
                logging.error(e)
            else:
                logging.error(e)

        except Exception as e:
            self.set_status(httplib.INTERNAL_SERVER_ERROR)
            self.write(json.dumps({'errorText': 'Internal Error'}))
            logging.exception(e)

        self.set_header('Content-Type', 'application/json')

    def _get_full_username(self, username):
        if '@spottrading.com' not in username:
            return '{0}@spottrading.com'.format(username)
        else:
            return username

    def get_current_user(self):
        user_json = self.get_cookie("user")
        if user_json:
            return user_json
        else:
            return None
