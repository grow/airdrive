from google.appengine.api import mail
from . import admins
import appengine_config
import jinja2
import os
import premailer

CONFIG = appengine_config.CONFIG
_path = os.path.join(os.path.dirname(__file__), 'templates')
_loader = jinja2.FileSystemLoader(_path)
_env = jinja2.Environment(loader=_loader, autoescape=True, trim_blocks=True)


class Emailer(object):

  def __init__(self, approval):
    self.approval = approval

  def send_rejected_to_user(self):
    template_path = 'email_rejected_to_user.html'
    subject = '[{}] Your access request has been rejected'.format(CONFIG['title'])
    to = self.approval.user.email
    self.send(to, subject, template_path)

  def send_approved_to_user(self):
    template_path = 'email_approved_to_user.html'
    subject = '[{}] Your access request has been approved'.format(CONFIG['title'])
    to = self.approval.user.email
    self.send(to, subject, template_path)

  def send_created_to_user(self):
    template_path = 'email_created_to_user.html'
    subject = '[{}] We have received your access request'.format(CONFIG['title'])
    to = self.approval.user.email
    self.send(to, subject, template_path)

  def send_created_to_admins(self):
    template_path = 'email_created_to_admins.html'
    subject = '[{}] Access request from {}'.format(CONFIG['title'], self.approval.user.email)
    to = admins.Admin.list_emails()
    if to:
      self.send(to, subject, template_path)

  def send(self, to, subject, template_path):
    html = self._render(template_path)
    self._send(subject, to, html)

  def _render(self, template_path):
    template = _env.get_template(template_path)
    html = template.render({
        'config': appengine_config,
        'approval': self.approval,
    })
    return premailer.transform(html)

  def _send(self, subject, to, html):
    sender = appengine_config.EMAIL_SENDER
    message = mail.EmailMessage(sender=sender, subject=subject)
    message.to = to
    message.html = html
    message.send()
