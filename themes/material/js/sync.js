var airpress = airpress || {};
airpress.sync = airpress.sync || {};


airpress.sync.sync = function(resourceId) {
  airpress.rpc('admins.sync', {
    'resources': [
      {'resource_id': resourceId}
    ]
  }).done(
      function(resp) {
    console.log(resp);
    this.$scope.$apply();
  }.bind(this));
};
