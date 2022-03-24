from pmr2.app.annotation import note_factory as factory
from note import *

ZincViewerNoteFactory = factory(ZincViewerNote, 'zinc_viewer')
JsonZincViewerNoteFactory = factory(JsonZincViewerNote, 'json_zinc_viewer')
FieldMLMetadataNoteFactory = factory(FieldMLMetadataNote, 'fieldml_metadata')
ScaffoldDescriptionNoteFactory = factory(ScaffoldDescriptionNote, 'scaffold_viewer')
ScaffoldvuerNoteFactory = factory(ScaffoldvuerNote, 'scaffoldvuer')
ArgonSDSArchiveNoteFactory = factory(ArgonSDSArchiveNote, 'argon_sds_archive')
