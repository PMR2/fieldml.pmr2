import zope.interface
from zope.schema import fieldproperty

from pmr2.app.interfaces import *
from pmr2.app.annotation.note import ExposureFileNoteBase
from pmr2.app.annotation.note import ExposureFileEditableNoteBase

from interfaces import *


class ZincViewerNote(ExposureFileNoteBase):
    """\
    Zinc viewer note
    """

    zope.interface.implements(IZincViewerNote)
    exnode = fieldproperty.FieldProperty(IZincViewerNote['exnode'])
    exelem = fieldproperty.FieldProperty(IZincViewerNote['exelem'])


class JsonZincViewerNote(ExposureFileNoteBase):
    """\
    Zinx viewer note.  No data here because this attaches to the json
    file, which contains all the required data.
    """

    zope.interface.implements(IJsonZincViewerNote)
    json = fieldproperty.FieldProperty(IJsonZincViewerNote['json'])


class FieldMLMetadataNote(ExposureFileNoteBase):
    """\
    FieldML metadata note
    """

    zope.interface.implements(IFieldMLMetadataNote)
    title = fieldproperty.FieldProperty(IFieldMLMetadataNote['title'])
    creator = fieldproperty.FieldProperty(IFieldMLMetadataNote['creator'])
    description = fieldproperty.FieldProperty(IFieldMLMetadataNote['description'])


class ScaffoldDescriptionNote(ExposureFileEditableNoteBase):
    """
    Scaffold Description note.
    """

    zope.interface.implements(IScaffoldDescriptionNote)
    view_json = fieldproperty.FieldProperty(IScaffoldDescriptionNote['view_json'])


class ScaffoldvuerNote(ExposureFileNoteBase):
    """
    Scaffoldvuer note.
    """

    zope.interface.implements(IScaffoldvuerNote)


class ArgonSDSArchiveNote(ExposureFileNoteBase):
    """
    Scaffoldvuer note.
    """

    zope.interface.implements(IArgonSDSArchiveNote)
