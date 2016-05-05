var airpress = airpress || {};
airpress.menu = airpress.menu || {};


airpress.menu.updateSidebar = function() {
  var layoutEl = document.querySelector('.layout');
  if (layoutEl && layoutEl.classList.contains('layout--wide')) {
    return;
  }
  var enabled = document.body.offsetWidth <= 1440;
  document.body.classList.toggle('body--drawer-enabled', enabled);
};


airpress.menu.init = function() {
  window.addEventListener('resize', airpress.menu.updateSidebar);

  var items = document.querySelectorAll('ul.menu');
  [].forEach.call(items, function(el) {
    airpress.menu.decorate(el);
  });

  document.body.addEventListener('click', function(e) {
    if (e.target.classList.contains('layout-main-mask')) {
      document.body.classList.remove('body--drawer-open');
    }

    if (e.target.classList.contains('layout-main-header-menu')) {
      document.body.classList.toggle('body--drawer-open');
    }

    if (!e.target.classList.contains('menu-item--folder')) {
      return;
    }

    // If config.keep_folders_open.
    if (!e.target.querySelector('i')) {
      return;
    }
    var el = e.target;
    var parentEl = el.parentNode;
    var sublistEl = parentEl.nextSibling && parentEl.nextSibling.nextSibling;
    if (sublistEl) {
      sublistEl.classList.toggle('menu-item-child--open');
    }
    var siblingListEl = sublistEl.previousSibling &&
        sublistEl.previousSibling.previousSibling;
    if (siblingListEl) {
      siblingListEl.classList.toggle('menu-item-child--open');
    }
    e.preventDefault();
  });
};


airpress.menu.decorate = function(el) {
  var item = el.querySelector('.menu-item--active');
  do {
    if (item) {
      item.classList.add('menu-item-child--open');
      if (item.tagName == 'UL' &&
          item.previousSibling &&
          item.previousSibling.previousSibling.tagName == 'LI') {
        var sibling = item.previousSibling.previousSibling;
        sibling.classList.add('menu-item-child--open');
      }
      item = item.parentNode;
    }
  } while (item && item != el);
  if (item == el) {
    item.classList.add('menu-item-child--open');
  }
  el.classList.remove('menu--hidden');
};
