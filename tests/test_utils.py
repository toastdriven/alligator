import re
import unittest

from alligator import __version__, version
from alligator.exceptions import UnknownModuleError, UnknownCallableError
from alligator.utils import (
    determine_module,
    determine_name,
    import_module,
    import_attr
)


class UtilsTestCase(unittest.TestCase):
    def test_import_module(self):
        module = import_module('random')
        self.assertEqual(module.__name__, 'random')

        with self.assertRaises(UnknownModuleError) as cm:
            import_module('nopenopeNOPE')

    def test_import_attr(self):
        choice = import_attr('random', 'choice')
        self.assertEqual(choice.__name__, 'choice')

        with self.assertRaises(UnknownCallableError) as cm:
            import_attr('random', 'yolo')

    def test_determine_module(self):
        from alligator.backends.locmem_backend import Client
        self.assertEqual(
            determine_module(Client),
            'alligator.backends.locmem_backend'
        )

    def test_determine_name(self):
        from alligator.backends.locmem_backend import Client
        self.assertEqual(determine_name(import_module), 'import_module')
        self.assertEqual(determine_name(Client), 'Client')
        self.assertEqual(determine_name(lambda x: x), '<lambda>')

    def test_version(self):
        semver = re.compile(r'[\d]+\.[\d]+\.[\d]+')

        v = version()
        self.assertTrue(semver.match(v))

        if len(__version__) > 3:
            self.assertTrue(__version__[3] in v)
