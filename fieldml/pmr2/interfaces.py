import zope.interface
import zope.schema

from pmr2.app.workspace.schema import StorageFileChoice


class ISettings(zope.interface.Interface):
    """
    Settings to be registered to the configuration registry.
    """

    zincjs_group_exporter = zope.schema.TextLine(
        title=u'ZincJS Group Exporter Location',
        description=u'The path to the exporter binary.',
        default=u'zincjs_group_exporter',
        required=False,
    )

    sparc_convert = zope.schema.TextLine(
        title=u'Sparc Convert location',
        description=u'The path to the sparc-convert binary.',
        default=u'sparc-convert',
        required=False,
    )

    create_scaffold_dataset = zope.schema.TextLine(
        title=u'Sparc Create Scaffold Dataset location',
        description=u'The path to the create-scaffold-dataset binary.',
        default=u'create-scaffold-dataset',
        required=False,
    )


class IZincJSUtility(zope.interface.Interface):
    """
    The marker interface for the ZincJS utility.
    """


class ISparcConvertUtility(zope.interface.Interface):
    """
    The marker interface for the sparc-convert cli wrapper utility.
    """


class ISparcDatasetToolsUtility(zope.interface.Interface):
    """
    Marker interface for sparc-dataset-tools cli wrapper utility.
    """


class IZincViewerNote(zope.interface.Interface):
    """\
    Zinc Viewer note.
    """

    exnode = zope.schema.TextLine(
        title=u'Exnode file',
        description=u'The exnode file for this model.',
    )

    exelem = zope.schema.TextLine(
        title=u'Exelem file',
        description=u'The exelem file for this model.',
    )


class IJsonZincViewerNote(zope.interface.Interface):
    """\
    Zinx JSON viewer note.
    """

    json = zope.schema.TextLine(
        title=u'Json file',
        description=u'The json file that will initiate the viewer for '
                     'this model.',
    )


class IFieldMLMetadataNote(zope.interface.Interface):
    """\
    FieldML Metadata note.
    """

    title = zope.schema.TextLine(
        title=u'Title',
        description=u'Title of the model.',
    )

    creator = zope.schema.TextLine(
        title=u'Creator',
        description=u'Creator of the model.',
        required=False,
    )

    citation = zope.schema.TextLine(
        title=u'Citation',
        description=u'The citation source of this work.',
        required=False,
    )

    ispartof = zope.schema.TextLine(
        title=u'Citation Identifier',
        description=u'Identifier of the citation.',
        required=False,
    )

    description = zope.schema.TextLine(
        title=u'Description',
        description=u'Description of the model.',
        required=False,
    )


class IScaffoldDescriptionNote(zope.interface.Interface):
    """
    Scaffold description note.
    """

    view_json = StorageFileChoice(
        title=u'Viewer JSON description',
        description=u'The JSON file that contain the viewport description; '
                     'a default configuration will be provided if omitted.',
        vocabulary='pmr2.vocab.manifest',
        required=False,
    )


class IScaffoldvuerNote(zope.interface.Interface):
    """
    Scaffoldvuer note.
    """


class IArgonSDSArchiveNote(zope.interface.Interface):
    """
    Argon SDS Archive note.
    """
