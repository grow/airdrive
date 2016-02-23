var airpress = airpress || {};


airpress.updateApprovalStatus = function(ident, approvalStatus) {
  var approvals = [];
  airpress.rpc('admins.update_approvals', {
    'approvals': approvals
  });
};


airpress.rpc = function(method, data) {
  return $.ajax({
      url: '/_api/' + method,
      type: 'POST',
      data: JSON.stringify(data),
      contentType: 'application/json'
  });
};


airpress.deleteAdmin = function(ident) {
  airpress.rpc('admins.delete_admins', {
    'admins': [{'ident': ident}]
  });
};


airpress.ng.DirectAddUsersController = function() {

};


airpress.ng.DirectAddUsersController.prototype.submit = function(emailsInput) {
  var emails = [];
  emailsInput.split(',').forEach(function(email) {
    emails.push(email.trim());
  });
  airpress.rpc('admins.direct_add_users', {
      'users': [
          {'email':

  });
};
