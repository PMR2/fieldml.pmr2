import unittest
import logging
import os
from StringIO import StringIO
from json import loads
from gzip import open as gzip_open
from tempfile import mkdtemp
from os.path import dirname
from os.path import isdir
from os.path import join
from os import listdir
from shutil import rmtree

import zope.component
from zope.publisher.interfaces import NotFound
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName

from pmr2.app.settings.interfaces import IPMR2GlobalSettings
from pmr2.app.workspace.content import Workspace
from pmr2.app.workspace.interfaces import IStorageUtility
from pmr2.app.workspace.interfaces import IStorage
from pmr2.app.exposure.interfaces import IExposureFile
from pmr2.app.exposure.content import ExposureFile
from pmr2.app.exposure.content import Exposure
from pmr2.app.exposure.browser import util

from pmr2.app.annotation import note_factory
from pmr2.app.annotation.tests import adapter
from pmr2.app.annotation.tests import content
from pmr2.app.annotation.interfaces import IExposureFileAnnotator

from pmr2.testing.base import TestRequest

from fieldml.pmr2.interfaces import ISparcConvertUtility
from fieldml.pmr2.interfaces import IZincJSUtility
from fieldml.pmr2.interfaces import ISettings
from fieldml.pmr2.utility import SparcConvertUtility
from fieldml.pmr2.utility import ZincJSUtility
from fieldml.pmr2.testing import layer
from fieldml.pmr2.browser.view import ScaffoldViewer
from fieldml.pmr2.browser.view import ScaffoldvuerView


with gzip_open(join(dirname(__file__), 'input', 'test.ex2.gz')) as fd:
    test_exfile_content = fd.read()


neon_files = {}

for fn in ['CubeSquareLine.neon', 'cubesquareline_sml.exf']:
    with open(join(dirname(__file__), 'input', fn)) as fd:
        neon_files[fn] = fd.read()


