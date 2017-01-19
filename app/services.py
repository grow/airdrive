import appengine_config
from . import admins
from . import approvals
from . import assets
from . import folders
from . import index
from . import messages
from . import settings
from . import sync
from . import users
from protorpc import remote
import airlock
import json
from google.appengine.ext import ndb


class AssetService(airlock.Service):

  @remote.method(messages.SearchRequest,
                 messages.SearchResponse)
  def search(self, request):
    results = index.do_search(request.query)
    resp = messages.SearchResponse()
    return resp

  @remote.method(messages.GetAssetGroupRequest,
                 messages.GetAssetGroupResponse)
  def get_group(self, request):
    parent_key = ndb.Key('Folder', request.parent_key)
    folder_message, asset_messages = assets.Asset.get_group(parent_key=parent_key)
    resp = messages.GetAssetGroupResponse()
    resp.folder = folder_message
    resp.assets = asset_messages
    return resp


class AdminService(airlock.Service):

  @staticmethod
  def admin_verifier(email):
    return admins.Admin.is_admin

  @remote.method(messages.SettingsMessage,
                 messages.SettingsMessage)
  def get_settings(self, request):
    ent = settings.Settings.singleton()
    self.require_admin()
    resp = ent.get_form()
    return resp

  @remote.method(messages.SettingsMessage,
                 messages.SettingsMessage)
  def update_settings(self, request):
    ent = settings.Settings.singleton()
    self.require_admin()
    ent.update(request)
    resp = ent.form
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
  def approve_approvals(self, request):
    self.require_admin()
    ents = approvals.Approval.approve_multi(
        request.approvals, updated_by=self.me,
        send_email=request.send_email)
    resp = messages.ApprovalsMessage()
    resp.approvals = [ent.to_message() for ent in ents]
    return resp

  @remote.method(messages.ApprovalsMessage,
                 messages.ApprovalsMessage)
  def reject_approvals(self, request):
    self.require_admin()
    ents = approvals.Approval.reject_multi(
        request.approvals, updated_by=self.me,
        send_email=request.send_email)
    resp = messages.ApprovalsMessage()
    resp.approvals = [ent.to_message() for ent in ents]
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

  @remote.method(messages.ApprovalsQueryMessage,
                 messages.ApprovalsMessage)
  def search_approvals(self, request):
    self.require_admin()
    ents, next_cursor, has_more = approvals.Approval.search(
        cursor=request.cursor, email=request.email)
    count = approvals.Approval.count()
    resp = messages.ApprovalsMessage()
    resp.approvals = [ent.to_message() for ent in ents]
    resp.has_more = has_more
    resp.cursor = next_cursor.urlsafe() if next_cursor else None
    resp.count = count
    return resp

  @remote.method(messages.ApprovalsMessage,
                 messages.ApprovalsMessage)
  def delete_approvals(self, request):
    self.require_admin()
    ents = approvals.Approval.get_multi(request.approvals)
    approvals.Approval.delete_multi(request.approvals)
    resp = messages.ApprovalsMessage()
    resp.approvals = [ent.to_message() for ent in ents]
    return resp

  @remote.method(messages.AdminsMessage,
                 messages.AdminsMessage)
  def create_admins(self, request):
    self.require_admin()
    ents = admins.Admin.create_multi(request.admins, created_by=self.me)
    resp = messages.AdminsMessage()
    resp.admins = [ent.to_message() for ent in ents]
    return resp

  @remote.method(messages.AdminsMessage,
                 messages.AdminsMessage)
  def update_admins(self, request):
    self.require_admin()
    ents = admins.Admin.update_multi(request.admins)
    resp = messages.AdminsMessage()
    resp.admins = [ent.to_message() for ent in ents]
    return resp

  @remote.method(messages.AdminsMessage,
                 messages.AdminsMessage)
  def delete_admins(self, request):
    self.require_admin()
    ents = admins.Admin.get_multi(request.admins)
    admins.Admin.delete_multi(request.admins)
    resp = messages.AdminsMessage()
    resp.admins = [ent.to_message() for ent in ents]
    return resp

  @remote.method(messages.AdminsMessage,
                 messages.AdminsMessage)
  def search_admins(self, request):
    self.require_admin()
    ents = admins.Admin.search()
    resp = messages.AdminsMessage()
    resp.admins = [ent.to_message() for ent in ents]
    return resp

  @remote.method(messages.DirectlyAddUsersMessage,
                 messages.ApprovalsMessage)
  def directly_add_users(self, request):
    self.require_admin()
    emails = [users.User.parse_email(user.email)
              for user in request.users]
    send_email = request.send_email
    form = request.form
    if request.add:
        approval_ents = users.User.add_access(emails, created_by=self.me, form=form)
    elif request.remove:
        approval_ents = users.User.remove_access(emails, created_by=self.me, form=form)
    else:
        approval_ents = users.User.direct_add_users(
            emails, created_by=self.me, send_email=send_email, form=form)
    resp = messages.ApprovalsMessage()
    resp.approvals = [ent.to_message() for ent in approval_ents]
    return resp

  @remote.method(messages.FoldersMessage,
                 messages.FoldersMessage)
  def delete_folders(self, request):
    self.require_admin()
    ents = folders.Folder.get_multi(request.folders)
    folders.Folder.delete_multi(ents)
    resp = messages.FoldersMessage()
    return resp

  @remote.method(messages.FoldersMessage,
                 messages.FoldersMessage)
  def update_folders(self, request):
    self.require_admin()
    ents = folders.Folder.get_multi(request.folders)
    for i, folder in enumerate(request.folders):
      ents[i].update(folder, updated_by=self.me)
    resp = messages.FoldersMessage()
    resp.approvals = [ent.to_message() for ent in ents]
    return resp

  @remote.method(messages.FoldersMessage,
                 messages.FoldersMessage)
  def search_folders(self, request):
    self.require_admin()
    ents = folders.Folder.search()
    resp = messages.FoldersMessage()
    resp.folders = [ent.to_message() for ent in ents]
    return resp

  @remote.method(messages.SyncMessage,
                 messages.SyncMessage)
  def sync(self, request):
    self.require_admin()
    resp = messages.SyncMessage()
    for resource in request.resources:
      resource_id = resource.resource_id
      token = sync.download_resource(
          resource_id, self.me, create_channel=True)
      resp.token = token
    return resp

  @remote.method(messages.SyncMessage,
                 messages.SyncMessage)
  def sync_all(self, request):
    self.require_admin()
    resp = messages.SyncMessage()
    root_folder_id = sync.get_root_folder_id()
    token = sync.download_resource(root_folder_id, self.me)
    resp.token = token
    return resp

  @remote.method(messages.ImportApprovalsMessage,
                 messages.ApprovalsMessage)
  def import_approvals(self, request):
    self.require_admin()
    send_email = False
    ents = users.User.import_from_google_sheets(
        sheet_id=request.sheet_id, gid=request.sheet_gid,
        form=request.form, created_by=self.me,
        send_email=send_email)
    resp = messages.ApprovalsMessage()
    resp.approvals = [approval.to_message() for approval in ents]
    return resp

  @remote.method(messages.GetSyncTreeRequest,
                 messages.GetSyncTreeResponse)
  def get_sync_tree(self, request):
    self.require_admin()
    sync_tree = folders.Folder.get_sync_tree()
    resp = messages.GetSyncTreeResponse()
    resp.sync_tree = json.dumps(sync_tree)
    return resp
