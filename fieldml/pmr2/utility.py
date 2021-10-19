import os
import json
from os.path import join, dirname, isdir
from shutil import rmtree
from subprocess import Popen, PIPE, call
from logging import getLogger
from distutils.spawn import find_executable

import zope.component
import zope.interface

from plone.registry.interfaces import IRegistry

from fieldml.pmr2.interfaces import IZincJSUtility
from fieldml.pmr2.interfaces import ISparcConvertUtility
from fieldml.pmr2.interfaces import ISettings

logger = getLogger(__name__)
prefix = 'fieldml.pmr2.settings'


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


@zope.interface.implementer(ISparcConvertUtility)
class SparcConvertUtility(object):

    def get_paths(self, neon_input):
        def get_region_model_sources(region):
            sources = region.get('Model', {}).get('Sources', [])
            results = {
                source['FileName'] for source in sources
                if source['Type'] == 'FILE'
            }
            for child in region.get('ChildRegions', []):
                results.update(get_region_model_sources(child))
            return results

        try:
            neon_doc = json.loads(neon_input)
            return get_region_model_sources(neon_doc['RootRegion'])
            # watch out for absolute paths
        except (KeyError, TypeError, ValueError, AttributeError):
            return []

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

    def __call__(self, working_dir, storage, neon_input):
        registry = zope.component.getUtility(IRegistry)
        try:
            settings = registry.forInterface(ISettings, prefix=prefix)
        except KeyError:
            logger.warning(
                "settings for '%s' not found; the fieldml.pmr2 may need to be "
                "reactivated", prefix,
            )
            return

        executable = find_executable(settings.sparc_convert)
        if executable is None:
            logger.warning(
                'unable to find the sparc-convert binary; please '
                "verify the registry key '%s' is set to the valid binary",
                prefix
            )
            return

        # figure out what paths to extract
        paths = self.get_paths(neon_input)

        # create a temporary directory in working_dir to write out; this
        # is currently done in the working_dir which is assumed to be
        # freshly created by the caller of this function.
        tmpdir = join(working_dir, 'src')
        os.mkdir(tmpdir)  # so this should always succeed
        # the neon file
        neon_path = join(tmpdir, 'input.neon')
        with open(neon_path, 'w') as fd:
            fd.write(neon_input)

        self.extract_paths(tmpdir, storage, paths)

        # then invoke the process;
        # restrict env to just the bare minimum, i.e. don't let things
        # like PYTHONPATH (if set) to interfere with the calling.
        # TODO need to extract Sources
        env = {k: os.environ[k] for k in ('PATH',)}
        call([executable, 'web-gl', neon_path], env=env, cwd=working_dir)
        # TODO cleanup the temporary files?
