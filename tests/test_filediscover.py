# coding: utf-8

from __future__ import unicode_literals

import os
import shutil
import tempfile

from prettyconf.configuration import ConfigurationDiscovery
from prettyconf.exceptions import InvalidPath
from prettyconf.loaders import IniFileConfigurationLoader
from .base import BaseTestCase


# noinspection PyStatementEffect
class ConfigFilesDiscoveryTestCase(BaseTestCase):
    def setUp(self):
        super(ConfigFilesDiscoveryTestCase, self).setUp()
        self.tmpdirs = []

    def tearDown(self):
        super(ConfigFilesDiscoveryTestCase, self).tearDown()
        for tmpdir in self.tmpdirs:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_config_file_parsing(self):
        self._create_file(self.test_files_path + "/../.env")
        self._create_file(self.test_files_path + "/../setup.cfg")  # invalid settings
        self._create_file(self.test_files_path + "/../settings.ini", "[settings]")
        discovery = ConfigurationDiscovery(os.path.dirname(self.test_files_path))
        self.assertEqual(len(discovery.config_files), 2)  # 2 *valid* files created

    def test_should_not_look_for_parent_directory_when_it_finds_valid_configurations(self):
        self._create_file(self.test_files_path + '/../../settings.ini', '[settings]')
        self._create_file(self.test_files_path + '/../../.env')
        self._create_file(self.test_files_path + '/../.env')
        self._create_file(self.test_files_path + '/../settings.ini', '[settings]')

        discovery = ConfigurationDiscovery(os.path.dirname(self.test_files_path))
        self.assertEqual(len(discovery.config_files), 2)
        filenames = [cfg.filename for cfg in discovery.config_files]
        self.assertIn(os.path.abspath(self.test_files_path + '/../.env'), filenames)
        self.assertIn(os.path.abspath(self.test_files_path + '/../settings.ini'), filenames)

    def test_should_look_for_parent_directory_when_it_finds_invalid_configurations(self):
        self._create_file(self.test_files_path + '/../../settings.ini', '[settings]')
        self._create_file(self.test_files_path + '/../../.env')
        self._create_file(self.test_files_path + '/../invalid.cfg', '')
        self._create_file(self.test_files_path + '/../settings.ini', '')

        discovery = ConfigurationDiscovery(os.path.dirname(self.test_files_path))
        self.assertEqual(len(discovery.config_files), 2)
        filenames = [cfg.filename for cfg in discovery.config_files]
        self.assertIn(os.path.abspath(self.test_files_path + '/../../.env'), filenames)
        self.assertIn(os.path.abspath(self.test_files_path + '/../../settings.ini'), filenames)

    def test_default_root_path_should_default_to_root_directory(self):
        discovery = ConfigurationDiscovery(os.path.dirname(self.test_files_path))
        assert discovery.root_path == "/"

    def test_root_path_should_be_parent_of_starting_path(self):
        with self.assertRaises(InvalidPath):
            ConfigurationDiscovery('/foo', root_path='/foo/bar/baz/')

    def test_use_configuration_from_root_path_when_no_other_was_found(self):
        root_dir = tempfile.mkdtemp()
        self.tmpdirs.append(root_dir)

        start_path = os.path.join(root_dir, 'some/directories/to/start/looking/for/settings')
        os.makedirs(start_path)

        test_file = os.path.realpath(os.path.join(root_dir, 'settings.ini'))
        with open(test_file, 'a') as file_:
            file_.write('[settings]')
        self.files.append(test_file)  # Required to removed it at tearDown

        discovery = ConfigurationDiscovery(start_path, root_path=root_dir)
        filenames = [cfg.filename for cfg in discovery.config_files]
        self.assertEqual([test_file], filenames)

    def test_lookup_should_stop_at_root_path(self):
        test_dir = tempfile.mkdtemp()
        self.tmpdirs.append(test_dir)  # Cleanup dir at tearDown

        start_path = os.path.join(test_dir, 'some/dirs/without/config')
        os.makedirs(start_path)

        # create a file in the test_dir
        test_file = os.path.realpath(os.path.join(test_dir, 'settings.ini'))
        with open(test_file, 'a') as file_:
            file_.write('[settings]')
        self.files.append(test_file)  # Required to removed it at tearDown

        root_dir = os.path.join(test_dir, 'some', 'dirs')  # No settings here

        discovery = ConfigurationDiscovery(start_path, root_path=root_dir)
        self.assertEqual(discovery.config_files, [])

    def test_inifile_discovery_should_ignore_invalid_files_without_raising_exception(self):
        root_dir = tempfile.mkdtemp()
        self.tmpdirs.append(root_dir)

        cfg_dir = os.path.join(root_dir, "some/strange")
        os.makedirs(cfg_dir)

        with open(os.path.join(cfg_dir, "config.cfg"), "wb") as cfg_file:
            cfg_file.write('&ˆ%$#$%ˆ&*()(*&ˆ'.encode('utf8'))
            self.files.append(cfg_file.name)

        with open(os.path.join(root_dir, "some/config.ini"), "wb") as cfg_file:
            cfg_file.write('$#%ˆ&*((*&ˆ%'.encode('utf8'))

        discovery = ConfigurationDiscovery(cfg_dir, filetypes=(IniFileConfigurationLoader,))
        self.assertEqual(discovery.config_files, [])
