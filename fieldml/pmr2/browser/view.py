from os.path import isfile
from os.path import commonprefix
from os.path import join
from os.path import realpath
from json import dumps
import zope.component
from zope.publisher.interfaces import NotFound
from zope.browserpage.viewpagetemplatefile import ViewPageTemplateFile

from Acquisition import aq_inner

from pmr2.app.settings.interfaces import IPMR2GlobalSettings
from pmr2.app.exposure.interfaces import IExposureSourceAdapter
from pmr2.app.exposure.browser.browser import ExposureFileViewBase


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


class FieldMLMetadata(ExposureFileViewBase):
    """\
    Wraps an object around the Zinc viewer.
    """

    template = ViewPageTemplateFile('fieldml_metadata.pt')


class ScaffoldViewer(ExposureFileViewBase):
    """
    The scaffold viewer
    """

    index = ViewPageTemplateFile('zincjs_scaffold_viewer.pt')
    default_view_json = dumps({
        "farPlane": 6.356104522334282,
        "nearPlane": 0.1333,
        "upVector": [
            0.6389172435557343, 0.2829491995105483, 0.7153492198803961
        ],
        "targetPosition": [
            0.05471361591632292, 0.12015277677143191, -0.39547867728129676
        ],
        "eyePosition": [
            -1.8366826545742034, -0.8914857814544176, 0.9499518864185601
        ]
    })

    def render(self):
        if not self.traverse_subpath:
            return super(ScaffoldViewer, self).render()

        if self.traverse_subpath == ['view.json']:
            if not self.note.view_json:
                return self.default_view_json
            # manually redirect
            helper = zope.component.queryAdapter(
                self.context, IExposureSourceAdapter)
            exposure, workspace, path = helper.source()
            target_uri = '%s/@@rawfile/%s/%s' % (
                workspace.absolute_url(),
                exposure.commit_id, self.note.view_json)
            return self.request.response.redirect(target_uri)

        settings = zope.component.getUtility(IPMR2GlobalSettings)
        root = realpath(settings.dirOf(self.context))
        target = realpath(join(root, *self.traverse_subpath))
        if commonprefix([root, target]) != root:
            raise NotFound(self.context, self.context.title_or_id())
        if not isfile(target):
            raise NotFound(self.context, self.context.title_or_id())
        with open(target) as fd:
            return fd.read()


class ScaffoldvuerView(ExposureFileViewBase):
    """
    The scaffoldvuer view
    """

    index = ViewPageTemplateFile('scaffoldvuer.pt')

    def render(self):
        if not self.traverse_subpath:
            return super(ScaffoldvuerView, self).render()

        settings = zope.component.getUtility(IPMR2GlobalSettings)
        root = join(realpath(settings.dirOf(self.context)), self.__name__)
        target = realpath(join(root, *self.traverse_subpath))
        if commonprefix([root, target]) != root:
            raise NotFound(self.context, self.context.title_or_id())
        if not isfile(target):
            raise NotFound(self.context, self.context.title_or_id())
        with open(target) as fd:
            return fd.read()
