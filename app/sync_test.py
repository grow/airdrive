from . import testing
from . import sync


class SyncTestCase(testing.TestCase):

  def test_download_folder(self):
    resource_id = '0BzZ9lY-SjtYab1ZrY2Y0d085dkU'
    resp = sync.download_resource(resource_id)
