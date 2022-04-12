import zope.interface
import zope.component

from os import makedirs
from os.path import exists
from os.path import isdir
from os.path import join
from shutil import rmtree

from pmr2.app.factory import named_factory
from pmr2.app.settings.interfaces import IPMR2GlobalSettings
from pmr2.app.annotation.interfaces import *
from pmr2.app.annotation.annotator import ExposureFileAnnotatorBase
from pmr2.app.exposure.interfaces import IExposureSourceAdapter
from pmr2.app.workspace.interfaces import IStorage

from fieldml.pmr2.interfaces import *
from fieldml.pmr2.rdf import RdfExposureNoteHelper


def make_view_dirs(settings, view):
    root = settings.dirOf(view.context)
    if not isdir(root):
        makedirs(root)

    working_dir = join(root, view.__name__)
    temp_dir = join(root, '_tmp_' + view.__name__)
    dirs = (working_dir, temp_dir,)

    for d in dirs:
        if exists(d):
            rmtree(d)
        makedirs(d)

    return dirs


class ZincViewerAnnotator(ExposureFileAnnotatorBase):
    zope.interface.implements(IExposureFileAnnotator)
    for_interface = IZincViewerNote
    title = u'Zinc Viewer (Original)'
    label = u'Zinc Viewer'

    def generate(self):
        helper = RdfExposureNoteHelper()
        helper.parse(self.input)
        return helper.queryEFNote(self.__name__)

ZincViewerAnnotatorFactory = named_factory(ZincViewerAnnotator)


class JsonZincViewerAnnotator(ExposureFileAnnotatorBase):
    zope.interface.implements(IExposureFileAnnotator)
    for_interface = IJsonZincViewerNote
    title = u'Zinc Viewer (JSON)'
    label = u'Zinc Viewer'

    def generate(self):
        helper = RdfExposureNoteHelper()
        helper.parse(self.input)
        return helper.queryEFNote(self.__name__)

JsonZincViewerAnnotatorFactory = named_factory(JsonZincViewerAnnotator)


class FieldMLMetadataAnnotator(ExposureFileAnnotatorBase):
    zope.interface.implements(IExposureFileAnnotator)
    for_interface = IFieldMLMetadataNote
    title = u'FieldML Metadata'
    label = u'FieldML Metadata'

    def generate(self):
        helper = RdfExposureNoteHelper()
        helper.parse(self.input)
        result = helper.querySingleDC('')
        if not result:
            return ()

        # XXX not handling multiple results
        # take first element, strip off namespaces
        return tuple(result)

FieldMLMetadataAnnotatorFactory = named_factory(FieldMLMetadataAnnotator)


class ScaffoldDescriptionAnnotator(ExposureFileAnnotatorBase):
    zope.interface.implements(
        IExposureFileAnnotator, IExposureFilePostEditAnnotator)
    for_interface = IScaffoldDescriptionNote
    title = u'Scaffold'
    label = u'Scaffold Viewer'
    edited_names = ('view_json',)

    def generate(self):
        settings = zope.component.queryUtility(IPMR2GlobalSettings)
        root = settings.dirOf(self.context)
        scaffold_root = join(root, 'scaffold')
        if not isdir(root):
            makedirs(root)
        if exists(scaffold_root):
            rmtree(scaffold_root)

        # TODO ensure root is created, and scaffold_root is removed
        utility = zope.component.queryUtility(IZincJSUtility)
        utility(root, self.input)
        # call the utility
        return ()

ScaffoldDescriptionAnnotatorFactory = named_factory(ScaffoldDescriptionAnnotator)


class ScaffoldvuerAnnotator(ExposureFileAnnotatorBase):
    zope.interface.implements(IExposureFileAnnotator)
    for_interface = IScaffoldDescriptionNote
    title = u'Scaffoldvuer'
    label = u'Scaffoldvuer Renderer'

    def generate(self):
        settings = zope.component.queryUtility(IPMR2GlobalSettings)
        live, tmp = make_view_dirs(settings, self)

        helper = zope.component.queryAdapter(
            self.context, IExposureSourceAdapter)
        exposure, workspace, path = helper.source()
        storage = IStorage(exposure)

        utility = zope.component.queryUtility(ISparcConvertUtility)
        utility(live, tmp, storage, self.input)
        return ()

ScaffoldvuerAnnotatorFactory = named_factory(ScaffoldvuerAnnotator)


class ArgonSDSArchiveAnnotator(ExposureFileAnnotatorBase):
    zope.interface.implements(IExposureFileAnnotator)
    for_interface = IArgonSDSArchiveNote
    title = u'SPARC Dataset Archive (Argon) Annotator'
    label = u'SPARC Dataset Archive (Argon)'

    def generate(self):
        settings = zope.component.queryUtility(IPMR2GlobalSettings)
        root = settings.dirOf(self.context)
        live, tmp = make_view_dirs(settings, self)

        helper = zope.component.queryAdapter(
            self.context, IExposureSourceAdapter)
        exposure, workspace, path = helper.source()
        storage = IStorage(exposure)

        utility = zope.component.queryUtility(ISparcDatasetToolsUtility)
        utility(live, tmp, storage, self.input)
        return ()

ArgonSDSArchiveAnnotatorFactory = named_factory(ArgonSDSArchiveAnnotator)
