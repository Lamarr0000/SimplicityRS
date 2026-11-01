import unittest
import urllib.error
from unittest.mock import Mock
from model_connection import ModelConnection


class ConnectionErrors(unittest.TestCase):
    def connection(self,remote=True):
        connection=ModelConnection.__new__(ModelConnection)
        connection.remote=remote
        connection.endpoint='https://192.168.182.1:11436' if remote else 'http://127.0.0.1:11434'
        connection.headers={}
        connection.opener=Mock()
        return connection

    def test_remote_timeout_names_host_services_without_claiming_a_cause(self):
        connection=self.connection()
        connection.opener.open.side_effect=urllib.error.URLError(TimeoutError())
        with self.assertRaisesRegex(RuntimeError,'host model server and encrypted VM relay'):
            connection.open('/api/version')

    def test_local_timeout_does_not_direct_user_to_vm_relay(self):
        connection=self.connection(False)
        connection.opener.open.side_effect=TimeoutError()
        with self.assertRaisesRegex(RuntimeError,'local model connection'):
            connection.open('/api/chat')

    def test_authentication_failure_remains_an_http_error(self):
        connection=self.connection()
        connection.opener.open.side_effect=urllib.error.HTTPError(connection.endpoint,403,'Forbidden',{},None)
        with self.assertRaises(urllib.error.HTTPError) as error:connection.open('/api/version')
        error.exception.close()


if __name__=='__main__':unittest.main()
