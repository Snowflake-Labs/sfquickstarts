"use strict";

var _typeof = typeof Symbol === "function" && typeof Symbol.iterator === "symbol" ? function (obj) { return typeof obj; } : function (obj) { return obj && typeof Symbol === "function" && obj.constructor === Symbol && obj !== Symbol.prototype ? "symbol" : typeof obj; };

/*! (C) WebReflection Mit Style License */
var URLSearchParams = URLSearchParams || function () {
  "use strict";
  function e(e) {
    return encodeURIComponent(e).replace(i, u);
  }function t(e) {
    return decodeURIComponent(e.replace(s, " "));
  }function n(e) {
    this[f] = Object.create(null);if (!e) return;for (var n, r, i = (e || "").split("&"), s = 0, o = i.length; s < o; s++) {
      r = i[s], n = r.indexOf("="), -1 < n && this.append(t(r.slice(0, n)), t(r.slice(n + 1)));
    }
  }function l() {
    try {
      return !!Symbol.iterator;
    } catch (e) {
      return !1;
    }
  }var r = n.prototype,
      i = /[!'\(\)~]|%20|%00/g,
      s = /\+/g,
      o = { "!": "%21", "'": "%27", "(": "%28", ")": "%29", "~": "%7E", "%20": "+", "%00": "\0" },
      u = function u(e) {
    return o[e];
  },
      a = l(),
      f = "__URLSearchParams__:" + Math.random();r.append = function (t, n) {
    var r = this[f];t in r ? r[t].push("" + n) : r[t] = ["" + n];
  }, r.delete = function (t) {
    delete this[f][t];
  }, r.get = function (t) {
    var n = this[f];return t in n ? n[t][0] : null;
  }, r.getAll = function (t) {
    var n = this[f];return t in n ? n[t].slice(0) : [];
  }, r.has = function (t) {
    return t in this[f];
  }, r.set = function (t, n) {
    this[f][t] = ["" + n];
  }, r.forEach = function (t, n) {
    var r = this[f];Object.getOwnPropertyNames(r).forEach(function (e) {
      r[e].forEach(function (r) {
        t.call(n, r, e, this);
      }, this);
    }, this);
  }, r.keys = function () {
    var t = [];this.forEach(function (e, n) {
      t.push(n);
    });var n = { next: function next() {
        var e = t.shift();return { done: e === undefined, value: e };
      } };return a && (n[Symbol.iterator] = function () {
      return n;
    }), n;
  }, r.values = function () {
    var t = [];this.forEach(function (e) {
      t.push(e);
    });var n = { next: function next() {
        var e = t.shift();return { done: e === undefined, value: e };
      } };return a && (n[Symbol.iterator] = function () {
      return n;
    }), n;
  }, r.entries = function () {
    var t = [];this.forEach(function (e, n) {
      t.push([n, e]);
    });var n = { next: function next() {
        var e = t.shift();return { done: e === undefined, value: e };
      } };return a && (n[Symbol.iterator] = function () {
      return n;
    }), n;
  }, a && (r[Symbol.iterator] = r.entries), r.toJSON = function () {
    return {};
  }, r.toString = function y() {
    var t = this[f],
        n = [],
        r,
        i,
        s,
        o;for (i in t) {
      s = e(i);for (r = 0, o = t[i]; r < o.length; r++) {
        n.push(s + "=" + e(o[r]));
      }
    }return n.join("&");
  };var c = Object.defineProperty,
      h = Object.getOwnPropertyDescriptor,
      p = function p(e) {
    function t(t, n) {
      r.append.call(this, t, n), t = this.toString(), e.set.call(this._usp, t ? "?" + t : "");
    }function n(t) {
      r.delete.call(this, t), t = this.toString(), e.set.call(this._usp, t ? "?" + t : "");
    }function i(t, n) {
      r.set.call(this, t, n), t = this.toString(), e.set.call(this._usp, t ? "?" + t : "");
    }return function (e, r) {
      return e.append = t, e.delete = n, e.set = i, c(e, "_usp", { configurable: !0, writable: !0, value: r });
    };
  },
      d = function d(e) {
    return function (t, n) {
      return c(t, "_searchParams", { configurable: !0, writable: !0, value: e(n, t) }), n;
    };
  },
      v = function v(e) {
    var t = e.append;e.append = r.append, n.call(e, e._usp.search.slice(1)), e.append = t;
  },
      m = function m(e, t) {
    if (!(e instanceof t)) throw new TypeError("'searchParams' accessed on an object that does not implement interface " + t.name);
  },
      g = function g(e) {
    var t = e.prototype,
        r = h(t, "searchParams"),
        i = h(t, "href"),
        s = h(t, "search"),
        o;!r && s && s.set && (o = d(p(s)), Object.defineProperties(t, { href: { get: function get() {
          return i.get.call(this);
        }, set: function set(e) {
          var t = this._searchParams;i.set.call(this, e), t && v(t);
        } }, search: { get: function get() {
          return s.get.call(this);
        }, set: function set(e) {
          var t = this._searchParams;s.set.call(this, e), t && v(t);
        } }, searchParams: { get: function get() {
          return m(this, e), this._searchParams || o(this, new n(this.search.slice(1)));
        }, set: function set(t) {
          m(this, e), o(this, t);
        } } }));
  };return g(HTMLAnchorElement), /^function|object$/.test(typeof URL === "undefined" ? "undefined" : _typeof(URL)) && g(URL), n;
}();
(function (window, document) {
  'use strict';

  var app = function app() {
    // Grab a reference to our auto-binding template
    // and give it some initial binding values
    // Learn more about auto-binding templates at http://goo.gl/Dx1u2g
    var app = document.querySelector('#app');

    app.categoryStartCards = {};
    // Tags which should always be kept for filtering,
    // no matter what.
    // Populated in the reconstructFromURL.
    app.kioskTags = [];

    // template is="dom-bind" has stamped its content.
    app.addEventListener('dom-change', function (e) {
      // Use element's protected _readied property to signal if a dom-change
      // has already happened.
      if (app._readied) {
        return;
      }

      // Calculate category offsets.
      var cards = document.querySelectorAll('.codelab-card');
      Array.prototype.forEach.call(cards, function (card, i) {
        var category = card.getAttribute('data-category');
        if (app.categoryStartCards[category] === undefined) {
          app.categoryStartCards[category] = card;
        }
      });
    });

    app.codelabUrl = function (view, codelab) {
      var codelabUrlParams = 'index=' + encodeURIComponent('../..' + view.url);
      if (view.ga) {
        codelabUrlParams += '&viewga=' + view.ga;
      }
      return codelab.url + '?' + codelabUrlParams;
    };

    app.sortBy = function (e, detail) {
      var order = detail.item.textContent.trim().toLowerCase();
      this.$.cards.sort(order);
    };

    app.filterBy = function (e, detail) {
      if (detail.hasOwnProperty('selected')) {
        this.$.cards.filterByCategory(detail.selected);
        return;
      }
      detail.kioskTags = app.kioskTags;
      this.$.cards.filter(detail);
    };

    app.onCategoryActivate = function (e, detail) {
      var item = e.target.selectedItem;
      if (item && item.getAttribute('filter') === detail.selected) {
        detail.selected = null;
      }
      if (!detail.selected) {
        this.async(function () {
          e.target.selected = null;
        });
      }
      this.filterBy(e, { selected: detail.selected });

      // Update URL deep link to filter.
      var params = new URLSearchParams(window.location.search.slice(1));
      params.delete('cat'); // delete all cat params
      if (detail.selected) {
        params.set('cat', detail.selected);
      }

      // record in browser history to make the back button work
      var url = window.location.pathname;
      var search = '?' + params;
      if (search !== '?') {
        url += search;
      }
      window.history.pushState({}, '', url);

      updateLuckyLink();
    };

    function updateLuckyLink() {
      var luckyLink = document.querySelector('.js-lucky-link');
      if (!luckyLink) {
        return;
      }
      var cards = app.$.cards.querySelectorAll('.codelab-card');
      if (cards.length < 2) {
        luckyLink.href = '#';
        luckyLink.parentNode.style.display = 'none';
        return;
      }
      var i = Math.floor(Math.random() * cards.length);
      luckyLink.href = cards[i].href;
      luckyLink.parentNode.style.display = null;
    }

    var chips = document.querySelector('#chips');

    /**
     * Highlights selected chips identified by tags.
     * @param {!string|Array<!string>}
     */
    function selectChip(tags) {
      if (!chips) {
        return;
      }
      tags = Array.isArray(tags) ? tags : [tags];
      var chipElems = chips.querySelectorAll('.js-chips__item');
      for (var i = 0; i < chipElems.length; i++) {
        var el = chipElems[i];
        if (tags.indexOf(el.getAttribute('filter')) != -1) {
          el.classList.add('selected');
        } else {
          el.classList.remove('selected');
        }
      }
    }

    if (chips) {
      chips.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();

        // Make sure the click was on a chip.
        var tag = e.target.getAttribute('filter');
        if (!tag) {
          return;
        }
        // Remove or add the selected class.
        e.target.classList.toggle('selected');
        // Collect all selected chips.
        var tags = [];
        var chipElems = chips.querySelectorAll('.js-chips__item.selected');
        for (var i = 0; i < chipElems.length; i++) {
          var t = chipElems[i].getAttribute('filter');
          if (t) {
            tags.push(t);
          }
        }
        // Re-run the filter and select a new random codelab
        // from the filtered subset.
        app.filterBy(null, { tags: tags });
        updateLuckyLink();
      });
    }

    app.reconstructFromURL = function () {
      var params = new URLSearchParams(window.location.search.slice(1));
      var cat = params.get('cat');
      var tags = params.getAll('tags');
      var filter = params.get('filter');
      var i = tags.length;
      while (i--) {
        if (tags[i] === 'kiosk' || tags[i].substr(0, 6) === 'kiosk-') {
          app.kioskTags.push(tags[i]);
          tags.splice(i, 1);
        }
      }

      if (this.$.categorylist) {
        this.$.categorylist.selected = cat;
      }
      if (this.$.sidelist) {
        this.$.sidelist.selected = cat;
      }
      if (tags) {
        selectChip(tags);
      }
      this.filterBy(null, { cat: cat, tags: tags });
      if (filter) {
        app.searchVal = filter;
        app.onSearchKeyDown();
      }
      updateLuckyLink();
    };

    // Prevent immediate link navigation.
    app.navigate = function (event) {
      event.preventDefault();

      var go = function go(href) {
        window.location.href = href;
      };

      var target = event.currentTarget;
      var wait = target.hasAttribute('data-wait-for-ripple');
      if (wait) {
        target.addEventListener('transitionend', go.bind(target, target.href));
      } else {
        go(target.href);
      }
    };

    app.clearSearch = function (e, detail) {
      this.searchVal = null;
      this.$.cards.filterByText(null);
    };

    app.onSearchKeyDown = function (e, detail) {
      this.debounce('search', function () {
        this.$.cards.filterByText(app.searchVal);
      }, 250);
    };

    return app;
  };

  // unregisterServiceWorker removes the service worker. We used to use SW, but
  // now we don't. This is for backwards-compatibility.
  var unregisterServiceWorker = function unregisterServiceWorker() {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.ready.then(function (reg) {
        reg.unregister();
      });
    }
  };

  // loadWebComponents checks if web components are supported and loads them if
  // they are not present.
  var loadWebComponents = function loadWebComponents() {
    var supported = 'registerElement' in document && 'import' in document.createElement('link') && 'content' in document.createElement('template');

    // If web components are supported, we likely missed the event since it
    // fires before the DOM is ready. Re-fire that event.
    if (supported) {
      document.dispatchEvent(new Event('WebComponentsReady'));
    } else {
      var script = document.createElement('script');
      script.async = true;
      script.src = '/bower_components/webcomponentsjs/webcomponents-lite.min.js';
      document.head.appendChild(script);
    }
  };

  var init = function init() {
    // Unload legacy service worker
    unregisterServiceWorker();

    // load the web components - this will emit WebComponentsReady when finished
    loadWebComponents();
  };

  // Wait for the app to be ready and initalized, and then remove the class
  // hiding the unrendered components on the body. This prevents the FOUC as
  // cards are shuffled into the correct order client-side.
  document.addEventListener('AppReady', function () {
    document.body.classList.remove('loading');
  });

  // Wait for web components to be ready and then load the app.
  document.addEventListener('WebComponentsReady', function () {
    var a = app();

    // TODO: handle forward/backward and filter cards
    window.addEventListener('popstate', function () {
      a.reconstructFromURL();
    });

    // debounce fails with "Cannot read property of undefined" without this
    if (a._setupDebouncers) {
      a._setupDebouncers();
    }

    // Rebuild and sort cards based on the URL
    a.reconstructFromURL();

    // Notify the app is ready
    document.dispatchEvent(new Event('AppReady'));
  });

  // This file is loaded asyncronously, so the document might already be fully
  // loaded, in which case we can drop right into initialization. Otherwise, we
  // need to wait for the document to be loaded.
  if (document.readyState === 'complete' || document.readyState === 'loaded' || document.readyState === 'interactive') {
    init();
  } else {
    document.addEventListener('DOMContentLoaded', init);
  }
})(window, document);