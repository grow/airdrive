from google.appengine.api import mail
from . import admins
from . import settings
import appengine_config
import jinja2
import os
import premailer
import webapp2

CONFIG = appengine_config.CONFIG
SETTINGS = settings.Settings.singleton()


class Emailer(object):

  def __init__(self, approval):
    self.approval = approval
    self.title = SETTINGS.title

  def send_rejected_to_user(self):
    template_path = 'email_rejected_to_user.html'
    subject = '[{}] Your access request has been rejected'.format(self.title)
    to = self.approval.user.email
    self.send(to, subject, template_path)

  def send_approved_to_user(self):
    template_path = 'email_approved_to_user.html'
    subject = '[{}] Your access request has been approved'.format(self.title)
    to = self.approval.user.email
    self.send(to, subject, template_path)

  def send_created_to_user(self):
    template_path = 'email_created_to_user.html'
    subject = '[{}] We have received your access request'.format(self.title)
    to = self.approval.user.email
    self.send(to, subject, template_path)

  def send_created_to_admins(self):
    template_path = 'email_created_to_admins.html'
    subject = '[{}] Access request from {}'.format(self.title, self.approval.user.email)
    to = admins.Admin.list_emails()
    if to:
      self.send(to, subject, template_path)

  def send(self, to, subject, template_path):
    html = self._render(template_path)
    self._send(subject, to, html)

  def _render(self, template_path):
    settings_obj = settings.Settings.singleton()
    template = self.env.get_template(template_path)
    html = template.render({
        'config': appengine_config,
        'settings': settings_obj,
        'approval': self.approval,
    })
    return premailer.transform(html)

  def _send(self, subject, to, html):
    sender = appengine_config.EMAIL_SENDER
    message = mail.EmailMessage(sender=sender, subject=subject)
    message.to = to
    message.html = html
    message.send()

  @webapp2.cached_property
  def env(self):
    here = os.path.dirname(__file__)
    path = os.path.join(os.path.dirname(__file__), 'templates')
    theme_path = os.path.join(here, '..', 'themes', SETTINGS.get_theme(), 'emails')
    loader = jinja2.FileSystemLoader([
        theme_path,
        path,
    ])
    return jinja2.Environment(loader=loader, autoescape=True, trim_blocks=True)
