from plone.app.testing import PloneSandboxLayer
from plone.app.testing import IntegrationTesting
from plone.testing import z2

from pmr2.app.exposure.tests import layer


class FieldMLUtilityLayer(PloneSandboxLayer):

    defaultBases = (layer.EXPOSURE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        import fieldml.pmr2
        self.loadZCML(package=fieldml.pmr2)
        # z2.installProduct(app, 'fieldml.pmr2')

    def setUpPloneSite(self, portal):
        """
        Apply the default fieldml.pmr2 profile and ensure that the
        settings have the tmpdir applied in.
        """

        # install fieldml.pmr2
        self.applyProfile(portal, 'fieldml.pmr2:default')

    def tearDownZope(self, app):
        z2.uninstallProduct(app, 'fieldml.pmr2')


FIELDML_UTILITY_FIXTURE = FieldMLUtilityLayer()

FIELDML_UTILITY_INTEGRATION_LAYER = IntegrationTesting(
    bases=(FIELDML_UTILITY_FIXTURE,), name="fieldml.pmr2:integration")
