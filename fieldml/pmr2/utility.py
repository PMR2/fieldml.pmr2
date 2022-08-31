import os
import posixpath
import json
import zipfile
from io import BytesIO
from os import walk
from os.path import join, dirname, isdir, relpath, sep
from shutil import rmtree
from subprocess import Popen, PIPE, call
from logging import getLogger
from distutils.spawn import find_executable

import zope.component
import zope.interface

from plone.registry.interfaces import IRegistry
from pmr2.app.annotation.factory import has_note
from pmr2.app.exposure.interfaces import IExposureDownloadTool

from fieldml.pmr2.interfaces import (
    IZincJSUtility,
    ISparcConvertUtility,
    ISparcDatasetToolsUtility,
    ISettings,
)

logger = getLogger(__name__)
prefix = 'fieldml.pmr2.settings'
settings_json_path = join(dirname(__file__), 'mesh_generator-settings.json')


def _find(root):
    for dirname, dnames, fnames in walk(root):
        for fname in fnames:
            fullpath = join(dirname, fname)
            yield relpath(fullpath, root), fullpath
        for dname in dnames:
            fullpath = join(dirname, dname)
            yield relpath(fullpath, root) + sep, fullpath


def _create_zip(root):
    stream = BytesIO()
    zf = zipfile.ZipFile(stream, mode='w')

    for path, fullpath in _find(root):
        znfo = zipfile.ZipInfo(path)
        if isdir(fullpath):
            contents = ''
        else:
            znfo.compress_type = zipfile.ZIP_DEFLATED
            with open(fullpath) as fd:
                contents = fd.read()
        znfo.file_size = len(contents)
        znfo.external_attr = 0o777 << 16L
        zf.writestr(znfo, contents)
    zf.close()
    return stream.getvalue()


@zope.interface.implementer(IExposureDownloadTool)
class ArgonSDSArchiveDownloadTool(object):
    """
    Argon SDS Download link
    """

    label = u'SPARC Dataset Archive'
    suffix = '.zip'
    mimetype = 'application/zip'

    def get_download_link(self, exposure_object):
        if not has_note(exposure_object, 'argon_sds_archive'):
            return
        return exposure_object.absolute_url() + '/argon_sds_archive/download'

    def download(self, exposure_object, request):
        # Implemented in the view
        pass


@zope.interface.implementer(IZincJSUtility)
class ZincJSUtility(object):

    def __call__(self, root, model_data):
        registry = zope.component.getUtility(IRegistry)
        try:
            settings = registry.forInterface(ISettings, prefix=prefix)
        except KeyError:
            logger.warning(
                "settings for '%s' not found; the fieldml.pmr2 may need to be "
                "reactivated", prefix,
            )
            return

        executable = find_executable(settings.zincjs_group_exporter)
        if executable is None:
            logger.warning(
                'unable to find the zincjs_group_exporter binary; please '
                "verify the registry key '%s' is set to the valid binary",
                prefix
            )
            return

        # restrict env to just the bare minimum, i.e. don't let things
        # like PYTHONPATH (if set) to interfere with the calling.
        env = {k: os.environ[k] for k in ('PATH',)}
        p = Popen([executable, root], stdin=PIPE, env=env)
        p.communicate(model_data)


class SparcUtilityBase(object):
    """
    Common methods that deal with sparc programs and their input files.
    """

    executable_key = None
    binary_name = None

    def get_paths(self, sparc_input, sparc_input_path):
        def normalize(path):
            return posixpath.normpath(posixpath.join(
                posixpath.dirname(
                    posixpath.join(posixpath.sep, sparc_input_path)),
                path.replace('\\', '/'),
            ))[1:]

        def get_region_model_sources(region):
            sources = region.get('Model', {}).get('Sources', [])
            results = {
                normalize(source['FileName']) for source in sources
                if source['Type'] == 'FILE'
            }
            for child in region.get('ChildRegions', []):
                results.update(get_region_model_sources(child))
            return results

        try:
            sparc_doc = json.loads(sparc_input)
            return get_region_model_sources(sparc_doc['RootRegion'])
            # watch out for absolute paths
        except (KeyError, TypeError, ValueError, AttributeError):
            return set()

    def extract_paths(self, rootdir, storage, paths):
        # write out the data for each of the referenced paths
        for path in paths:
            # assume data can only be returned if the path is a proper
            # partial path
            data = storage.file(path)
            fullpath = join(rootdir, path)
            if not isdir(dirname(fullpath)):
                os.makedirs(dirname(fullpath))
            with open(fullpath, 'wb') as fd:
                fd.write(data)

    def __call__(
            self, working_dir, temp_dir, storage, sparc_input,
            sparc_input_path, **kw):
        registry = zope.component.getUtility(IRegistry)
        try:
            settings = registry.forInterface(ISettings, prefix=prefix)
        except KeyError:
            logger.warning(
                "settings for '%s' not found; the fieldml.pmr2 may need to be "
                "reactivated", prefix,
            )
            return

        executable = find_executable(getattr(settings, self.executable_key))
        if executable is None:
            logger.warning(
                'unable to find the %s binary; please '
                "verify the registry key '%s' is set to the valid binary",
                self.binary_name,
                prefix,
            )
            return

        # figure out what paths to extract
        paths = self.get_paths(sparc_input, sparc_input_path)

        # the sparc related file
        sparc_path = join(temp_dir, sparc_input_path)
        if not isdir(dirname(sparc_path)):
            os.makedirs(dirname(sparc_path))
        with open(sparc_path, 'w') as fd:
            fd.write(sparc_input)

        self.extract_paths(temp_dir, storage, paths)

        # restrict env to just the bare minimum, i.e. don't let things
        # like PYTHONPATH (if set) to interfere with the calling.
        env = {k: os.environ[k] for k in ('PATH',)}

        # then invoke the process;
        self.call(executable, sparc_path, env, working_dir, temp_dir, **kw)

    def call(self, executable, sparc_path, env, working_dir, temp_dir, **kw):
        raise NotImplementedError


@zope.interface.implementer(ISparcConvertUtility)
class SparcConvertUtility(SparcUtilityBase):

    executable_key = 'sparc_convert'
    binary_name = 'sparc-convert'
    sparc_filename = 'input.neon'

    def call(self, executable, sparc_path, env, working_dir, temp_dir, **kw):
        call([executable, 'web-gl', sparc_path], env=env, cwd=working_dir)


@zope.interface.implementer(ISparcDatasetToolsUtility)
class SparcDatasetToolsUtility(SparcUtilityBase):
    """
    The sparc-dataset-tools utility
    """

    executable_key = 'create_scaffold_dataset'
    binary_name = 'create-scaffold-dataset'
    sparc_filename = 'input.argon'

    def call(self, executable, sparc_path, env, working_dir, temp_dir, **kw):
        # TODO if a custom settings_file be specified, load it from
        # dict(self.data)['settings_file'] and write it out.
        # settings_json_path = join(temp_dir, 'mesh_generator-settings.json')

        # Provide the required environment variables to activate osmesa
        osmesa_env = {}
        osmesa_env.update(env)
        osmesa_env.update({
            'PYOPENGL_PLATFORM': 'osmesa',
            'OC_EXPORTER_RENDERER': 'osmesa',
        })

        call(
            [executable, working_dir, settings_json_path, sparc_path],
            env=osmesa_env, cwd=working_dir,
        )
