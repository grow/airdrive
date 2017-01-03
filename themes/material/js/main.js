var airpress = airpress || {};

if (!String.prototype.endsWith) {
  String.prototype.endsWith = function(searchString, position) {
      var subjectString = this.toString();
      if (typeof position !== 'number' || !isFinite(position) || Math.floor(position) !== position || position > subjectString.length) {
        position = subjectString.length;
      }
      position -= searchString.length;
      var lastIndex = subjectString.lastIndexOf(searchString, position);
      return lastIndex !== -1 && lastIndex === position;
  };
}


airpress.main = function() {
  angular.module('airpress', [])
      .config(['$interpolateProvider', function($interpolateProvider) {
         $interpolateProvider.startSymbol('[[').endSymbol(']]');
      }])
      .controller('FoldersController', airpress.ng.FoldersController)
      .controller('FooterNavController', airpress.ng.FooterNavController)
      .controller('DownloadBarController', airpress.ng.DownloadBarController)
      .controller('AdminsController', airpress.ng.AdminsController)
      .controller('ApprovalController', airpress.ng.ApprovalController)
      .controller('ApprovalsController', airpress.ng.ApprovalsController)
      .controller('SettingsController', airpress.ng.SettingsController)
      .controller('SyncController', airpress.ng.SyncController)
      .filter('filesize', function() {
        return function(bytes, precision) {
          if (isNaN(parseFloat(bytes)) || !isFinite(bytes)) return '-';
          if (typeof precision === 'undefined') precision = 1;
          var units = ['bytes', 'kB', 'MB', 'GB', 'TB', 'PB'];
          var number = Math.floor(Math.log(bytes) / Math.log(1024));
          return (bytes / Math.pow(1024, Math.floor(number))).toFixed(precision) +  ' ' + units[number];
        };
      })
      .filter('prettyLanguage', function() {
        return function(identifier) {
	  return airpress.prettyLanguage(identifier);
	};
      });
  angular.bootstrap(document, ['airpress'])
  smoothScroll.init({offset: 40});
  airpress.moveLayoutFooter();
};


airpress.prettyLanguage = function(identifier) {
  switch (identifier) {
    case 'de':
      return 'German';
    case 'fr-ca':
      return 'French (Canada)';
    case 'en-nz':
      return 'English (New Zealand)';
    case 'es':
      return 'Spanish';
    case 'fi':
      return 'Finnish';
    case 'fr':
      return 'French (France)';
    case 'it':
      return 'Italian';
    case 'nl':
      return 'Dutch';
    case 'no':
      return 'Norwegian';
    case 'se':
      return 'Swedish';
    case 'sv':
      return 'Swedish';
    case 'ja':
      return 'Japanese';
    case 'jp':
      return 'Japanese';
    case 'dk':
      return 'Danish';
    case 'da':
      return 'Danish';
    case 'en':
      return 'English (US)';
    case 'en-au':
      return 'English (Australia)';
    case 'en-gb':
      return 'English (UK)';
    case 'en-ca':
      return 'English (Canada)';
    case 'en-in':
      return 'English (India)';
    case 'fr-ca':
      return 'French (Canada)';
  }
  return identifier;
};


airpress.moveLayoutFooter = function() {
  var el = document.querySelector('.page-document .layout-main-footer');
  if (!el) {
    return;
  }
  el.parentNode.parentNode.appendChild(el);
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
  this.email = null;
  this.approvals = [];
  this.searchApprovals();
};


