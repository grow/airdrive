from . import folders
from . import sync
from . import testing


class SyncTestCase(testing.TestCase):

  def test_download_folder(self):
    resource_id = '0BzZ9lY-SjtYab1ZrY2Y0d085dkU'
    resp = sync.download_resource(resource_id)
    folder = folders.Folder.get(resource_id)
    children = folder.list_children()
    raise Exception(children)
