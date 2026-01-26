"use strict";

(function (window, document) {
  'use strict';
  function e(a) {
    this.i = "a-z";this.a = { tags: [] };this.g = a;this.c = a.querySelectorAll(".codelab-card");for (var d = a = 0; d < this.c.length; d++) {
      var b = this.c[d];b.j = (b.dataset.title || "").trim().toLowerCase();b.h = f((b.dataset.category || "").split(","));b.tags = f((b.dataset.tags || "").split(","));b.f = new Date(b.dataset.updated);b.duration = parseInt(b.dataset.duration, 10);b.dataset.pin && (a += 1, b.b = a);
    }
  }e.prototype.sort = function (a) {
    this.i = a;g(this);
  };
  e.prototype.filter = function (a) {
    this.a.cat = h(a.cat);this.a.text = h(a.text);this.a.tags = f(a.tags);this.a.kioskTags = f(a.kioskTags);g(this);
  };e.prototype.filterByCategory = function (a) {
    this.a.cat = h(a);g(this);
  };e.prototype.filterByText = function (a) {
    this.a.text = h(a);g(this);
  };e.prototype.filterByTags = function (a, d) {
    this.a.tags = f(a);this.a.kioskTags = f(d);g(this);
  };e.prototype.clearFilters = function () {
    this.filter({ tags: [], kioskTags: [] });
  };
  function g(a) {
    for (var d = Array.prototype.slice.call(a.c, 0), b = d.length; b--;) {
      var c = d[b];if (a.a.kioskTags && 0 < a.a.kioskTags.length && !l(a.a.kioskTags, c.tags)) c = !1;else {
        var n = !a.a.cat;if (a.a.cat) for (var k = 0; k < c.h.length; k++) {
          a.a.cat === c.h[k] && (n = !0);
        }c = !n || a.a.text && -1 === c.j.indexOf(a.a.text) || 0 < a.a.tags.length && !l(a.a.tags, c.tags) ? !1 : !0;
      }c || d.splice(b, 1);
    }m(a, d);for (b = 0; b < a.c.length; b++) {
      c = a.c[b], c.parentNode && c.parentNode.removeChild(c);
    }d.forEach(a.g.appendChild.bind(a.g));
  }
  function m(a, d) {
    switch (a.i) {case "duration":
        d.sort(function (a, c) {
          var b = p(a, c);return null !== b ? b : a.duration - c.duration;
        });break;case "recent":
        d.sort(function (a, c) {
          var b = p(a, c);return null !== b ? b : c.f < a.f ? -1 : c.f > a.f ? 1 : 0;
        });break;default:
        d.sort(function (a, c) {
          var b = p(a, c);return null !== b ? b : a.dataset.title < c.dataset.title ? -1 : a.dataset.title > c.dataset.title ? 1 : 0;
        });}
  }function h(a) {
    return (a || "").trim().toLowerCase();
  }
  function f(a) {
    a = a || [];for (var d = [], b = 0; b < a.length; b++) {
      var c = h(a[b]);c && d.push(c);
    }d.sort();return d;
  }function p(a, d) {
    return a.b && !d.b ? -1 : !a.b && d.b ? 1 : a.b && d.b ? a.b - d.b : null;
  }function l(a, d) {
    for (var b = 0, c = 0; b < a.length && c < d.length;) {
      if (a[b] < d[c]) b++;else if (a[b] > d[c]) c++;else return !0;
    }return !1;
  };window.CardSorter = e;
})(window, document);