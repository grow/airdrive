from . import admins
from . import approvals
from . import messages
from . import settings
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
  def delete_approvals(self, request):
    self.require_admin()
    ents = approvals.Approval.get_multi(request.approvals)
    approvals.Approval.delete_multi(request.approvals)
    resp = messages.ApprovalsMessage()
    resp.approvals = [ent.to_message() for ent in ents]
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

  @remote.method(messages.UsersMessage,
                 messages.ApprovalsMessage)
  def directly_add_users(self, request):
    emails = [user.email for user in request.users]
    approval_ents = users.User.directly_create_approvals(emails)
    resp = messages.ApprovalsMessage()
    resp.approvals = [ent.to_message() for ent in approval_ents]
    return resp