airpress.ng.ApprovalsController.prototype.createApprovals =
    function(users, sendEmail) {
  var form = this.getFormWithFolders();
  airpress.rpc('admins.directly_add_users', {
    'users': users,
    'form': form,
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


airpress.ng.ApprovalsController.prototype.deleteSelectedApprovals =
    function() {
  var approvals = [];
  this.approvals.forEach(function(approval) {
    if (approval.selected) {
      approvals.push(approval);
    }
  });
  this.deleteApprovals(approvals);
};


airpress.ng.ApprovalsController.prototype.getFormWithFolders = function() {
  var form = {};
  var folders = [];
  for (var choice in this.folderChoices) {
    if (this.folderChoices[choice]) {
      folders.push(choice);
    }
  }
  form.folders = folders;
  return form;
};


airpress.ng.ApprovalsController.prototype.importApprovals = function(sheetId, sheetGid) {
  this.loadingImport = true;
  var form = this.getFormWithFolders();
  airpress.rpc('admins.import_approvals', {
    'form': form,
    'sheet_gid': sheetGid,
    'sheet_id': sheetId
  }).done(function(resp) {
    this.loadingImport = false;
    this.importedApprovals = resp['approvals'];
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


airpress.ng.ApprovalsController.prototype.deleteApprovals = function(approvals) {
  if (!window.confirm('Really delete ' + approvals.length + ' users?')) {
    return;
  }
  var deletedIdents = [];
  approvals.forEach(function(approval) {
    deletedIdents.push(approval.ident);
  });
  airpress.rpc('admins.delete_approvals', {
    'approvals': approvals
  }).done(
      function(resp) {
    this.approvals = this.approvals.filter(function(item) {
      return deletedIdents.indexOf(item['ident']) == -1;
    });
    this.$scope.$apply();
  }.bind(this));
};


airpress.ng.ApprovalsController.prototype.searchApprovals = function(opt_cursor, opt_clear) {
  this.loading = true;
  var kwargs = {};
  if (this.email) {
    kwargs['email'] = this.email;
  } else if (opt_cursor) {
    kwargs['cursor'] = opt_cursor;
  }
  airpress.rpc('admins.search_approvals', kwargs).done(
      function(resp) {
    this.loading = false;
    if (resp['approvals']) {
      if (this.email && !opt_cursor || opt_clear) {
        this.approvals = [];
      }
      this.approvals = this.approvals.concat(resp['approvals']);
    }
    this.count = resp['count'];
    this.hasMore = resp['has_more'];
    this.nextCursor = resp['cursor'];
    this.$scope.$apply();
  }.bind(this));
};


airpress.ng.ApprovalsController.prototype.toggleSelectAll = function(selected) {
  this.approvals.forEach(function(approval) {
    approval.selected = selected;
  });
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
  airpress.rpc('admins.get_sync_tree', {}).done(function(resp) {
    console.log(resp);
  }.bind(this));
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


airpress.ng.ApprovalController.prototype.updateForm = function() {
  var approval = this.approval;
  airpress.rpc('admins.update_approvals', {
    'approvals': [approval]
  });
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
  this.selectedAsset = {};
  this.assets = {};
  this.loaded = false;
  this.maskEl = document.querySelector('.downloadbar-mask');

  var buttonEls = document.querySelectorAll('[data-asset-parentkey]');
  [].forEach.call(buttonEls, function(buttonEl) {
    var parentKey = buttonEl.getAttribute('data-asset-parentkey');
    buttonEl.addEventListener('click', function() {
      this.setVisible(!this.visible, parentKey);
      this.$scope.$apply();
    }.bind(this));
  }.bind(this));

  this.maskEl.addEventListener('click', function() {
    this.setVisible(false);
    this.$scope.$apply();
  }.bind(this));

  $scope.$watch(function(scope) {
    return this.selectedAsset.language;
  }.bind(this), function(newVal, oldVal) {
    if (newVal) {
      window.localStorage['hl'] = newVal;
    }
  }.bind(this));
};


airpress.ng.DownloadBarController.prototype.orderBy = function(item) {
  return airpress.prettyLanguage(item);
};


airpress.ng.DownloadBarController.prototype.setVisible =
    function(visible, parentKey) {
  if (visible) {
      this.maskEl.classList.add('downloadbar-mask--visible');
      this.updateForm_([]);
  } else {
      this.maskEl.classList.remove('downloadbar-mask--visible');
  }
  this.visible = visible;
  if (!visible) {
    return;
  }
  this.updateAsset_(parentKey);
};


airpress.ng.DownloadBarController.prototype.updateAsset_ = function(parentKey) {
  airpress.rpc('assets.get_group', {
    'parent_key': parentKey
  }).done(
      function(resp) {
    this.updateForm_(resp['assets']);
    if (resp['folder']) {
      this.selectedAsset.title = resp['folder']['title'];
    }
    this.loaded = true;
    this.$scope.$apply();
  }.bind(this));
};


airpress.ng.DownloadBarController.prototype.hasThumbnail = function(asset) {
  if (!asset) {
    return;
  }
  // Special case for PSD: Google Drive only generates thumbnails for files
  // under 50MiB.
  if (asset.metadata.ext == '.psd') {
    return asset.size < 52430000;
  }
  var exts = ['.jpg', '.png', '.pdf'];
  return exts.indexOf(asset.metadata.ext) != -1;
};


airpress.ng.DownloadBarController.prototype.updateForm_ = function(assets) {
  this.selectedAsset = {};
  this.assets = assets;
  this.form = {
    dimensions: [],
    label: [],
    variant: [],
    language: [],
  };
  if (!this.assets) {
    return;
  }
  this.assets.forEach(function(asset) {
    asset.metadata.language = asset.metadata.language || 'en';
    if (this.form.dimensions.indexOf(asset.metadata.dimensions) == -1) {
      if (asset.metadata.dimensions) {
        this.form.dimensions.push(asset.metadata.dimensions);
      }
    }
    if (this.form.label.indexOf(asset.metadata.label) == -1) {
      if (asset.metadata.label) {
	this.form.label.push(asset.metadata.label);
      }
    }
    if (this.form.language.indexOf(asset.metadata.language) == -1) {
      if (asset.metadata.language) {
        this.form.language.push(asset.metadata.language);
      }
    }
    if (this.form.variant.indexOf(asset.metadata.variant) == -1) {
      if (asset.metadata.variant) {
        this.form.variant.push(asset.metadata.variant);
      }
    }
  }.bind(this));
  if (this.form.variant.length == 1) {
    this.selectedAsset.variant = this.form.variant[0];
  }
  if (this.form.label.length == 1) {
    this.selectedAsset.label = this.form.label[0];
  }
  if (this.form.dimensions.length == 1) {
    this.selectedAsset.dimensions = this.form.dimensions[0];
  }
  if (this.form.language.length == 1) {
    this.selectedAsset.language = this.form.language[0];
  }
  var hl = window.localStorage['hl'];
  if (!hl) {
    return;
  }
  if (this.form.language.indexOf(hl) != -1) {
    this.selectedAsset.language = hl;
  }
};


airpress.ng.DownloadBarController.prototype.getAsset = function() {
  if (!this.assets) {
    return;
  }
  for (var i = 0; i < this.assets.length; i++) {
    var asset = this.assets[i];
    if (asset.metadata.dimensions == this.selectedAsset.dimensions
          && asset.metadata.label == this.selectedAsset.label
          && asset.metadata.language == this.selectedAsset.language) {
      return asset;
    }
  }
};


airpress.ng.DownloadBarController.prototype.getAssetWithSize = function(size) {
  if (!this.assets) {
    return;
  }
  for (var i = 0; i < this.assets.length; i++) {
    var asset = this.assets[i];
    if (asset.metadata.dimensions == size
          && asset.metadata.label == this.selectedAsset.label
          && asset.metadata.language == this.selectedAsset.language) {
      return asset;
    }
  }
};


airpress.ng.DownloadBarController.prototype.updateThumbnailPreview =
    function(opt_enabled) {
  if (opt_enabled === false) {
    this.thumbnailPreviewUrl = null;
    return;
  }
  var asset = this.getAsset();
  if (!asset) {
    return;
  }
  var image = new Image();
  image.onload = function() {
    this.thumbnailPreviewUrl = image.src;
    this.$scope.$apply();
  }.bind(this);
  image.onerror = function() {
    this.thumbnailPreviewUrl = null;
    this.$scope.$apply();
  }.bind(this);
  image.src = asset.thumbnail_url;
};


airpress.ng.DownloadBarController.prototype.getDownloadUrl = function() {
  var asset = this.getAsset();
  if (!asset) {
    return;
  }
  return asset.download_url;
};


airpress.initTables = function() {
  // TODO: Clean up this code.
  $('.page-document > table').each(function(i, table) {
    var $table = $(table);
    if ($table) {
      var numCols = $(this).find('> tbody > tr:first-child > td').size();
      var numRows = $(this).find('tr').size();
      if ($table.attr('class').indexOf('page-document-table')) {
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


airpress.ng.FooterNavController = function($scope, $element) {
  this.el_ = $element[0];
  this.$scope = $scope;

  var next = this.getSibling(true);
  var prev = this.getSibling();
  this.$scope.next = next;
  this.$scope.prev = prev;
};


airpress.ng.FooterNavController.prototype.getSibling = function(opt_next, opt_root) {
  var selectedEl = document.querySelector('.menu-item--active');
  var linkEl = opt_root || selectedEl.parentNode;
  if (opt_next) {
    var nextItemEl = linkEl.nextSibling;
    if (nextItemEl.nodeType == 3) {  // Text node.
      nextItemEl = nextItemEl.nextSibling;
    }
    if (!nextItemEl) {
      var parentList = linkEl.parentNode;
      nextItemEl = parentList.nextSibling;
      if (nextItemEl.nodeType == 3) {
        nextItemEl = nextItemEl.nextSibling;
      }
    }
  } else {
    var nextItemEl = linkEl.previousSibling;
    if (nextItemEl.nodeType == 3) {  // Text node.
      nextItemEl = nextItemEl.previousSibling;
    }
    if (!nextItemEl) {
      var parentList = linkEl.parentNode;
      nextItemEl = parentList.previousSibling;
      if (nextItemEl.nodeType == 3) {
        nextItemEl = nextItemEl.previousSibling;
      }
    }
  }
  if (!nextItemEl) {
    return;
  }
  var nextLinkEl = nextItemEl.querySelector('a');
  var title = nextLinkEl.textContent.trim();
  var url = nextLinkEl.href;
  var title = title.split('\n')[0];
  if (url == 'javascript:') {
    return this.getSibling(opt_next, nextItemEl);
  }
  return {
    title: title,
    url: url
  }
};
