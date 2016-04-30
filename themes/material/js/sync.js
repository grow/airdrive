var airpress = airpress || {};
airpress.sync = airpress.sync || {};


airpress.sync.sync = function(resourceId) {
  return airpress.rpc('admins.sync', {
    'resources': [
      {'resource_id': resourceId}
    ]
  });
};
