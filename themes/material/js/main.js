var airpress = airpress || {};


airpress.main = function() {
  angular.module('airpress', [])
      .config(['$interpolateProvider', function($interpolateProvider) {
         $interpolateProvider.startSymbol('[[').endSymbol(']]');
      }])
      .controller('FoldersController', airpress.ng.FoldersController)
      .controller('AdminsController', airpress.ng.AdminsController)
      .controller('ApprovalController', airpress.ng.ApprovalController)
      .controller('ApprovalsController', airpress.ng.ApprovalsController)
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


airpress.ng.ApprovalsController = function($scope) {
  this.$scope = $scope;
  this.searchApprovals();
};


airpress.ng.ApprovalsController.prototype.createApprovals = function(users) {
  airpress.rpc('admins.directly_add_users', {
    'users': users
  }).done(
      function(resp) {
    this.approvals = resp['approvals'].concat(this.approvals);
    this.$scope.$apply();
  }.bind(this));

};


airpress.ng.ApprovalsController.prototype.searchApprovals = function() {
  airpress.rpc('admins.search_approvals', {}).done(
      function(resp) {
    this.approvals = resp['approvals'] || [];
    this.$scope.$apply();
  }.bind(this));
};


airpress.ng.ApprovalsController.prototype.submit = function(emailsInput) {
  var users = [];
  emailsInput.split(',').forEach(function(email) {
    users.push({'email': email.trim()});
  });
  this.createApprovals(users);
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
    this.admins = resp['admins'].concat(this.admins);
    this.$scope.$apply();
  }.bind(this));
};


airpress.ng.AdminsController.prototype.searchAdmins = function() {
  airpress.rpc('admins.search_admins', {}).done(
      function(resp) {
    this.admins = resp['admins'] || [];
    this.$scope.$apply();
  }.bind(this));
};


airpress.ng.AdminsController.prototype.deleteAdmin = function(ident) {
  airpress.rpc('admins.delete_admins', {
    'admins': [{'ident': ident}]
  }).done(function(resp) {
    this.admins = this.admins.filter(function(item) {
      return item['ident'] != ident;
    });
    this.$scope.$apply();
  }.bind(this));
};


airpress.ng.FoldersController = function($scope) {
  this.$scope = $scope;
  this.searchFolders();
};


airpress.ng.FoldersController.prototype.searchFolders = function() {
  airpress.rpc('admins.search_folders', {}).done(
      function(resp) {
    this.folders = resp['folders'] || [];
    this.$scope.$apply();
  }.bind(this));
};


airpress.ng.ApprovalController = function($scope, $element) {
  this.$scope = $scope;
  var ident = $element[0].getAttribute('data-approval-ident');
  this.getApproval(ident);
};


airpress.ng.ApprovalController.prototype.getApproval = function(ident) {
  airpress.rpc('admins.get_approval', {
    'approval': {
      'ident': ident
    }
  }).done(
      function(resp) {
    this.approval = resp['approval'];
    this.$scope.$apply();
  }.bind(this));
};
