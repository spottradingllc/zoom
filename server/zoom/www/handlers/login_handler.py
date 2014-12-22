import httplib
import json
import ldap
import logging

import tornado.escape
import tornado.gen
import tornado.web

from zoom.common.decorators import TimeThis


class LoginHandler(tornado.web.RequestHandler):

    @property
    def read_write_groups(self):
        """
        :rtype: list
        """
        return self.application.configuration.read_write_groups

    @property
    def ldap_url(self):
        """
        :rtype: str
        """
        return self.application.configuration.ldap_url

    #@tornado.gen.coroutine
    @TimeThis(__file__)
    def post(self):
        try:
            request = json.loads(self.request.body)  # or '{"login": {}}'
            user = request['username']
            password = request['password']
            # expire the persistent cookie after 14 days
            days_to_expire = 14

            # User, password combination Case 1 of 4
            if not user and not password:
                logging.info('No username and no password set. Clearing cookie.')
                self.clear_cookie("username")
                self.clear_cookie("read_write")
                self.write({'errorText': "No username and no password: you have been logged out."})
                self.set_status(httplib.UNAUTHORIZED)

            # Case 2 of 4 and 3 of 4
            elif not user or not password:
                logging.info('No username or no password set.')
                self.write({'errorText': "No username or no password: try again."})
                self.set_status(httplib.UNAUTHORIZED)

            # Case 4 of 4
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
                self.set_cookie("username", user, expires_days=days_to_expire)
                if can_read_write:
                    self.set_cookie("read_write", user, expires_days=days_to_expire)
                self.write({'message': "Login successful"})
                logging.info('successful login')

        except ldap.INVALID_CREDENTIALS:
            self.set_status(httplib.UNAUTHORIZED)
            self.write({'errorText': 'Invalid username or password'})
            logging.error('Invalid username or password')

        except ldap.LDAPError as e:
            if isinstance(e.message, dict) and 'desc' in e.message:
                self.set_status(httplib.GATEWAY_TIMEOUT)
                self.write({'errorText': e.message['desc']})
                logging.error(e)
            else:
                logging.error(e)

        except Exception as e:
            self.set_status(httplib.INTERNAL_SERVER_ERROR)
            self.write({'errorText': e.message['desc']})
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
