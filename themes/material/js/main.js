var airpress = airpress || {};


airpress.main = function() {
  angular.module('airpress', [])
      .config(['$interpolateProvider', function($interpolateProvider) {
         $interpolateProvider.startSymbol('[[').endSymbol(']]');
      }])
      .controller('FoldersController', airpress.ng.FoldersController)
      .controller('DownloadBarController', airpress.ng.DownloadBarController)
      .controller('AdminsController', airpress.ng.AdminsController)
      .controller('ApprovalController', airpress.ng.ApprovalController)
      .controller('ApprovalsController', airpress.ng.ApprovalsController)
      .controller('SettingsController', airpress.ng.SettingsController)
      .controller('SyncController', airpress.ng.SyncController)

  angular.bootstrap(document, ['airpress'])
  smoothScroll.init({offset: 40});
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


airpress.ng.ApprovalsController.prototype.createApprovals =
    function(users, sendEmail) {
  airpress.rpc('admins.directly_add_users', {
    'users': users,
    'send_email': sendEmail
  }).done(
      function(resp) {
    var approvalsToSet = resp['approvals'];
    this.approvals.forEach(function(approval) {
      var addApproval = true;
      approvalsToSet.forEach(function(approvalToSet) {
        if (approval['ident'] == approvalToSet['ident']) {
          addApproval = false;
        }
      });
      if (addApproval) {
        approvalsToSet.push(approval);
      }
    });
    this.approvals = approvalsToSet;
    this.$scope.$apply();
  }.bind(this));

};


airpress.ng.ApprovalsController.prototype.updateSelected =
    function(approve, sendEmail) {
  var approvals = [];
  this.approvals.forEach(function(approval) {
    if (approval.selected) {
      approvals.push(approval);
    }
  });
  var method = approve ? 'admins.approve_approvals' : 'admins.reject_approvals';
  airpress.rpc(method, {
    'approvals': approvals,
    'send_email': sendEmail
  }).done(
      function(resp) {
    this.approvals.forEach(function(approval, i) {
      resp['approvals'].forEach(function(updatedApproval) {
        if (approval['ident'] == updatedApproval['ident']) {
          updatedApproval.selected = true;
          this.approvals[i] = updatedApproval;
        }
      }.bind(this));
    }.bind(this));
    this.$scope.$apply();
  }.bind(this));
};


airpress.ng.ApprovalsController.prototype.deleteApproval = function(ident) {
  var approvals = [{
    'ident': ident
  }];
  airpress.rpc('admins.delete_approvals', {
    'approvals': approvals
  }).done(
      function(resp) {
    this.approvals = this.approvals.filter(function(item) {
      return item['ident'] != ident;
    });
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


airpress.ng.ApprovalsController.prototype.submit =
    function(emailsInput, sendEmail) {
  var users = [];
  emailsInput.split(',').forEach(function(email) {
    users.push({'email': email.trim()});
  });
  this.createApprovals(users, sendEmail);
};


airpress.ng.SettingsController = function($scope) {
  this.$scope = $scope;
  airpress.rpc('admins.get_settings').done(function(resp) {
    this.settings = resp;
    this.$scope.$apply();
  }.bind(this));
};


airpress.ng.SettingsController.prototype.updateSettings = function(form) {
  airpress.rpc('admins.update_settings', form).done(function(resp) {
    this.settings = resp;
    this.$scope.$apply();
  }.bind(this));
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


airpress.ng.AdminsController.prototype.updateAdmin = function(admin) {
  airpress.rpc('admins.update_admins', {
    'admins': [admin]
  }).done(function(resp) {
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


airpress.ng.FoldersController.prototype.deleteFolder = function(folder) {
  this.addToLog('Deleting...');
  airpress.rpc('admins.delete_folders', {
    'folders': [folder]
  }).done(function() {
    this.addToLog('Deleted: ' + folder.title);
  }.bind(this));
};


airpress.ng.FoldersController.prototype.sync = function(resourceId) {
  this.addToLog('Syncing...');
  airpress.rpc('admins.sync', {
    'resources': [{'resource_id': resourceId}]
  }).done(function(resp) {
    this.updateChannel(resp['token']);
  }.bind(this));
};


airpress.ng.FoldersController.prototype.syncAll = function() {
  this.addToLog('Syncing...');
  airpress.rpc('admins.sync_all', {}).done(function(resp) {
    this.updateChannel(resp['token']);
  }.bind(this));
};


airpress.ng.FoldersController.prototype.addToLog = function(message) {
  var logEl = document.getElementById('sync-log');
  if (logEl.textContent) {
    logEl.appendChild(document.createElement('br'));
  }
  logEl.appendChild(document.createTextNode(message));
};


airpress.ng.FoldersController.prototype.updateChannel = function(token) {
  var channel = new goog.appengine.Channel(token);
  socket = channel.open();
  socket.onmessage = function(message) {
    if (message['data']) {
      var data = message['data'];
      data = JSON.parse(data);
      this.addToLog(data['message']);
    }
  }.bind(this);
  return socket;
};


airpress.ng.ApprovalController = function($scope, $element) {
  this.$scope = $scope;
  this.folderChoices = {};
  var ident = $element[0].getAttribute('data-approval-ident');
  this.getApproval(ident);
};


airpress.ng.ApprovalController.prototype.updateStatus =
    function(approve, sendEmail) {
  var method = approve ? 'admins.approve_approvals' : 'admins.reject_approvals';
  airpress.rpc(method, {
    'approvals': [this.approval],
    'send_email': sendEmail
  }).done(
      function(resp) {
    this.getApproval(this.approval['ident']);
  }.bind(this));
};


airpress.ng.ApprovalController.prototype.update =
    function(approval, formChoices) {
  var folders = [];
  for (var choice in formChoices) {
    if (formChoices[choice]) {
      folders.push(choice);
    }
  }
  approval.form.folders = folders;
  airpress.rpc('admins.update_approvals', {
    'approvals': [approval]
  });
};


airpress.ng.ApprovalController.prototype.getApproval = function(ident) {
  airpress.rpc('admins.get_approval', {
    'approval': {
      'ident': ident
    }
  }).done(
      function(resp) {
    if (resp['approval']['form']['folders']) {
      resp['approval']['form']['folders'].forEach(function(folderId) {
        this.folderChoices[folderId] = true;
      }.bind(this));
    }
    this.approval = resp['approval'];
    this.$scope.$apply();
  }.bind(this));
};


airpress.ng.SyncController = function($scope) {
  this.success = false;
  this.error = false;
  this.loading = false;
  this.$scope = $scope;
};


airpress.ng.SyncController.prototype.sync = function(resourceId) {
  this.loading = true;
  this.success = false;
  this.error = false;
  airpress.sync.sync(resourceId).done(function(resp) {
    this.loading = false;
    this.success = true;
    this.$scope.$apply();
  }.bind(this)).fail(function(resp) {
    this.error = true;
    this.loading = false;
    this.success = false;
    this.$scope.$apply();
  }.bind(this));
};


airpress.ng.DownloadBarController = function($scope, $element) {
  this.el_ = $element[0];
  this.$scope = $scope;
  this.visible = false;
  this.asset = {};
  this.updateForm_([]);
  this.assets = {};

  var buttonEls = document.querySelectorAll('[data-asset-title]');
  [].forEach.call(buttonEls, function(buttonEl) {
    var assetTitle = buttonEl.getAttribute('data-asset-title');
    buttonEl.addEventListener('click', function() {
      this.setVisible(!this.visible, assetTitle);
      this.$scope.$apply();
    }.bind(this));
  }.bind(this));
};


airpress.ng.DownloadBarController.prototype.setVisible = function(visible, assetTitle) {
  this.visible = visible;
  if (!visible) {
    return;
  }
  this.asset.title = assetTitle;
  this.updateAsset_(assetTitle);
};


airpress.ng.DownloadBarController.prototype.updateAsset_ = function(title) {
  airpress.rpc('assets.get_group', {
    'title': title
  }).done(
      function(resp) {
    this.asset.title = title;
    this.updateForm_(resp['assets']);
    this.$scope.$apply();
  }.bind(this));
};


airpress.ng.DownloadBarController.prototype.updateForm_ = function(assets) {
  this.assets = assets;
  this.form = {
    format: [],
    messaging: [],
    region: [],
  };
  this.assets.forEach(function(asset) {
    if (this.form.format.indexOf(asset.format) == -1) {
      this.form.format.push(asset.format);
    }
    if (this.form.messaging.indexOf(asset.messaging) == -1) {
      this.form.messaging.push(asset.messaging);
    }
    if (this.form.region.indexOf(asset.region) == -1) {
      this.form.region.push(asset.region);
    }
  }.bind(this));
};


airpress.ng.DownloadBarController.prototype.getDownloadUrl = function() {
  for (var i = 0; i < this.assets.length; i++) {
    var asset = this.assets[i];
    if (asset.format == this.asset.format
          && asset.messaging == this.asset.messaging
          && asset.region == this.asset.region) {
      return asset.download_url;
    }
  }
};


airpress.initTables = function() {
  // TODO: Clean up this code.
  $('.page-document > table').each(function(i, table) {
    var $table = $(table);
    if ($table) {
      var numCols = $(this).find('> tbody > tr:first-child > td').size();
      if ($table.attr('class').indexOf('page-document-table') < 0) {
        $(this).addClass('cols-' + numCols);
      }
    }
  });
  $('.page--hidden').removeClass('page--hidden');

  var buildToc = function() {
    var tocEl = document.querySelector('.toc--auto ul');
    if (tocEl) {
      var els = document.querySelectorAll('h2');
      [].forEach.call(els, function(el, i) {
        var elId = 'toc-' + i;
        el.setAttribute('id', elId);
        var title = el.textContent;
        var listItemEl = $('<li><a data-scroll href="#' + elId + '">' + title + '</a></li>');
        $(tocEl).append(listItemEl);
      });
    }
  };
  buildToc();
};
