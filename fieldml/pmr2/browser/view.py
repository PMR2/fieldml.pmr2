import zope.component
from zope.publisher.browser import BrowserPage
from zope.browserpage.viewpagetemplatefile import ViewPageTemplateFile

from Acquisition import aq_inner

from pmr2.app.workspace.interfaces import IStorage
from pmr2.app.exposure.interfaces import IExposureSourceAdapter
from pmr2.app.exposure.browser.browser import ExposureFileViewBase

from pmr2.opencmiss.api import to_threejs


class BaseZincViewer(ExposureFileViewBase):
    """\
    Base Zinc Viewer to provide a private helper to assist resolving
    full path of files.
    """

    @property
    def js_root(self):
        """
        Return the root of the js library for fieldml.pmr2
        """

        context = aq_inner(self.context)
        portal_state = zope.component.getMultiAdapter((context, self.request),
            name=u'plone_portal_state')
        portal_url = portal_state.portal_url()
        return '/'.join((portal_url, '++resource++fieldml.pmr2.js'))

    def _getPath(self, filename):
        uri = self.context.absolute_url()
        # take the "dirname" of the context and apply the path in place.
        path, id_ = uri.rsplit('/', 1)
        return '/'.join([path, filename])


class ZincViewer(BaseZincViewer):
    """\
    Wraps an object around the Zinc viewer.
    """

    index = ViewPageTemplateFile('zinc_content.pt')

    @property
    def exnode(self):
        return self._getPath(self.note.exnode)

    @property
    def exelem(self):
        return self._getPath(self.note.exelem)


class JsonZincViewer(BaseZincViewer):
    """\
    Wraps an object around the JSON Zinc viewer.
    """

    index = ViewPageTemplateFile('json_zinc_content.pt')

    @property
    def json(self):
        return self._getPath(self.note.json)


class ThreeJSViewer(BaseZincViewer):
    """
    threejs viewer class.
    """

    index = ViewPageTemplateFile('threejs_viewer.pt')

    def src(self):
        return '/'.join((self.context.absolute_url(), self.__name__,
            'threejs'))

    def render(self):
        if self.url_subpath == 'threejs':
            # XXX temporary, normally we have pre-generated data here
            # but we can't due to possible storage requirements so we
            # will have dedicated endpoints/servers for this which will
            # need to be determined on exact implementation.  Proof of
            # concept at this stage so this dummy endpoint will be
            # removed.
            esa = zope.component.getAdapter(self.context,
                IExposureSourceAdapter)
            e, workspace, n = esa.source()
            storage = zope.component.getAdapter(workspace, IStorage)
            # assume this is valid.
            graphics_description = storage.file('graphics_descriptions')
            region_data = esa.file()
            return to_threejs(region_data, graphics_description)
        return super(ThreeJSViewer, self).render()


class FieldMLMetadata(BrowserPage):
    """\
    Wraps an object around the Zinc viewer.
    """

    template = ViewPageTemplateFile('fieldml_metadata.pt')