class UtilsTestCase(unittest.TestCase):

    # Just using the integration layer for now until a way to set up and
    # test with just the FIXTURE is done.
    layer = layer.FIELDML_UTILITY_INTEGRATION_LAYER

    def setUp(self):
        self.portal = self.layer['portal']
        self.testdir = mkdtemp()
        self.logger = logging.getLogger()

        self.stream = StringIO()
        self.handler = logging.StreamHandler(self.stream)
        self.handler.setFormatter(logging.Formatter(
            u'%(asctime)s %(levelname)s %(name)s %(message)s'))
        self.logger.addHandler(self.handler)
        self.logger.setLevel(logging.DEBUG)

    def tearDown(self):
        rmtree(self.testdir)
        self.logger.removeHandler(self.handler)

    def test_settings(self):
        registry = zope.component.getUtility(IRegistry)
        settings = registry.forInterface(
            ISettings, prefix='fieldml.pmr2.settings')
        self.assertEqual(
            settings.zincjs_group_exporter, 'zincjs_group_exporter')
        self.assertEqual(
            settings.sparc_convert, 'sparc-convert')

    def test_zincjs_utility_registered(self):
        utility = zope.component.queryUtility(IZincJSUtility)
        self.assertTrue(isinstance(utility, ZincJSUtility))

    def test_zincjs_utility_usage_without_binary(self):
        utility = zope.component.queryUtility(IZincJSUtility)
        utility(self.testdir, '')

        self.assertIn(
            'unable to find the zincjs_group_exporter binary',
            self.stream.getvalue()
        )

    @unittest.skipIf(
        'ZINCJS_GROUP_EXPORTER_BIN' not in os.environ,
        'define ZINCJS_GROUP_EXPORTER_BIN environment variable to run full '
        'integration test')
    def test_with_success_generation(self):
        registry = zope.component.getUtility(IRegistry)
        utility = zope.component.queryUtility(IZincJSUtility)
        settings = registry.forInterface(
            ISettings, prefix='fieldml.pmr2.settings')
        settings.zincjs_group_exporter = os.environ[
            'ZINCJS_GROUP_EXPORTER_BIN'].decode('utf8')

        utility(self.testdir, test_exfile_content)

        scaffolddir = join(self.testdir, 'scaffold')
        self.assertTrue(isdir(scaffolddir))
        self.assertEqual(19, len(listdir(scaffolddir)))

    @unittest.skipIf(
        'ZINCJS_GROUP_EXPORTER_BIN' not in os.environ,
        'define ZINCJS_GROUP_EXPORTER_BIN environment variable to run full '
        'integration test')
    def test_zincjs_scaffold_view(self):
        oid = 'scaffold'
        fid = 'test.ex2'
        pmr2_settings = zope.component.getUtility(IPMR2GlobalSettings)
        pmr2_settings.repo_root = self.testdir

        registry = zope.component.getUtility(IRegistry)
        utility = zope.component.queryUtility(IZincJSUtility)
        settings = registry.forInterface(
            ISettings, prefix='fieldml.pmr2.settings')
        settings.zincjs_group_exporter = os.environ[
            'ZINCJS_GROUP_EXPORTER_BIN'].decode('utf8')

        su = zope.component.getUtility(IStorageUtility, name='dummy_storage')
        su._dummy_storage_data[oid] = [{
            fid: test_exfile_content,
        }]

        w = Workspace(oid)
        w.storage = 'dummy_storage'
        self.portal.workspace[oid] = w

        exposure = Exposure(oid)
        exposure.commit_id = u'0'
        exposure.workspace = u'/plone/workspace/%s' % oid

        self.portal.exposure[oid] = exposure
        self.portal.exposure[oid][fid] = ExposureFile(fid)

        context = self.portal.exposure[oid][fid]
        request = TestRequest()
        annotator = zope.component.getUtility(IExposureFileAnnotator,
            name='scaffold_viewer')(context, request)
        annotator(data=())

        out_root = join(self.testdir, 'plone', 'exposure', oid, fid)
        self.assertTrue(isdir(out_root))

        # TODO try a test with testbrowser
        request = self.layer['portal'].REQUEST
        view = ScaffoldViewer(context, request)
        base_render = view()
        self.assertIn('MAPcorePortalArea', base_render)

        view.publishTraverse(request, 'scaffold')

        with self.assertRaises(NotFound):
            view()

        view.publishTraverse(request, '0')
        root_json = view()
        with open(join(out_root, 'scaffold', '0')) as fd:
            contents = fd.read()
            self.assertEqual(contents, root_json)
            self.assertTrue(isinstance(loads(root_json), list))

        # destroy that file and recreate
        with open(join(out_root, 'scaffold', '0'), 'w') as fd:
            fd.write('???')

        # this should break the view
        with self.assertRaises(ValueError):
            loads(view())

        request = TestRequest()
        annotator = zope.component.getUtility(IExposureFileAnnotator,
            name='scaffold_viewer')(context, request)
        annotator(data=())

        root_json = view()
        with open(join(out_root, 'scaffold', '0')) as fd:
            contents = fd.read()
            self.assertEqual(contents, root_json)
            self.assertTrue(isinstance(loads(root_json), list))

    def test_zincjs_scaffold_view(self):
        oid = 'scaffold'
        fid = 'test.ex2'
        pmr2_settings = zope.component.getUtility(IPMR2GlobalSettings)
        pmr2_settings.repo_root = self.testdir

        su = zope.component.getUtility(IStorageUtility, name='dummy_storage')
        su._dummy_storage_data[oid] = [{
            fid: test_exfile_content,
            'view.json': '{}',
        }]

        w = Workspace(oid)
        w.storage = 'dummy_storage'
        self.portal.workspace[oid] = w
        exposure = Exposure(oid)
        exposure.commit_id = u'0'
        exposure.workspace = u'/plone/workspace/%s' % oid
        self.portal.exposure[oid] = exposure
        self.portal.exposure[oid][fid] = ExposureFile(fid)

        context = self.portal.exposure[oid][fid]
        request = TestRequest()
        annotator = zope.component.getUtility(IExposureFileAnnotator,
            name='scaffold_viewer')(context, request)
        annotator(data=())

        # TODO try a test with testbrowser
        request = self.layer['portal'].REQUEST
        view = ScaffoldViewer(context, request)
        # since this was not adapted through the standard flow, this
        # need to be manually set
        view.__name__ = 'scaffold_viewer'
        base_render = view()
        self.assertIn('MAPcorePortalArea', base_render)

        # when note.view_json is not defined
        view.publishTraverse(request, 'view.json')
        self.assertEqual(view(), view.default_view_json)

        # when the view_json is set.
        annotator(data=(('view_json', 'view.json'),))
        self.assertEqual(
            'http://nohost/plone/workspace/scaffold/@@rawfile/0/view.json',
            view(),
        )

    def test_sparc_convert_registered(self):
        utility = zope.component.queryUtility(ISparcConvertUtility)
        self.assertTrue(isinstance(utility, SparcConvertUtility))

    def test_sparc_utility_usage_without_binary(self):
        utility = zope.component.queryUtility(ISparcConvertUtility)
        utility(self.testdir, None, '')

        self.assertIn(
            'unable to find the sparc-convert binary',
            self.stream.getvalue()
        )

    def test_sparc_utility_get_paths(self):
        utility = zope.component.queryUtility(ISparcConvertUtility)
        paths = utility.get_paths("""
        {
          "RootRegion": {
            "ChildRegions": [
              {
                "ChildRegions": [
                  {
                    "ChildRegions": [
                      {
                        "Model": {
                          "Sources": [
                            {
                              "FileName": "source1.exnode",
                              "RegionName": "/source1",
                              "Type": "FILE"
                            },
                            {
                              "FileName": "source1.exelem",
                              "RegionName": "/source1",
                              "Type": "FILE"
                            }
                          ]
                        }
                      },
                      {
                        "Model": {
                          "Sources": [
                            {
                              "FileName": "src/source2.exnode",
                              "RegionName": "/source2",
                              "Type": "FILE"
                            },
                            {
                              "FileName": "src/source2.exelem",
                              "RegionName": "/source2",
                              "Type": "FILE"
                            }
                          ]
                        }
                      }
                    ],
                    "Model": {
                      "Sources": [
                        {
                          "FileName": "source1.exnode",
                          "RegionName": "/source1",
                          "Type": "FILE"
                        },
                        {
                          "FileName": "source1.exelem",
                          "RegionName": "/source1",
                          "Type": "FILE"
                        }
                      ]
                    }
                  }
                ]
              }
            ]
          }
        }
        """)

        self.assertEqual(paths, {
            'source1.exnode', 'source1.exelem',
            'src/source2.exnode', 'src/source2.exelem',
        })

        su = zope.component.getUtility(IStorageUtility, name='dummy_storage')
        su._dummy_storage_data['fake'] = [{
            'source1.exnode': 'source1.exnode',
            'src/source2.exnode': 'source2.exnode',
            'source1.exelem': 'source1.exelem',
            'src/source2.exelem': 'source2.exelem',
        }]
        w = Workspace('fake')
        w.storage = 'dummy_storage'
        storage = IStorage(w)

        utility.extract_paths(self.testdir, storage, paths)
        with open(join(self.testdir, 'src', 'source2.exelem')) as fd:
            self.assertEqual(fd.read(), 'source2.exelem')

    @unittest.skipIf(
        'SPARC_CONVERT_BIN' not in os.environ,
        'define SPARC_CONVERT_BIN environment variable to run full '
        'integration test')
    def test_sparc_convert_full(self):
        wid = 'cubesquare'
        fid = 'CubeSquareLine.neon'
        pmr2_settings = zope.component.getUtility(IPMR2GlobalSettings)
        pmr2_settings.repo_root = self.testdir

        registry = zope.component.getUtility(IRegistry)
        utility = zope.component.queryUtility(ISparcConvertUtility)
        settings = registry.forInterface(
            ISettings, prefix='fieldml.pmr2.settings')
        settings.sparc_convert = os.environ[
            'SPARC_CONVERT_BIN'].decode('utf8')

        su = zope.component.getUtility(IStorageUtility, name='dummy_storage')
        su._dummy_storage_data[wid] = [neon_files]

        w = Workspace(wid)
        w.storage = 'dummy_storage'
        self.portal.workspace[wid] = w

        exposure = Exposure(wid)
        exposure.commit_id = u'0'
        exposure.workspace = u'/plone/workspace/%s' % wid

        self.portal.exposure[wid] = exposure
        self.portal.exposure[wid][fid] = ExposureFile(fid)

        context = self.portal.exposure[wid][fid]
        request = TestRequest()
        annotator = zope.component.getUtility(IExposureFileAnnotator,
            name='scaffoldvuer')(context, request)
        annotator(data=())

        out_root = join(self.testdir, 'plone', 'exposure', wid, fid)
        self.assertTrue(isdir(out_root))

        # skip the neon file.
        fn = 'cubesquareline_sml.exf'
        with open(join(out_root, 'scaffoldvuer', 'src', fn)) as fd:
            self.assertEqual(fd.read(), neon_files[fn])

        # TODO try a test with testbrowser
        request = self.layer['portal'].REQUEST
        view = ScaffoldvuerView(context, request)
        # have to manually set view name as it was not adapted
        view.__name__ = 'scaffoldvuer'
        base_render = view()
        self.assertIn('MAPcorePortalArea', base_render)

        # get the root view
        entry = 'ArgonSceneExporterWebGL_metadata.json'
        view.publishTraverse(request, entry)
        root_json = view()
        with open(join(out_root, 'scaffoldvuer', entry)) as fd:
            contents = fd.read()
            self.assertEqual(contents, root_json)
            self.assertTrue(isinstance(loads(root_json), list))

        # destroy that file and recreate
        with open(join(out_root, 'scaffoldvuer', entry), 'w') as fd:
            fd.write('???')

        # this should break the view
        with self.assertRaises(ValueError):
            loads(view())
