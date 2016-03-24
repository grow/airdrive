var airpress = airpress || {};
airpress.menu = airpress.menu || {};


airpress.menu.init = function() {
  var decorateMenu = function(el) {
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

  var items = document.querySelectorAll('ul.menu');
  [].forEach.call(items, function(el) {
    decorateMenu(el);
  });

  document.body.addEventListener('click', function(e) {
    if (!e.target.classList.contains('menu-item--folder')) {
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
