var airpress = airpress || {};


airpress.main = function() {
  angular.module('airpress', [])
      .config(['$interpolateProvider', function($interpolateProvider) {
         $interpolateProvider.startSymbol('[[').endSymbol(']]');
      }])
      .controller('AdminsController', airpress.ng.AdminsController)
      .controller('SettingsController', airpress.ng.SettingsController)

  angular.bootstrap(document, ['airpress'])
};


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


airpress.ng = airpress.ng || {};


airpress.ng.DirectAddUsersController = function() {

};


airpress.ng.DirectAddUsersController.prototype.submit = function(emailsInput) {
  var emails = [];
  emailsInput.split(',').forEach(function(email) {
    emails.push(email.trim());
  });
  airpress.rpc('admins.direct_add_users', {
  });
};


airpress.ng.SettingsController = function() {
  airpress.rpc('admins.get_settings').done(function(resp) {
    console.log(resp);
  });
};


airpress.ng.AdminsController = function($scope) {
  this.$scope = $scope;
  this.searchAdmins();
};


airpress.ng.AdminsController.prototype.createAdmin = function(email) {
  airpress.rpc('admins.create_admins', {
    'admins': [{'email': email}]
  }).done(function(resp) {
    this.admins = resp['admins'];
    this.$scope.$apply();
  }.bind(this));
};


airpress.ng.AdminsController.prototype.searchAdmins = function() {
  airpress.rpc('admins.search_admins', {}).done(
      function(resp) {
    this.admins = resp['admins'];
    this.$scope.$apply();
  }.bind(this));
};


airpress.ng.AdminsController.prototype.deleteAdmin = function(ident) {
  airpress.rpc('admins.delete_admins', {
    'admins': [{'ident': ident}]
  });
};
