from . import admins
from . import approvals
from . import folders
from . import messages
from . import settings
from . import sync
from . import users
from protorpc import remote
import airlock


class AdminService(airlock.Service):

  @staticmethod
  def admin_verifier(email):
    return admins.Admin.is_admin

  @remote.method(messages.SettingsMessage,
                 messages.SettingsMessage)
  def get_settings(self, request):
    ent = settings.Settings.singleton()
    self.require_admin()
    resp = messages.SettingsMessage()
    resp.form = ent.form
    return resp

  @remote.method(messages.ApprovalRequest,
                 messages.ApprovalRequest)
  def get_approval(self, request):
    self.require_admin()
    ent = approvals.Approval.get_by_ident(request.approval.ident)
    resp = messages.ApprovalRequest()
    resp.approval = ent.to_message()
    return resp

  @remote.method(messages.ApprovalsMessage,
                 messages.ApprovalsMessage)
  def update_approvals(self, request):
    self.require_admin()
    ents = approvals.Approval.get_multi(request.approvals)
    for i, approval in enumerate(request.approvals):
      ents[i].update(approval, updated_by=self.me)
    resp = messages.ApprovalsMessage()
    resp.approvals = [ent.to_message() for ent in ents]
    return resp

  @remote.method(messages.ApprovalsMessage,
                 messages.ApprovalsMessage)
  def search_approvals(self, request):
    # self.require_admin()
    ents, next_cursor, has_more = approvals.Approval.search()
    resp = messages.ApprovalsMessage()
    resp.approvals = [ent.to_message() for ent in ents]
    return resp

  @remote.method(messages.ApprovalsMessage,
                 messages.ApprovalsMessage)
  def delete_approvals(self, request):
#    self.require_admin()
    ents = approvals.Approval.get_multi(request.approvals)
    approvals.Approval.delete_multi(request.approvals)
    resp = messages.ApprovalsMessage()
    resp.approvals = [ent.to_message() for ent in ents]
    return resp

  @remote.method(messages.AdminsMessage,
                 messages.AdminsMessage)
  def create_admins(self, request):
#    self.require_admin()
    ents = admins.Admin.create_multi(request.admins, created_by=self.me)
    resp = messages.AdminsMessage()
    resp.admins = [ent.to_message() for ent in ents]
    return resp

  @remote.method(messages.AdminsMessage,
                 messages.AdminsMessage)
  def delete_admins(self, request):
#    self.require_admin()
    ents = admins.Admin.get_multi(request.admins)
    admins.Admin.delete_multi(request.admins)
    resp = messages.AdminsMessage()
    resp.admins = [ent.to_message() for ent in ents]
    return resp

  @remote.method(messages.AdminsMessage,
                 messages.AdminsMessage)
  def search_admins(self, request):
#    self.require_admin()
    ents = admins.Admin.search()
    resp = messages.AdminsMessage()
    resp.admins = [ent.to_message() for ent in ents]
    return resp

  @remote.method(messages.UsersMessage,
                 messages.ApprovalsMessage)
  def directly_add_users(self, request):
    emails = [user.email for user in request.users]
    approval_ents = users.User.direct_add_users(emails, created_by=self.me)
    resp = messages.ApprovalsMessage()
    resp.approvals = [ent.to_message() for ent in approval_ents]
    return resp

  @remote.method(messages.FoldersMessage,
                 messages.FoldersMessage)
  def update_folders(self, request):
    ents = folders.Folder.get_multi(request.folders)
    for i, folder in enumerate(request.folders):
      ents[i].update(folder, updated_by=self.me)
    resp = messages.FoldersMessage()
    resp.approvals = [ent.to_message() for ent in ents]
    return resp

  @remote.method(messages.FoldersMessage,
                 messages.FoldersMessage)
  def search_folders(self, request):
#    self.require_admin()
    ents = folders.Folder.search()
    resp = messages.FoldersMessage()
    resp.folders = [ent.to_message() for ent in ents]
    return resp

  @remote.method(messages.SyncMessage,
                 messages.SyncMessage)
  def sync(self, request):
    resp = messages.SyncMessage()
    for resource in request.resources:
      resource_id = resource.resource_id
      token = sync.download_resource(
          resource_id, self.me, create_channel=True)
      resp.token = token
    return resp
