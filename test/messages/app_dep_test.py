from unittest import TestCase
from zoom.www.messages.application_dependencies import ApplicationDependenciesMessage


class AppDependencyMessageTest(TestCase):

    def test_update(self):
        path = '/foo'
        mes = ApplicationDependenciesMessage()
        d1 = {"configuration_path": path, "dependencies": list()}

        # test dict gets update
        data = {path: d1}
        mes.update(data)
        self.assertEqual(mes.application_dependencies, data)

        # test data change for same key
        d2 = d1.copy()
        d2['dependencies'] = [1, 2, 3]
        data = {path: d2}
        mes.update(data)

        self.assertEqual(mes.application_dependencies.get(path), d2)

    def test_combine(self):
        """
        Test that two ApplicationDependenciesMessage can be combined into 1
        """
        path1 = '/foo'
        mes1 = self._create_dep_message(path1)

        path2 = '/bar'
        mes2 = self._create_dep_message(path2)

        expected = {
            path2: {"configuration_path": path2, "dependencies": list()},
            path1: {"configuration_path": path1, "dependencies": list()}
        }
        mes1.combine(mes2)

        self.assertEqual(mes1.application_dependencies, expected)

    def test_remove(self):
        path1 = '/foo'
        path2 = '/bar'
        mes = self._create_dep_message(path1, path2)

        expected = {
            path2: {"configuration_path": path2, "dependencies": list()},
        }
        mes.remove({
            path1: {"configuration_path": path1, "dependencies": list()}
        })

        self.assertEqual(mes.application_dependencies, expected)

    def test_clear(self):
        mes = self._create_dep_message('/foo', '/bar')
        mes.clear()
        self.assertEqual(mes.application_dependencies, {})

    def test_len(self):
        mes = self._create_dep_message('/foo', '/bar')
        self.assertEqual(len(mes), 2)

    def _create_dep_message(self, *args):
        """
        :rtype: ApplicationDependenciesMessage
        """
        mes = ApplicationDependenciesMessage()
        for path in args:
            data = {
                path: {"configuration_path": path, "dependencies": list()}
            }
            mes.update(data)

        return mes
