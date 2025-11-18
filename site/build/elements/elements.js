(function() {

  // Ensure that the `unresolved` attribute added by the WebComponents polyfills
  // is removed. This is done as a convenience so users don't have to remember
  // to do so themselves. This attribute provides FOUC prevention when
  // native Custom Elements is not available.

  function resolve() {
    document.body.removeAttribute('unresolved');
  }

  if (window.WebComponents) {
    addEventListener('WebComponentsReady', resolve);
  } else {
    if (document.readyState === 'interactive' || document.readyState === 'complete') {
      resolve();
    } else {
      addEventListener('DOMContentLoaded', resolve);
    }
  }

})();
window.Polymer = {
    Settings: (function() {
      // NOTE: Users must currently opt into using ShadowDOM. They do so by doing:
      // Polymer = {dom: 'shadow'};
      // TODO(sorvell): Decide if this should be auto-use when available.
      // TODO(sorvell): if SD is auto-use, then the flag above should be something
      // like: Polymer = {dom: 'shady'}

      // via Polymer object
      var settings = window.Polymer || {};

      // via url
      var parts = location.search.slice(1).split('&');
      for (var i=0, o; (i < parts.length) && (o=parts[i]); i++) {
        o = o.split('=');
        o[0] && (settings[o[0]] = o[1] || true);
      }

      settings.wantShadow = (settings.dom === 'shadow');
      settings.hasShadow = Boolean(Element.prototype.createShadowRoot);
      settings.nativeShadow = settings.hasShadow && !window.ShadowDOMPolyfill;
      settings.useShadow = settings.wantShadow && settings.hasShadow;

      settings.hasNativeImports = 
        Boolean('import' in document.createElement('link'));
      settings.useNativeImports = settings.hasNativeImports;

      settings.useNativeCustomElements = (!window.CustomElements ||
        window.CustomElements.useNative);

      settings.useNativeShadow = settings.useShadow && settings.nativeShadow;

      settings.usePolyfillProto = !settings.useNativeCustomElements && 
        !Object.__proto__;

      return settings;
    })()
  };
(function() {

    // until ES6 modules become standard, we follow Occam and simply stake out
    // a global namespace

    // Polymer is a Function, but of course this is also an Object, so we
    // hang various other objects off of Polymer.*

    var userPolymer = window.Polymer;

    window.Polymer = function(prototype) {
      // if input is a `class` (aka a function with a prototype), use the prototype
      // remember that the `constructor` will never be called
      if (typeof prototype === 'function') {
        prototype = prototype.prototype;
      }
      // if there is no prototype, use a default empty object
      if (!prototype) {
        prototype = {};
      }
      // desugar the prototype and return a factory object
      var factory = desugar(prototype);
      // Polymer.Base is now chained to factory.prototype, and for IE10 compat
      // this may have resulted in a new prototype being created
      prototype = factory.prototype;
      var options = {
        prototype: prototype
      };
      // NOTE: we're specifically supporting older Chrome versions here 
      // (specifically Chrome 39) that throw when options.extends is undefined.
      if (prototype.extends) {
        options.extends = prototype.extends;
      }
      Polymer.telemetry._registrate(prototype);
      document.registerElement(prototype.is, options);
      return factory;
    };

    var desugar = function(prototype) {
      // Note: need to chain user prototype with the correct type-extended
      // version of Polymer.Base; this is especially important when you can't
      // prototype swizzle (e.g. IE10), since CustomElements uses getPrototypeOf
      var base = Polymer.Base;
      if (prototype.extends) {
        base = Polymer.Base._getExtendedPrototype(prototype.extends);
      }
      prototype = Polymer.Base.chainObject(prototype, base);
      prototype.registerCallback();
      return prototype.constructor;
    };

    if (userPolymer) {
      for (var i in userPolymer) {
        Polymer[i] = userPolymer[i];
      }
    }

    Polymer.Class = desugar;

  })();

  /*
  // Raw usage
  [ctor =] Polymer.Class(prototype);
  document.registerElement(name, ctor);

  // Simplified usage
  [ctor = ] Polymer(prototype);
  */

  // telemetry: statistics, logging, and debug

  Polymer.telemetry = {
    registrations: [],
    _regLog: function(prototype) {
      console.log('[' + prototype.is + ']: registered')
    },
    _registrate: function(prototype) {
      this.registrations.push(prototype);
      Polymer.log && this._regLog(prototype);
    },
    dumpRegistrations: function() {
      this.registrations.forEach(this._regLog);
    }
  };
// a tiny bit of sugar for `document.currentScript.ownerDocument`
  Object.defineProperty(window, 'currentImport', {
    enumerable: true,
    configurable: true,
    get: function() {
      return (document._currentScript || document.currentScript).ownerDocument;
    }
  });
/*
   * Helper for determining when first render occurs.
   * Call `Polymer.RenderStatus.whenReady(callback)` to be notified when
   * first render occurs or immediately if it has already occured.
   * Note that since HTML Imports are designed to load before rendering,
   * this call can also be used to guarantee that imports have loaded.
   * This behavior is normalized to function correctly with the HTMLImports
   * polyfill which does not otherwise maintain this rendering guarantee.
   * Querying style and layout data before first render is currently
   * problematic on some browsers (Blink/Webkit) so this helper can be used
   * to prevent doing so until a safe time.
   */
  Polymer.RenderStatus = {

    _ready: false,

    _callbacks: [],

    whenReady: function(cb) {
      if (this._ready) {
        cb();
      } else {
        this._callbacks.push(cb);
      }
    },

    _makeReady: function() {
      this._ready = true;
      for (var i=0; i < this._callbacks.length; i++) {
        this._callbacks[i]();
      }
      this._callbacks = [];
    },

    _catchFirstRender: function() {
      requestAnimationFrame(function() {
        Polymer.RenderStatus._makeReady();
      });
    },

    _afterNextRenderQueue: [],
    _waitingNextRender: false,

    afterNextRender: function(element, fn, args) {
      this._watchNextRender();
      this._afterNextRenderQueue.push([element, fn, args]);
    },

    _watchNextRender: function() {
      if (!this._waitingNextRender) {
        this._waitingNextRender = true;
        var fn = function() {
          Polymer.RenderStatus._flushNextRender();
        }
        if (!this._ready) {
          this.whenReady(fn);
        } else {
          requestAnimationFrame(fn);
        }
      }
    },

    _flushNextRender: function() {
      var self = this;
      // we want to defer after render until just after the paint.
      setTimeout(function() {
        self._flushRenderCallbacks(self._afterNextRenderQueue);
        self._afterNextRenderQueue = [];
        self._waitingNextRender = false;
      });
    },

    _flushRenderCallbacks: function(callbacks) {
      for (var i=0, h; i < callbacks.length; i++) {
        h = callbacks[i];
        h[1].apply(h[0], h[2] || Polymer.nar);
      }
    }
  };

  if (window.HTMLImports) {
    HTMLImports.whenReady(function() {
      Polymer.RenderStatus._catchFirstRender();
    });
  } else {
    Polymer.RenderStatus._catchFirstRender();
  }

  // NOTE: for bc.
  Polymer.ImportStatus = Polymer.RenderStatus;
  Polymer.ImportStatus.whenLoaded = Polymer.ImportStatus.whenReady;
(function() {

  'use strict';

  var settings = Polymer.Settings;

  Polymer.Base = {

    // Used for `isInstance` type checking; cannot use `instanceof` because
    // there is no common Polymer.Base in the prototype chain between type
    // extensions and normal custom elements
    __isPolymerInstance__: true,

    // pluggable features
    // `this` context is a prototype, not an instance
    _addFeature: function(feature) {
      this.extend(this, feature);
    },

    // `this` context is a prototype, not an instance
    registerCallback: function() {
      // TODO(sjmiles): perhaps this method should be called from polymer-bootstrap?
      this._desugarBehaviors(); // abstract
      this._doBehavior('beforeRegister'); // abstract
      this._registerFeatures();  // abstract
      if (!settings.lazyRegister) {
        this.ensureRegisterFinished();
      }
    },

    createdCallback: function() {
      if (!this.__hasRegisterFinished) {
        this._ensureRegisterFinished(this.__proto__);
      }
      Polymer.telemetry.instanceCount++;
      this.root = this;
      this._doBehavior('created'); // abstract
      this._initFeatures(); // abstract
    },

    /**
     * As an optimization, when `Polymer.Settings.lazyRegister` is set to true
     * registration tasks are deferred until the first instance of the element
     * is created. If an element should not defer registration tasks until
     * this time, `ensureRegisterFinished` may be called
     * on the element's prototype.
     */
    ensureRegisterFinished: function() {
      this._ensureRegisterFinished(this);
    },

    _ensureRegisterFinished: function(proto) {
      if (proto.__hasRegisterFinished !== proto.is) {
        proto.__hasRegisterFinished = proto.is;
        if (proto._finishRegisterFeatures) {
          proto._finishRegisterFeatures();
        }
        // registration extension point
        proto._doBehavior('registered');
        // where prototypes are simulated (IE10), element instance
        // must be specfically fixed up.
        if (settings.usePolyfillProto && proto !== this) {
          proto.extend(this, proto);
        }
      }
    },

    // reserved for canonical behavior
    attachedCallback: function() {
      // NOTE: workaround for:
      // https://code.google.com/p/chromium/issues/detail?id=516550
      // To allow querying style/layout data in attached, we defer it
      // until we are sure rendering is ready.
      var self = this;
      Polymer.RenderStatus.whenReady(function() {
        self.isAttached = true;
        self._doBehavior('attached'); // abstract
      });
    },

    // reserved for canonical behavior
    detachedCallback: function() {
      // NOTE: duplicate attachedCallback behavior
      var self = this;
      Polymer.RenderStatus.whenReady(function() {
        self.isAttached = false;
        self._doBehavior('detached'); // abstract
      });
    },

    // reserved for canonical behavior
    attributeChangedCallback: function(name, oldValue, newValue) {
      // TODO(sorvell): consider filtering out changes to host attributes
      // note: this was barely measurable with 3 host attributes.
      this._attributeChangedImpl(name); // abstract
      this._doBehavior('attributeChanged', [name, oldValue, newValue]); // abstract
    },

    _attributeChangedImpl: function(name) {
      this._setAttributeToProperty(this, name);
    },

    /**
     * Copies own properties (including accessor descriptors) from a source
     * object to a target object.
     *
     * @method extend
     * @param {Object} prototype Target object to copy properties to.
     * @param {Object} api Source object to copy properties from.
     * @return {Object} prototype object that was passed as first argument.
     */
    extend: function(prototype, api) {
      if (prototype && api) {
        var n$ = Object.getOwnPropertyNames(api);
        for (var i=0, n; (i<n$.length) && (n=n$[i]); i++) {
          this.copyOwnProperty(n, api, prototype);
        }
      }
      return prototype || api;
    },

    /**
     * Copies props from a source object to a target object.
     *
     * Note, this method uses a simple `for...in` strategy for enumerating
     * properties.  To ensure only `ownProperties` are copied from source
     * to target and that accessor implementations are copied, use `extend`.
     *
     * @method mixin
     * @param {Object} target Target object to copy properties to.
     * @param {Object} source Source object to copy properties from.
     * @return {Object} Target object that was passed as first argument.
     */
    mixin: function(target, source) {
      for (var i in source) {
        target[i] = source[i];
      }
      return target;
    },

    copyOwnProperty: function(name, source, target) {
      var pd = Object.getOwnPropertyDescriptor(source, name);
      if (pd) {
        Object.defineProperty(target, name, pd);
      }
    },

    _logger: function(level, args) {
      // accept ['foo', 'bar'] and [['foo', 'bar']]
      if (args.length === 1 && Array.isArray(args[0])) {
        args = args[0];
      }
      // only accept logging functions
      switch(level) {
        case 'log':
        case 'warn':
        case 'error':
          console[level].apply(console, args);
          break;
      }
    },
    _log: function() {
      var args = Array.prototype.slice.call(arguments, 0);
      this._logger('log', args);
    },
    _warn: function() {
      var args = Array.prototype.slice.call(arguments, 0);
      this._logger('warn', args);
    },
    _error: function() {
      var args = Array.prototype.slice.call(arguments, 0);
      this._logger('error', args);
    },
    _logf: function(/* args*/) {
      return this._logPrefix.concat(this.is).concat(Array.prototype.slice.call(arguments, 0));
    }
  };

  Polymer.Base._logPrefix = (function(){
    // only Firefox, Chrome, and Safari support colors in console logging
    var color = (window.chrome && !(/edge/i.test(navigator.userAgent))) || (/firefox/i.test(navigator.userAgent));
    return color ? ['%c[%s::%s]:', 'font-weight: bold; background-color:#EEEE00;'] : ['[%s::%s]:'];
  })();

  Polymer.Base.chainObject = function(object, inherited) {
    if (object && inherited && object !== inherited) {
      if (!Object.__proto__) {
        object = Polymer.Base.extend(Object.create(inherited), object);
      }
      object.__proto__ = inherited;
    }
    return object;
  };

  Polymer.Base = Polymer.Base.chainObject(Polymer.Base, HTMLElement.prototype);

  if (window.CustomElements) {
    Polymer.instanceof = CustomElements.instanceof;
  } else {
    Polymer.instanceof = function(obj, ctor) {
      return obj instanceof ctor;
    };
  }

  Polymer.isInstance = function(obj) {
    return Boolean(obj && obj.__isPolymerInstance__);
  };

  // TODO(sjmiles): ad hoc telemetry
  Polymer.telemetry.instanceCount = 0;

})();
(function() {

  var modules = {};
  var lcModules = {};
  var findModule = function(id) {
    return modules[id] || lcModules[id.toLowerCase()];
  };

  /**
   * The `dom-module` element registers the dom it contains to the name given
   * by the module's id attribute. It provides a unified database of dom
   * accessible via any dom-module element. Use the `import(id, selector)`
   * method to locate dom within this database. For example,
   *
   * <dom-module id="foo">
   *   <img src="stuff.png">
   * </dom-module>
   *
   * Then in code in some other location that cannot access the dom-module above
   *
   * var img = document.createElement('dom-module').import('foo', 'img');
   *
   */
  var DomModule = function() {
    return document.createElement('dom-module');
  };

  DomModule.prototype = Object.create(HTMLElement.prototype);

  Polymer.Base.extend(DomModule.prototype, {

    constructor: DomModule,

    createdCallback: function() {
      this.register();
    },

    /**
     * Registers the dom-module at a given id. This method should only be called
     * when a dom-module is imperatively created. For
     * example, `document.createElement('dom-module').register('foo')`.
     * @method register
     * @param {String} id The id at which to register the dom-module.
     */
    register: function(id) {
      id = id || this.id ||
        this.getAttribute('name') || this.getAttribute('is');
      if (id) {
        this.id = id;
        // store id separate from lowercased id so that
        // in all cases mixedCase id will stored distinctly
        // and lowercase version is a fallback
        modules[id] = this;
        lcModules[id.toLowerCase()] = this;
      }
    },

    /**
     * Retrieves the dom specified by `selector` in the module specified by
     * `id`. For example, this.import('foo', 'img');
     * @method register
     * @param {String} id
     * @param {String} selector
     * @return {Object} Returns the dom which matches `selector` in the module
     * at the specified `id`.
     */
    import: function(id, selector) {
      if (id) {
        var m = findModule(id);
        if (!m) {
          // If polyfilling, a script can run before a dom-module element
          // is upgraded. We force the containing document to upgrade
          // dom-modules and try again to workaround this polyfill limitation.
          forceDomModulesUpgrade();
          m = findModule(id);
        }
        if (m && selector) {
          m = m.querySelector(selector);
        }
        return m;
      }
    }

  });

  // NOTE: HTMLImports polyfill does not
  // block scripts on upgrading elements. However, we want to ensure that
  // any dom-module in the tree is available prior to a subsequent script
  // processing.
  // Therefore, we force any dom-modules in the tree to upgrade when dom-module
  // is registered by temporarily setting CE polyfill to crawl the entire
  // imports tree. (Note: this should only upgrade any imports that have been
  // loaded by this point. In addition the HTMLImports polyfill should be
  // changed to upgrade elements prior to running any scripts.)
  var cePolyfill = window.CustomElements && !CustomElements.useNative;
  document.registerElement('dom-module', DomModule);

  function forceDomModulesUpgrade() {
    if (cePolyfill) {
      var script = document._currentScript || document.currentScript;
      var doc = script && script.ownerDocument || document;
      // find all dom-modules
      var modules = doc.querySelectorAll('dom-module');
      // minimize work by going backwards and stopping if we find an
      // upgraded module.
      for (var i= modules.length-1, m; (i >=0) && (m=modules[i]); i--) {
        if (m.__upgraded__) {
          return;
        } else {
          CustomElements.upgrade(m);
        }
      }
    }
  }

})();
Polymer.Base._addFeature({

    _prepIs: function() {
      if (!this.is) {
        var module =
          (document._currentScript || document.currentScript).parentNode;
        if (module.localName === 'dom-module') {
          var id = module.id || module.getAttribute('name')
            || module.getAttribute('is');
          this.is = id;
        }
      }
      if (this.is) {
        this.is = this.is.toLowerCase();
      }
    }

  });
/**
   * Automatically extend using objects referenced in `behaviors` array.
   *
   *     someBehaviorObject = {
   *       accessors: {
   *        value: {type: Number, observer: '_numberChanged'}
   *       },
   *       observers: [
   *         // ...
   *       ],
   *       ready: function() {
   *         // called before prototoype's ready
   *       },
   *       _numberChanged: function() {}
   *     };
   *
   *     Polymer({
   *
   *       behaviors: [
   *         someBehaviorObject
   *       ]
   *
   *       ...
   *
   *     });
   *
   * @class base feature: behaviors
   */

  Polymer.Base._addFeature({

    /**
     * Array of objects to extend this prototype with.
     *
     * Each entry in the array may specify either a behavior object or array
     * of behaviors.
     *
     * Each behavior object may define lifecycle callbacks, `properties`,
     * `hostAttributes`, `observers` and `listeners`.
     *
     * Lifecycle callbacks will be called for each behavior in the order given
     * in the `behaviors` array, followed by the callback on the prototype.
     * Additionally, any non-lifecycle functions on the behavior object are
     * mixed into the base prototype, such that same-named functions on the
     * prototype take precedence, followed by later behaviors over earlier
     * behaviors.
     */
    behaviors: [],

    _desugarBehaviors: function() {
      if (this.behaviors.length) {
        this.behaviors = this._desugarSomeBehaviors(this.behaviors);
      }
    },

    _desugarSomeBehaviors: function(behaviors) {
      var behaviorSet = [];
      // iteration 1
      behaviors = this._flattenBehaviorsList(behaviors);
      // iteration 2
      // traverse the behaviors in _reverse_ order (youngest first) because
      // `_mixinBehavior` has _first property wins_ behavior, this is done
      // to optimize # of calls to `_copyOwnProperty`
      for (var i=behaviors.length-1; i>=0; i--) {
        var b = behaviors[i];
        if (behaviorSet.indexOf(b) === -1) {
          this._mixinBehavior(b);
          behaviorSet.unshift(b);
        }
      }
      return behaviorSet;
    },

    _flattenBehaviorsList: function(behaviors) {
      var flat = [];
      for (var i=0; i < behaviors.length; i++) {
        var b = behaviors[i];
        if (b instanceof Array) {
          flat = flat.concat(this._flattenBehaviorsList(b));
        }
        // filter out null entries so other iterators don't need to check
        else if (b) {
          flat.push(b);
        } else {
          this._warn(this._logf('_flattenBehaviorsList', 'behavior is null, check for missing or 404 import'));
        }
      }
      return flat;
    },

    _mixinBehavior: function(b) {
      var n$ = Object.getOwnPropertyNames(b);
      for (var i=0, n; (i<n$.length) && (n=n$[i]); i++) {
        if (!Polymer.Base._behaviorProperties[n] && !this.hasOwnProperty(n)) {
          this.copyOwnProperty(n, b, this);
        }
      }
    },

    _prepBehaviors: function() {
      this._prepFlattenedBehaviors(this.behaviors);
    },

    _prepFlattenedBehaviors: function(behaviors) {
      // iteration 3
      // `_prepBehavior` goes in natural order
      // otherwise, it's a tricky detail for implementors of `_prepBehavior`
      for (var i=0, l=behaviors.length; i<l; i++) {
        this._prepBehavior(behaviors[i]);
      }
      // prep our prototype-as-behavior
      this._prepBehavior(this);
    },

    _doBehavior: function(name, args) {
      for (var i=0; i < this.behaviors.length; i++) {
        this._invokeBehavior(this.behaviors[i], name, args);
      }
      this._invokeBehavior(this, name, args);
    },

    _invokeBehavior: function(b, name, args) {
      var fn = b[name];
      if (fn) {
        fn.apply(this, args || Polymer.nar);
      }
    },

    _marshalBehaviors: function() {
      for (var i=0; i < this.behaviors.length; i++) {
        this._marshalBehavior(this.behaviors[i]);
      }
      this._marshalBehavior(this);
    }

  });

  // special properties on behaviors are not mixed in and are instead
  // either processed specially (e.g. listeners, properties) or available
  // for calling via doBehavior (e.g. created, ready)
  Polymer.Base._behaviorProperties = {
    hostAttributes: true,
    beforeRegister: true,
    registered: true,
    properties: true,
    observers: true,
    listeners: true,
    created: true,
    attached: true,
    detached: true,
    attributeChanged: true,
    ready: true
  };
/**
   * Support `extends` property (for type-extension only).
   *
   * If the mixin is String-valued, the corresponding Polymer module
   * is mixed in.
   *
   *     Polymer({
   *       is: 'pro-input',
   *       extends: 'input',
   *       ...
   *     });
   *
   * Type-extension objects are created using `is` notation in HTML, or via
   * the secondary argument to `document.createElement` (the type-extension
   * rules are part of the Custom Elements specification, not something
   * created by Polymer).
   *
   * Example:
   *
   *     <!-- right: creates a pro-input element -->
   *     <input is="pro-input">
   *
   *     <!-- wrong: creates an unknown element -->
   *     <pro-input>
   *
   *     <script>
   *        // right: creates a pro-input element
   *        var elt = document.createElement('input', 'pro-input');
   *
   *        // wrong: creates an unknown element
   *        var elt = document.createElement('pro-input');
   *     <\script>
   *
   *   @class base feature: extends
   */

  Polymer.Base._addFeature({

    _getExtendedPrototype: function(tag) {
      return this._getExtendedNativePrototype(tag);
    },

    _nativePrototypes: {}, // static

    _getExtendedNativePrototype: function(tag) {
      var p = this._nativePrototypes[tag];
      if (!p) {
        var np = this.getNativePrototype(tag);
        p = this.extend(Object.create(np), Polymer.Base);
        this._nativePrototypes[tag] = p;
      }
      return p;
    },

    /**
     * Returns the native element prototype for the tag specified.
     *
     * @method getNativePrototype
     * @param {string} tag  HTML tag name.
     * @return {Object} Native prototype for specified tag.
    */
    getNativePrototype: function(tag) {
      // TODO(sjmiles): sad necessity
      return Object.getPrototypeOf(document.createElement(tag));
    }

  });
/**
   * Generates a boilerplate constructor.
   * 
   *     XFoo = Polymer({
   *       is: 'x-foo'
   *     });
   *     ASSERT(new XFoo() instanceof XFoo);
   *  
   * You can supply a custom constructor on the prototype. But remember that 
   * this constructor will only run if invoked **manually**. Elements created
   * via `document.createElement` or from HTML _will not invoke this method_.
   * 
   * Instead, we reuse the concept of `constructor` for a factory method which 
   * can take arguments. 
   * 
   *     MyFoo = Polymer({
   *       is: 'my-foo',
   *       constructor: function(foo) {
   *         this.foo = foo;
   *       }
   *       ...
   *     });
   * 
   * @class base feature: constructor
   */

  Polymer.Base._addFeature({

    // registration-time

    _prepConstructor: function() {
      // support both possible `createElement` signatures
      this._factoryArgs = this.extends ? [this.extends, this.is] : [this.is];
      // thunk the constructor to delegate allocation to `createElement`
      var ctor = function() { 
        return this._factory(arguments); 
      };
      if (this.hasOwnProperty('extends')) {
        ctor.extends = this.extends; 
      }
      // ensure constructor is set. The `constructor` property is
      // not writable on Safari; note: Chrome requires the property
      // to be configurable.
      Object.defineProperty(this, 'constructor', {value: ctor, 
        writable: true, configurable: true});
      ctor.prototype = this;
    },

    _factory: function(args) {
      var elt = document.createElement.apply(document, this._factoryArgs);
      if (this.factoryImpl) {
        this.factoryImpl.apply(elt, args);
      }
      return elt;
    }

  });
/**
   * Define property metadata.
   *
   *     properties: {
   *       <property>: <Type || Object>,
   *       ...
   *     }
   *
   * Example:
   *
   *     properties: {
   *       // `foo` property can be assigned via attribute, will be deserialized to
   *       // the specified data-type. All `properties` properties have this behavior.
   *       foo: String,
   *
   *       // `bar` property has additional behavior specifiers.
   *       //   type: as above, type for (de-)serialization
   *       //   notify: true to send a signal when a value is set to this property
   *       //   reflectToAttribute: true to serialize the property to an attribute
   *       //   readOnly: if true, the property has no setter
   *       bar: {
   *         type: Boolean,
   *         notify: true
   *       }
   *     }
   *
   * By itself the properties feature doesn't do anything but provide property
   * information. Other features use this information to control behavior.
   *
   * The `type` information is used by the `attributes` feature to convert
   * String values in attributes to typed properties. The `bind` feature uses
   * property information to control property access.
   *
   * Marking a property as `notify` causes a change in the property to
   * fire a non-bubbling event called `<property>-changed`. Elements that
   * have enabled two-way binding to the property use this event to
   * observe changes.
   *
   * `readOnly` properties have a getter, but no setter. To set a read-only
   * property, use the private setter method `_set_<property>(value)`.
   *
   * @class base feature: properties
   */

  // null object
  Polymer.nob = Object.create(null);

  Polymer.Base._addFeature({

    /*
     * Object containing property configuration data, where keys are property
     * names and values are descriptor objects that configure Polymer features
     * for the property.  Valid fields in the property descriptor object are
     * as follows:
     *
     * * `type` - used to determine how to deserialize attribute value strings
     *    to JS properties.  By convention, this field takes a JS constructor
     *    for the type, such as `String` or `Boolean`.
     * * `value` - default value for the property.  The value may either be a
     *    primitive value, or a function that returns a value (which should be
     *    used for initializing Objects and Arrays to avoid shared objects on
     *    instances).
     * * `notify` - when `true`, configures the property to fire a non-bubbling
     *    event called `<property>-changed` for each change to the property.
     *    Elements that have enabled two-way binding to the property use this
     *    event to observe changes.
     * * `readOnly` - when `true` configures the property to have a getter, but
     *    no setter. To set a read-only property, use the private setter method
     *    `_set_<property>(value)`.
     * * `reflectToAttribute` - when `true` configures the property value to
     *    be serialized to a string and reflected to the attribute each time
     *    it changes.  This can impact performance, so it should be used
     *    only when reflecting the attribute value is important.
     * * `observer` - indicates the name of a function that should be called
     *    each time the property changes. `e.g.: `observer: 'valueChanged'
     * * `computed` - configures the property to be computed by a computing
     *    function each time one or more dependent properties change.
     *    `e.g.: `computed: 'computeValue(prop1, prop2)'
     *
     * Note: a shorthand may be used for the object descriptor when only the
     * type needs to be specified by using the type as the descriptor directly.
     */
    properties: {
    },

    /**
     * Returns a property descriptor object for the property specified.
     *
     * This method allows introspecting the configuration of a Polymer element's
     * properties as configured in its `properties` object.  Note, this method
     * normalizes shorthand forms of the `properties` object into longhand form.
     *
     * @method getPropertyInfo
     * @param {string} property Name of property to introspect.
     * @return {Object} Property descriptor for specified property.
    */
    // TODO(sorvell): This function returns the first property object found
    // and this is not the property info Polymer acts on for readOnly or type
    // This api should be combined with _propertyInfo.
    getPropertyInfo: function(property) {
      var info = this._getPropertyInfo(property, this.properties);
      if (!info) {
        for (var i=0; i < this.behaviors.length; i++) {
          info = this._getPropertyInfo(property, this.behaviors[i].properties);
          if (info) {
            return info;
          }
        }
      }
      return info || Polymer.nob;
    },

    _getPropertyInfo: function(property, properties) {
      var p = properties && properties[property];
      if (typeof(p) === 'function') {
        p = properties[property] = {
          type: p
        };
      }
      // Let users determine whether property was defined without null check
      if (p) {
        p.defined = true;
      }
      return p;
    },

    // union properties, behaviors.properties, and propertyEffects
    _prepPropertyInfo: function() {
      this._propertyInfo = {};
      for (var i=0; i < this.behaviors.length; i++) {
        this._addPropertyInfo(this._propertyInfo, this.behaviors[i].properties);
      }
      this._addPropertyInfo(this._propertyInfo, this.properties);
      this._addPropertyInfo(this._propertyInfo, this._propertyEffects);
    },

    // list of propertyInfo with {readOnly, type, attribute}
    _addPropertyInfo: function(target, source) {
      if (source) {
        var t, s;
        for (var i in source) {
          t = target[i];
          s = source[i];
          // optimization: avoid info'ing properties that are protected and
          // not read only since they are not needed for attributes or
          // configuration.
          if (i[0] === '_' && !s.readOnly) {
            continue;
          }
          if (!target[i]) {
            target[i] = {
              type: typeof(s) === 'function' ? s : s.type,
              readOnly: s.readOnly,
              attribute: Polymer.CaseMap.camelToDashCase(i)
            }
          } else {
            if (!t.type) {
              t.type = s.type;
            }
            if (!t.readOnly) {
              t.readOnly = s.readOnly;
            }
          }
        }
      }
    }

  });
Polymer.CaseMap = {

    _caseMap: {},
    _rx: {
      dashToCamel: /-[a-z]/g,
      camelToDash: /([A-Z])/g
    },

    dashToCamelCase: function(dash) {
      return this._caseMap[dash] || (
        this._caseMap[dash] = dash.indexOf('-') < 0 ? dash : dash.replace(this._rx.dashToCamel,
          function(m) {
            return m[1].toUpperCase();
          }
        )
      );
    },

    camelToDashCase: function(camel) {
      return this._caseMap[camel] || (
        this._caseMap[camel] = camel.replace(this._rx.camelToDash, '-$1').toLowerCase()
      );
    }

  };
/**
   * Support for `hostAttributes` property.
   *
   *     hostAttributes: {
   *       'aria-role': 'button',
   *       tabindex: 0
   *     }
   *
   * `hostAttributes` is an object containing attribute names as keys and static values
   * to set to attributes when the element is created.
   *
   * Support for mapping attributes to properties.
   *
   * Properties that are configured in `properties` with a type are mapped
   * to attributes.
   *
   * A value set in an attribute is deserialized into the specified
   * data-type and stored into the matching property.
   *
   * Example:
   *
   *     properties: {
   *       // values set to index attribute are converted to Number and propagated
   *       // to index property
   *       index: Number,
   *       // values set to label attribute are propagated to index property
   *       label: String
   *     }
   *
   * Types supported for deserialization:
   *
   * - Number
   * - Boolean
   * - String
   * - Object (JSON)
   * - Array (JSON)
   * - Date
   *
   * This feature implements `attributeChanged` to support automatic
   * propagation of attribute values at run-time. If you override
   * `attributeChanged` be sure to call this base class method
   * if you also want the standard behavior.
   *
   * @class base feature: attributes
   */

  Polymer.Base._addFeature({

    // prototype time
    _addHostAttributes: function(attributes) {
      if (!this._aggregatedAttributes) {
        this._aggregatedAttributes = {};
      }
      if (attributes) {
        this.mixin(this._aggregatedAttributes, attributes);
      }
    },

    // instance time
    _marshalHostAttributes: function() {
      if (this._aggregatedAttributes) {
        this._applyAttributes(this, this._aggregatedAttributes);
      }
    },

    /* apply attributes to node but avoid overriding existing values */
    _applyAttributes: function(node, attr$) {
      for (var n in attr$) {
        // NOTE: never allow 'class' to be set in hostAttributes
        // since shimming classes would make it work
        // inconsisently under native SD
        if (!this.hasAttribute(n) && (n !== 'class')) {
          var v = attr$[n];
          this.serializeValueToAttribute(v, n, this);
        }
      }
    },

    _marshalAttributes: function() {
      this._takeAttributesToModel(this);
    },

    _takeAttributesToModel: function(model) {
      if (this.hasAttributes()) {
        for (var i in this._propertyInfo) {
          var info = this._propertyInfo[i];
          if (this.hasAttribute(info.attribute)) {
            this._setAttributeToProperty(model, info.attribute, i, info);
          }
        }
      }
    },

    _setAttributeToProperty: function(model, attribute, property, info) {
      // Don't deserialize back to property if currently reflecting
      if (!this._serializing) {
        property = (property || Polymer.CaseMap.dashToCamelCase(attribute));
        // fallback to property lookup
        // TODO(sorvell): check for _propertyInfo existence because of dom-bind
        info = info || (this._propertyInfo && this._propertyInfo[property]);
        if (info && !info.readOnly) {
          var v = this.getAttribute(attribute);
          model[property] = this.deserialize(v, info.type);
        }
      }
    },

    _serializing: false,

    /**
     * Serializes a property to its associated attribute.
     *
     * Generally users should set `reflectToAttribute: true` in the
     * `properties` configuration to achieve automatic attribute reflection.
     *
     * @method reflectPropertyToAttribute
     * @param {string} property Property name to reflect.
     * @param {*=} attribute Attribute name to reflect.
     * @param {*=} value Property value to refect.
     */
    reflectPropertyToAttribute: function(property, attribute, value) {
      this._serializing = true;
      value = (value === undefined) ? this[property] : value;
      this.serializeValueToAttribute(value,
        attribute || Polymer.CaseMap.camelToDashCase(property));
      this._serializing = false;
    },

    /**
     * Sets a typed value to an HTML attribute on a node.
     *
     * This method calls the `serialize` method to convert the typed
     * value to a string.  If the `serialize` method returns `undefined`,
     * the attribute will be removed (this is the default for boolean
     * type `false`).
     *
     * @method serializeValueToAttribute
     * @param {*} value Value to serialize.
     * @param {string} attribute Attribute name to serialize to.
     * @param {Element=} node Element to set attribute to (defaults to this).
     */
    serializeValueToAttribute: function(value, attribute, node) {
      var str = this.serialize(value);
      // TODO(kschaaf): Consider enabling under a flag
      // if (str && str.length > 250) {
      //   this._warn(this._logf('serializeValueToAttribute',
      //     'serializing long attribute values can lead to poor performance', this));
      // }
      node = node || this;
      if (str === undefined) {
        node.removeAttribute(attribute);
      } else {
        node.setAttribute(attribute, str);
      }
    },

    /**
     * Converts a string to a typed value.
     *
     * This method is called by Polymer when reading HTML attribute values to
     * JS properties.  Users may override this method on Polymer element
     * prototypes to provide deserialization for custom `type`s.  Note,
     * the `type` argument is the value of the `type` field provided in the
     * `properties` configuration object for a given property, and is
     * by convention the constructor for the type to deserialize.
     *
     * Note: The return value of `undefined` is used as a sentinel value to
     * indicate the attribute should be removed.
     *
     * @method deserialize
     * @param {string} value Attribute value to deserialize.
     * @param {*} type Type to deserialize the string to.
     * @return {*} Typed value deserialized from the provided string.
     */
    deserialize: function(value, type) {
      switch (type) {
        case Number:
          value = Number(value);
          break;

        case Boolean:
          value = (value != null);
          break;

        case Object:
          try {
            value = JSON.parse(value);
          } catch(x) {
            // allow non-JSON literals like Strings and Numbers
          }
          break;

        case Array:
          try {
            value = JSON.parse(value);
          } catch(x) {
            value = null;
            console.warn('Polymer::Attributes: couldn`t decode Array as JSON');
          }
          break;

        case Date:
          value = new Date(value);
          break;

        case String:
        default:
          break;
      }
      return value;
    },

    /**
     * Converts a typed value to a string.
     *
     * This method is called by Polymer when setting JS property values to
     * HTML attributes.  Users may override this method on Polymer element
     * prototypes to provide serialization for custom types.
     *
     * @method serialize
     * @param {*} value Property value to serialize.
     * @return {string} String serialized from the provided property value.
     */
    serialize: function(value) {
      /* eslint-disable no-fallthrough */
      switch (typeof value) {
        case 'boolean':
          return value ? '' : undefined;

        case 'object':
          if (value instanceof Date) {
            return value.toString();
          } else if (value) {
            try {
              return JSON.stringify(value);
            } catch(x) {
              return '';
            }
          }

        default:
          return value != null ? value : undefined;
      }
    }
    /* eslint-enable no-fallthrough */
  });
Polymer.version = 'master';
Polymer.Base._addFeature({

    _registerFeatures: function() {
      // identity
      this._prepIs();
      // shared behaviors
      this._prepBehaviors();
      // factory
      this._prepConstructor();
      // fast access to property info
      this._prepPropertyInfo();
    },

    _prepBehavior: function(b) {
      this._addHostAttributes(b.hostAttributes);
    },

    _marshalBehavior: function(b) {
    },

    _initFeatures: function() {
      // install host attributes
      this._marshalHostAttributes();
      // acquire behaviors
      this._marshalBehaviors();
    }

  });
/**
   * Automatic template management.
   *
   * The `template` feature locates and instances a `<template>` element
   * corresponding to the current Polymer prototype.
   *
   * The `<template>` element may be immediately preceeding the script that
   * invokes `Polymer()`.
   *
   * @class standard feature: template
   */

  Polymer.Base._addFeature({

    _prepTemplate: function() {
      // locate template using dom-module
      if (this._template === undefined) {
        this._template = Polymer.DomModule.import(this.is, 'template');
      }
      // stick finger in footgun
      if (this._template && this._template.hasAttribute('is')) {
        this._warn(this._logf('_prepTemplate', 'top-level Polymer template ' +
          'must not be a type-extension, found', this._template,
          'Move inside simple <template>.'));
      }
      // bootstrap the template if it has not already been
      if (this._template && !this._template.content &&
          window.HTMLTemplateElement && HTMLTemplateElement.decorate) {
        HTMLTemplateElement.decorate(this._template);
      }
    },

    _stampTemplate: function() {
      if (this._template) {
        // note: root is now a fragment which can be manipulated
        // while not attached to the element.
        this.root = this.instanceTemplate(this._template);
      }
    },

    /**
     * Calls `importNode` on the `content` of the `template` specified and
     * returns a document fragment containing the imported content.
     *
     * @method instanceTemplate
     * @param {HTMLTemplateElement} template HTML template element to instance.
     * @return {DocumentFragment} Document fragment containing the imported
     *   template content.
    */
    instanceTemplate: function(template) {
      var dom =
        document.importNode(template._content || template.content, true);
      return dom;
    }

  });
/**
   * Provides `ready` lifecycle callback which is called parent to child.
   *
   * This can be useful in a number of cases. Here are some examples:
   *
   * Setting a default property value that should have a side effect: To ensure
   * the side effect, an element must set a default value no sooner than
   * `created`; however, since `created` flows child to host, this is before the
   * host has had a chance to set a property value on the child. The `ready`
   * method solves this problem since it's called host to child.
   *
   * Dom distribution: To support reprojection efficiently, it's important to
   * distribute from host to child in one shot. The `attachedCallback` mostly
   * goes in the desired order except for elements that are in dom to start; in
   * this case, all children are attached before the host element. Ready also
   * addresses this case since it's guaranteed to be called host to child.
   *
   * @class standard feature: ready
   */

(function() {

  var baseAttachedCallback = Polymer.Base.attachedCallback;

  Polymer.Base._addFeature({

    _hostStack: [],

    /**
     * Lifecycle callback invoked when all local DOM children of this element
     * have been created and "configured" with data bound from this element,
     * attribute values, or defaults.
     *
     * @method ready
     */
    ready: function() {
    },

    // NOTE: The concept of 'host' is overloaded. There are two different
    // notions:
    // 1. an element hosts the elements in its local dom root.
    // 2. an element hosts the elements on which it configures data.
    // Practially, these notions are almost always coincident.
    // Some special elements like templates may separate them.
    // In order not to over-emphaisize this technical difference, we expose
    // one concept to the user and it maps to the dom-related meaning of host.
    //
    // set this element's `host` and push this element onto the `host`'s
    // list of `client` elements
    // this.dataHost reflects the parent element who manages
    // any bindings for the element.  Only elements originally
    // stamped from Polymer templates have a dataHost, and this
    // never changes
    _registerHost: function(host) {
      // NOTE: The `dataHost` of an element never changes.
      this.dataHost = host = host || 
        Polymer.Base._hostStack[Polymer.Base._hostStack.length-1];
      if (host && host._clients) {
        host._clients.push(this);
      }
      this._clients = null;
      this._clientsReadied = false;
    },

    // establish this element as the current hosting element (allows
    // any elements we stamp to easily set host to us).
    _beginHosting: function() {
      Polymer.Base._hostStack.push(this);
      if (!this._clients) {
        this._clients = [];
      }
    },

    _endHosting: function() {
      // this element is no longer the current hosting element
      Polymer.Base._hostStack.pop();
    },

    _tryReady: function() {
      this._readied = false;
      if (this._canReady()) {
        this._ready();
      }
    },

    _canReady: function() {
      return !this.dataHost || this.dataHost._clientsReadied;
    },

    _ready: function() {
      // extension point
      this._beforeClientsReady();
      if (this._template) {
        // prepare root
        this._setupRoot();
        this._readyClients();
      }
      this._clientsReadied = true;
      this._clients = null;
      // extension point
      this._afterClientsReady();
      this._readySelf();
    },

    _readyClients: function() {
      // logically distribute self
      this._beginDistribute();
      // now fully prepare localChildren
      var c$ = this._clients;
      if (c$) {
        for (var i=0, l= c$.length, c; (i<l) && (c=c$[i]); i++) {
          c._ready();
        }
      }
      // perform actual dom composition
      this._finishDistribute();
      // ensure elements are attached if they are in the dom at ready time
      // helps normalize attached ordering between native and polyfill ce.
      // TODO(sorvell): worth perf cost? ~6%
      // if (!Polymer.Settings.useNativeCustomElements) {
      //   CustomElements.takeRecords();
      // }
    },

    // mark readied and call `ready`
    // note: called localChildren -> host
    _readySelf: function() {
      this._doBehavior('ready');
      this._readied = true;
      if (this._attachedPending) {
        this._attachedPending = false;
        this.attachedCallback();
      }
    },

    // for system overriding
    _beforeClientsReady: function() {},
    _afterClientsReady: function() {},
    _beforeAttached: function() {},

    /**
     * Polymer library implementation of the Custom Elements `attachedCallback`.
     *
     * Note, users should not override `attachedCallback`, and instead should
     * implement the `attached` method on Polymer elements to receive
     * attached-time callbacks.
     *
     * @protected
     */
    attachedCallback: function() {
      if (this._readied) {
        this._beforeAttached();
        baseAttachedCallback.call(this);
      } else {
        this._attachedPending = true;
      }
    }

  });

})();
Polymer.ArraySplice = (function() {

  function newSplice(index, removed, addedCount) {
    return {
      index: index,
      removed: removed,
      addedCount: addedCount
    };
  }

  var EDIT_LEAVE = 0;
  var EDIT_UPDATE = 1;
  var EDIT_ADD = 2;
  var EDIT_DELETE = 3;

  function ArraySplice() {}

  ArraySplice.prototype = {

    // Note: This function is *based* on the computation of the Levenshtein
    // "edit" distance. The one change is that "updates" are treated as two
    // edits - not one. With Array splices, an update is really a delete
    // followed by an add. By retaining this, we optimize for "keeping" the
    // maximum array items in the original array. For example:
    //
    //   'xxxx123' -> '123yyyy'
    //
    // With 1-edit updates, the shortest path would be just to update all seven
    // characters. With 2-edit updates, we delete 4, leave 3, and add 4. This
    // leaves the substring '123' intact.
    calcEditDistances: function(current, currentStart, currentEnd,
                                old, oldStart, oldEnd) {
      // "Deletion" columns
      var rowCount = oldEnd - oldStart + 1;
      var columnCount = currentEnd - currentStart + 1;
      var distances = new Array(rowCount);

      // "Addition" rows. Initialize null column.
      for (var i = 0; i < rowCount; i++) {
        distances[i] = new Array(columnCount);
        distances[i][0] = i;
      }

      // Initialize null row
      for (var j = 0; j < columnCount; j++)
        distances[0][j] = j;

      for (i = 1; i < rowCount; i++) {
        for (j = 1; j < columnCount; j++) {
          if (this.equals(current[currentStart + j - 1], old[oldStart + i - 1]))
            distances[i][j] = distances[i - 1][j - 1];
          else {
            var north = distances[i - 1][j] + 1;
            var west = distances[i][j - 1] + 1;
            distances[i][j] = north < west ? north : west;
          }
        }
      }

      return distances;
    },

    // This starts at the final weight, and walks "backward" by finding
    // the minimum previous weight recursively until the origin of the weight
    // matrix.
    spliceOperationsFromEditDistances: function(distances) {
      var i = distances.length - 1;
      var j = distances[0].length - 1;
      var current = distances[i][j];
      var edits = [];
      while (i > 0 || j > 0) {
        if (i == 0) {
          edits.push(EDIT_ADD);
          j--;
          continue;
        }
        if (j == 0) {
          edits.push(EDIT_DELETE);
          i--;
          continue;
        }
        var northWest = distances[i - 1][j - 1];
        var west = distances[i - 1][j];
        var north = distances[i][j - 1];

        var min;
        if (west < north)
          min = west < northWest ? west : northWest;
        else
          min = north < northWest ? north : northWest;

        if (min == northWest) {
          if (northWest == current) {
            edits.push(EDIT_LEAVE);
          } else {
            edits.push(EDIT_UPDATE);
            current = northWest;
          }
          i--;
          j--;
        } else if (min == west) {
          edits.push(EDIT_DELETE);
          i--;
          current = west;
        } else {
          edits.push(EDIT_ADD);
          j--;
          current = north;
        }
      }

      edits.reverse();
      return edits;
    },

    /**
     * Splice Projection functions:
     *
     * A splice map is a representation of how a previous array of items
     * was transformed into a new array of items. Conceptually it is a list of
     * tuples of
     *
     *   <index, removed, addedCount>
     *
     * which are kept in ascending index order of. The tuple represents that at
     * the |index|, |removed| sequence of items were removed, and counting forward
     * from |index|, |addedCount| items were added.
     */

    /**
     * Lacking individual splice mutation information, the minimal set of
     * splices can be synthesized given the previous state and final state of an
     * array. The basic approach is to calculate the edit distance matrix and
     * choose the shortest path through it.
     *
     * Complexity: O(l * p)
     *   l: The length of the current array
     *   p: The length of the old array
     */
    calcSplices: function(current, currentStart, currentEnd,
                          old, oldStart, oldEnd) {
      var prefixCount = 0;
      var suffixCount = 0;

      var minLength = Math.min(currentEnd - currentStart, oldEnd - oldStart);
      if (currentStart == 0 && oldStart == 0)
        prefixCount = this.sharedPrefix(current, old, minLength);

      if (currentEnd == current.length && oldEnd == old.length)
        suffixCount = this.sharedSuffix(current, old, minLength - prefixCount);

      currentStart += prefixCount;
      oldStart += prefixCount;
      currentEnd -= suffixCount;
      oldEnd -= suffixCount;

      if (currentEnd - currentStart == 0 && oldEnd - oldStart == 0)
        return [];

      if (currentStart == currentEnd) {
        var splice = newSplice(currentStart, [], 0);
        while (oldStart < oldEnd)
          splice.removed.push(old[oldStart++]);

        return [ splice ];
      } else if (oldStart == oldEnd)
        return [ newSplice(currentStart, [], currentEnd - currentStart) ];

      var ops = this.spliceOperationsFromEditDistances(
          this.calcEditDistances(current, currentStart, currentEnd,
                                 old, oldStart, oldEnd));

      splice = undefined;
      var splices = [];
      var index = currentStart;
      var oldIndex = oldStart;
      for (var i = 0; i < ops.length; i++) {
        switch(ops[i]) {
          case EDIT_LEAVE:
            if (splice) {
              splices.push(splice);
              splice = undefined;
            }

            index++;
            oldIndex++;
            break;
          case EDIT_UPDATE:
            if (!splice)
              splice = newSplice(index, [], 0);

            splice.addedCount++;
            index++;

            splice.removed.push(old[oldIndex]);
            oldIndex++;
            break;
          case EDIT_ADD:
            if (!splice)
              splice = newSplice(index, [], 0);

            splice.addedCount++;
            index++;
            break;
          case EDIT_DELETE:
            if (!splice)
              splice = newSplice(index, [], 0);

            splice.removed.push(old[oldIndex]);
            oldIndex++;
            break;
        }
      }

      if (splice) {
        splices.push(splice);
      }
      return splices;
    },

    sharedPrefix: function(current, old, searchLength) {
      for (var i = 0; i < searchLength; i++)
        if (!this.equals(current[i], old[i]))
          return i;
      return searchLength;
    },

    sharedSuffix: function(current, old, searchLength) {
      var index1 = current.length;
      var index2 = old.length;
      var count = 0;
      while (count < searchLength && this.equals(current[--index1], old[--index2]))
        count++;

      return count;
    },

    calculateSplices: function(current, previous) {
      return this.calcSplices(current, 0, current.length, previous, 0,
                              previous.length);
    },

    equals: function(currentValue, previousValue) {
      return currentValue === previousValue;
    }
  };

  return new ArraySplice();

})();
Polymer.domInnerHTML = (function() {

  // Cribbed from ShadowDOM polyfill
  // https://github.com/webcomponents/webcomponentsjs/blob/master/src/ShadowDOM/wrappers/HTMLElement.js#L28
  /////////////////////////////////////////////////////////////////////////////
  // innerHTML and outerHTML

  // http://www.whatwg.org/specs/web-apps/current-work/multipage/the-end.html#escapingString
  var escapeAttrRegExp = /[&\u00A0"]/g;
  var escapeDataRegExp = /[&\u00A0<>]/g;

  function escapeReplace(c) {
    switch (c) {
      case '&':
        return '&amp;';
      case '<':
        return '&lt;';
      case '>':
        return '&gt;';
      case '"':
        return '&quot;';
      case '\u00A0':
        return '&nbsp;';
    }
  }

  function escapeAttr(s) {
    return s.replace(escapeAttrRegExp, escapeReplace);
  }

  function escapeData(s) {
    return s.replace(escapeDataRegExp, escapeReplace);
  }

  function makeSet(arr) {
    var set = {};
    for (var i = 0; i < arr.length; i++) {
      set[arr[i]] = true;
    }
    return set;
  }

  // http://www.whatwg.org/specs/web-apps/current-work/#void-elements
  var voidElements = makeSet([
    'area',
    'base',
    'br',
    'col',
    'command',
    'embed',
    'hr',
    'img',
    'input',
    'keygen',
    'link',
    'meta',
    'param',
    'source',
    'track',
    'wbr'
  ]);

  var plaintextParents = makeSet([
    'style',
    'script',
    'xmp',
    'iframe',
    'noembed',
    'noframes',
    'plaintext',
    'noscript'
  ]);

  function getOuterHTML(node, parentNode, composed) {
    switch (node.nodeType) {
      case Node.ELEMENT_NODE:
        //var tagName = node.tagName.toLowerCase();
        var tagName = node.localName;
        var s = '<' + tagName;
        var attrs = node.attributes;
        for (var i = 0, attr; (attr = attrs[i]); i++) {
          s += ' ' + attr.name + '="' + escapeAttr(attr.value) + '"';
        }
        s += '>';
        if (voidElements[tagName]) {
          return s;
        }
        return s + getInnerHTML(node, composed) + '</' + tagName + '>';
      case Node.TEXT_NODE:
        var data = node.data;
        if (parentNode && plaintextParents[parentNode.localName]) {
          return data;
        }
        return escapeData(data);
      case Node.COMMENT_NODE:
        return '<!--' + node.data + '-->';
      default:
        console.error(node);
        throw new Error('not implemented');
    }
  }

  function getInnerHTML(node, composed) {
    if (node instanceof HTMLTemplateElement)
      node = node.content;
    var s = '';
    var c$ = Polymer.dom(node).childNodes;
    for (var i=0, l=c$.length, child; (i<l) && (child=c$[i]); i++) {
      s += getOuterHTML(child, node, composed);
    }
    return s;
  }

  return {
    getInnerHTML: getInnerHTML
  };

})();
(function() {

  'use strict';

  // native add/remove
  var nativeInsertBefore = Element.prototype.insertBefore;
  var nativeAppendChild = Element.prototype.appendChild;
  var nativeRemoveChild = Element.prototype.removeChild;

  /**
   * TreeApi is a dom manipulation library used by Shady/Polymer.dom to
   * manipulate composed and logical trees.
   */
  Polymer.TreeApi = {

    // sad but faster than slice...
    arrayCopyChildNodes: function(parent) {
      var copy=[], i=0;
      for (var n=parent.firstChild; n; n=n.nextSibling) {
        copy[i++] = n;
      }
      return copy;
    },

    arrayCopyChildren: function(parent) {
      var copy=[], i=0;
      for (var n=parent.firstElementChild; n; n=n.nextElementSibling) {
        copy[i++] = n;
      }
      return copy;
    },

    arrayCopy: function(a$) {
      var l = a$.length;
      var copy = new Array(l);
      for (var i=0; i < l; i++) {
        copy[i] = a$[i];
      }
      return copy;
    }

  };

  Polymer.TreeApi.Logical = {

    hasParentNode: function(node) {
      return Boolean(node.__dom && node.__dom.parentNode);
    },

    hasChildNodes: function(node) {
      return Boolean(node.__dom && node.__dom.childNodes !== undefined);
    },

    getChildNodes: function(node) {
      // note: we're distinguishing here between undefined and false-y:
      // hasChildNodes uses undefined check to see if this element has logical
      // children; the false-y check indicates whether or not we should rebuild
      // the cached childNodes array.
      return this.hasChildNodes(node) ? this._getChildNodes(node) :
        node.childNodes;
    },

    _getChildNodes: function(node) {
      if (!node.__dom.childNodes) {
        node.__dom.childNodes = [];
        for (var n=node.__dom.firstChild; n; n=n.__dom.nextSibling) {
          node.__dom.childNodes.push(n);
        }
      }
      return node.__dom.childNodes;
    },

    // NOTE: __dom can be created under 2 conditions: (1) an element has a
    // logical tree, or (2) an element is in a logical tree. In case (1), the
    // element will store firstChild/lastChild, and in case (2), the element
    // will store parentNode, nextSibling, previousSibling. This means that
    // the mere existence of __dom is not enough to know if the requested
    // logical data is available and instead we do an explicit undefined check.
    getParentNode: function(node) {
      return node.__dom && node.__dom.parentNode !== undefined ?
        node.__dom.parentNode : node.parentNode;
    },

    getFirstChild: function(node) {
      return node.__dom && node.__dom.firstChild !== undefined ?
        node.__dom.firstChild : node.firstChild;
    },

    getLastChild: function(node) {
      return node.__dom && node.__dom.lastChild  !== undefined ?
        node.__dom.lastChild : node.lastChild;
    },

    getNextSibling: function(node) {
      return node.__dom && node.__dom.nextSibling  !== undefined ?
        node.__dom.nextSibling : node.nextSibling;
    },

    getPreviousSibling: function(node) {
      return node.__dom && node.__dom.previousSibling  !== undefined ?
        node.__dom.previousSibling : node.previousSibling;
    },

    getFirstElementChild: function(node) {
      return node.__dom && node.__dom.firstChild !== undefined ?
        this._getFirstElementChild(node) : node.firstElementChild;
    },

    _getFirstElementChild: function(node) {
      var n = node.__dom.firstChild;
      while (n && n.nodeType !== Node.ELEMENT_NODE) {
        n = n.__dom.nextSibling;
      }
      return n;
    },

    getLastElementChild: function(node) {
      return node.__dom && node.__dom.lastChild !== undefined ?
        this._getLastElementChild(node) : node.lastElementChild;
    },

    _getLastElementChild: function(node) {
      var n = node.__dom.lastChild;
      while (n && n.nodeType !== Node.ELEMENT_NODE) {
        n = n.__dom.previousSibling;
      }
      return n;
    },

    getNextElementSibling: function(node) {
      return node.__dom && node.__dom.nextSibling !== undefined ?
        this._getNextElementSibling(node) : node.nextElementSibling;
    },

    _getNextElementSibling: function(node) {
      var n = node.__dom.nextSibling;
      while (n && n.nodeType !== Node.ELEMENT_NODE) {
        n = n.__dom.nextSibling;
      }
      return n;
    },

    getPreviousElementSibling: function(node) {
      return node.__dom && node.__dom.previousSibling !== undefined ?
        this._getPreviousElementSibling(node) : node.previousElementSibling;
    },

    _getPreviousElementSibling: function(node) {
      var n = node.__dom.previousSibling;
      while (n && n.nodeType !== Node.ELEMENT_NODE) {
        n = n.__dom.previousSibling;
      }
      return n;
    },

    // Capture the list of light children. It's important to do this before we
    // start transforming the DOM into "rendered" state.
    // Children may be added to this list dynamically. It will be treated as the
    // source of truth for the light children of the element. This element's
    // actual children will be treated as the rendered state once this function
    // has been called.
    saveChildNodes: function(node) {
      if (!this.hasChildNodes(node)) {
        node.__dom = node.__dom || {};
        node.__dom.firstChild = node.firstChild;
        node.__dom.lastChild = node.lastChild;
        node.__dom.childNodes = [];
        for (var n=node.firstChild; n; n=n.nextSibling) {
          n.__dom = n.__dom || {};
          n.__dom.parentNode = node;
          node.__dom.childNodes.push(n);
          n.__dom.nextSibling = n.nextSibling;
          n.__dom.previousSibling = n.previousSibling;
        }
      }
    },

    recordInsertBefore: function(node, container, ref_node) {
      container.__dom.childNodes = null;
      // handle document fragments
      if (node.nodeType === Node.DOCUMENT_FRAGMENT_NODE) {
        // TODO(sorvell): remember this for patching:
        // the act of setting this info can affect patched nodes
        // getters; therefore capture childNodes before patching.
        for (var n=node.firstChild; n; n=n.nextSibling) {
          this._linkNode(n, container, ref_node);
        }
      } else {
        this._linkNode(node, container, ref_node);
      }
    },

    _linkNode: function(node, container, ref_node) {
      node.__dom = node.__dom || {};
      container.__dom = container.__dom || {};
      if (ref_node) {
        ref_node.__dom = ref_node.__dom || {};
      }
      // update ref_node.previousSibling <-> node
      node.__dom.previousSibling = ref_node ? ref_node.__dom.previousSibling :
        container.__dom.lastChild;
      if (node.__dom.previousSibling) {
        node.__dom.previousSibling.__dom.nextSibling = node;
      }
      // update node <-> ref_node
      node.__dom.nextSibling = ref_node;
      if (node.__dom.nextSibling) {
        node.__dom.nextSibling.__dom.previousSibling = node;
      }
      // update node <-> container
      node.__dom.parentNode = container;
      if (ref_node) {
        if (ref_node === container.__dom.firstChild) {
          container.__dom.firstChild = node;
        }
      } else {
        container.__dom.lastChild = node;
        if (!container.__dom.firstChild) {
          container.__dom.firstChild = node;
        }
      }
      // remove caching of childNodes
      container.__dom.childNodes = null;
    },

    recordRemoveChild: function(node, container) {
      node.__dom = node.__dom || {};
      container.__dom = container.__dom || {};
      if (node === container.__dom.firstChild) {
        container.__dom.firstChild = node.__dom.nextSibling;
      }
      if (node === container.__dom.lastChild) {
        container.__dom.lastChild = node.__dom.previousSibling;
      }
      var p = node.__dom.previousSibling;
      var n = node.__dom.nextSibling;
      if (p) {
        p.__dom.nextSibling = n;
      }
      if (n) {
        n.__dom.previousSibling = p;
      }
      // When an element is removed, logical data is no longer tracked.
      // Explicitly set `undefined` here to indicate this. This is disginguished
      // from `null` which is set if info is null.
      node.__dom.parentNode = node.__dom.previousSibling =
        node.__dom.nextSibling = undefined;
      // remove caching of childNodes
      container.__dom.childNodes = null;
    }

  }

  // TODO(sorvell): composed tree manipulation is made available
  // (1) to maninpulate the composed tree, and (2) to track changes
  // to the tree for optional patching pluggability.
  Polymer.TreeApi.Composed = {

    getChildNodes: function(node) {
      return Polymer.TreeApi.arrayCopyChildNodes(node);
    },

    getParentNode: function(node) {
      return node.parentNode;
    },

    // composed tracking needs to reset composed children here in case
    // they may have already been set (this shouldn't happen but can
    // if dependency ordering is incorrect and as a result upgrade order
    // is unexpected)
    clearChildNodes: function(node) {
      node.textContent = '';
    },

    insertBefore: function(parentNode, newChild, refChild) {
      return nativeInsertBefore.call(parentNode, newChild, refChild || null);
    },

    appendChild: function(parentNode, newChild) {
      return nativeAppendChild.call(parentNode, newChild);
    },

    removeChild: function(parentNode, node) {
      return nativeRemoveChild.call(parentNode, node);
    }

  };

})();
/**
   * DomApi is a dom manipulation library which is compatible with both
   * Shady DOM and Shadow DOM. The general usage is
   * `Polymer.dom(node).method(arguments)` where methods and arguments
   * match native DOM where possible.
   */
  Polymer.DomApi = (function() {
    'use strict';

    var Settings = Polymer.Settings;
    var TreeApi = Polymer.TreeApi;

    var DomApi = function(node) {
      this.node = needsToWrap ? DomApi.wrap(node) : node;
    };

    // ensure nodes are wrapped if SD polyfill is present
    var needsToWrap = Settings.hasShadow && !Settings.nativeShadow;
    DomApi.wrap = window.wrap ? window.wrap : function(node) { return node; };

    DomApi.prototype = {

      flush: function() {
        Polymer.dom.flush();
      },

      /**
       * Check that the given node is a descendant of `this`,
       * ignoring ShadowDOM boundaries
       * @param {Node} node
       * @return {Boolean} true if `node` is a descendant or equal to `this`
       */
      deepContains: function(node) {
        // fast path, use shallow `contains`.
        if (this.node.contains(node)) {
          return true;
        }
        var n = node;
        var doc = node.ownerDocument;
        // walk from node to `this` or `document`
        while (n && n !== doc && n !== this.node) {
          // use logical parentnode, or native ShadowRoot host
          n = Polymer.dom(n).parentNode || n.host;
        }
        return n === this.node;
      },

      /*
        Returns a list of nodes distributed within this element. These can be
        dom children or elements distributed to children that are insertion
        points.
      */
      queryDistributedElements: function(selector) {
        var c$ = this.getEffectiveChildNodes();
        var list = [];
        for (var i=0, l=c$.length, c; (i<l) && (c=c$[i]); i++) {
          if ((c.nodeType === Node.ELEMENT_NODE) &&
              DomApi.matchesSelector.call(c, selector)) {
            list.push(c);
          }
        }
        return list;
      },

      /*
        Returns a list of effective childNoes within this element. These can be
        dom child nodes or elements distributed to children that are insertion
        points.
      */
      getEffectiveChildNodes: function() {
        var list = [];
        var c$ = this.childNodes;
        for (var i=0, l=c$.length, c; (i<l) && (c=c$[i]); i++) {
          if (c.localName === CONTENT) {
            var d$ = dom(c).getDistributedNodes();
            for (var j=0; j < d$.length; j++) {
              list.push(d$[j]);
            }
          } else {
            list.push(c);
          }
        }
        return list;
      },

      /**
       * Notifies callers about changes to the element's effective child nodes,
       * the same list as returned by `getEffectiveChildNodes`.
       * @param {function} callback The supplied callback is called with an
       * `info` argument which is an object that provides
       * the `target` on which the changes occurred, a list of any nodes
       * added in the `addedNodes` array, and nodes removed in the
       * `removedNodes` array.
       * @return {object} Returns a handle which is the argument to
       * `unobserveNodes`.
       */
      observeNodes: function(callback) {
        if (callback) {
          if (!this.observer) {
            this.observer = this.node.localName === CONTENT ?
              new DomApi.DistributedNodesObserver(this) :
              new DomApi.EffectiveNodesObserver(this);
          }
          return this.observer.addListener(callback);
        }
      },

      /**
       * Stops observing changes to the element's effective child nodes.
       * @param {object} handle The handle for the callback that should
       * no longer receive notifications. This handle is returned from
       * `observeNodes`.
       */
      unobserveNodes: function(handle) {
        if (this.observer) {
          this.observer.removeListener(handle);
        }
      },

      notifyObserver: function() {
        if (this.observer) {
          this.observer.notify();
        }
      },

      // NOTE: `_query` is used primarily for ShadyDOM's querySelector impl,
      // but it's also generally useful to recurse through the element tree
      // and is used by Polymer's styling system. 
      _query: function(matcher, node, halter) {
        node = node || this.node;
        var list = [];
        this._queryElements(TreeApi.Logical.getChildNodes(node), matcher, 
          halter, list);
        return list;
      },

      _queryElements: function(elements, matcher, halter, list) {
        for (var i=0, l=elements.length, c; (i<l) && (c=elements[i]); i++) {
          if (c.nodeType === Node.ELEMENT_NODE) {
            if (this._queryElement(c, matcher, halter, list)) {
              return true;
            }
          }
        }
      },

      _queryElement: function(node, matcher, halter, list) {
        var result = matcher(node);
        if (result) {
          list.push(node);
        }
        if (halter && halter(result)) {
          return result;
        }
        this._queryElements(TreeApi.Logical.getChildNodes(node), matcher, 
          halter, list);
      }

    };

    var CONTENT = DomApi.CONTENT = 'content';

    var dom = DomApi.factory = function(node) {
      node = node || document;
      if (!node.__domApi) {
        node.__domApi = new DomApi.ctor(node);
      }
      return node.__domApi;
    };

    DomApi.hasApi = function(node) {
      return Boolean(node.__domApi);
    };

    DomApi.ctor = DomApi;

    Polymer.dom = function(obj, patch) {
      if (obj instanceof Event) {
        return Polymer.EventApi.factory(obj);
      } else {
        return DomApi.factory(obj, patch);
      }
    };

    var p = Element.prototype;
    DomApi.matchesSelector = p.matches || p.matchesSelector ||
      p.mozMatchesSelector || p.msMatchesSelector ||
      p.oMatchesSelector || p.webkitMatchesSelector;

    return DomApi;

  })();
(function() {
  'use strict';

  var Settings = Polymer.Settings;
  var DomApi = Polymer.DomApi;
  var dom = DomApi.factory;
  var TreeApi = Polymer.TreeApi;
  var getInnerHTML = Polymer.domInnerHTML.getInnerHTML;
  var CONTENT = DomApi.CONTENT;

  // *************** Configure DomApi for Shady DOM!! ***************
  if (Settings.useShadow) {
    return;
  }

  var nativeCloneNode = Element.prototype.cloneNode;
  var nativeImportNode = Document.prototype.importNode;

  Polymer.Base.extend(DomApi.prototype, {

    _lazyDistribute: function(host) {
      // note: only try to distribute if the root is not clean; this ensures
      // we don't distribute before initial distribution
      if (host.shadyRoot && host.shadyRoot._distributionClean) {
        host.shadyRoot._distributionClean = false;
        Polymer.dom.addDebouncer(host.debounce('_distribute',
          host._distributeContent));
      }
    },

    appendChild: function(node) {
      return this.insertBefore(node);
    },

    // cases in which we may not be able to just do standard native call
    // 1. container has a shadyRoot (needsDistribution IFF the shadyRoot
    // has an insertion point)
    // 2. container is a shadyRoot (don't distribute, instead set
    // container to container.host.
    // 3. node is <content> (host of container needs distribution)
    insertBefore: function(node, ref_node) {
      if (ref_node && TreeApi.Logical.getParentNode(ref_node) !== this.node) {
        throw Error('The ref_node to be inserted before is not a child ' +
          'of this node');
      }
      // remove node from its current position iff it's in a tree.
      if (node.nodeType !== Node.DOCUMENT_FRAGMENT_NODE) {
        var parent = TreeApi.Logical.getParentNode(node);
        // notify existing parent that this node is being removed.
        if (parent) {
          if (DomApi.hasApi(parent)) {
            dom(parent).notifyObserver();
          }
          this._removeNode(node);
        } else {
          this._removeOwnerShadyRoot(node);
        }
      }
      if (!this._addNode(node, ref_node)) {
        if (ref_node) {
          // if ref_node is <content> replace with first distributed node
          ref_node = ref_node.localName === CONTENT ?
            this._firstComposedNode(ref_node) : ref_node;
        }
        // if adding to a shadyRoot, add to host instead
        var container = this.node._isShadyRoot ? this.node.host : this.node;
        if (ref_node) {
          TreeApi.Composed.insertBefore(container, node, ref_node);
        } else {
          TreeApi.Composed.appendChild(container, node);
        }
      }
      this.notifyObserver();
      return node;
    },

    // Try to add node. Record logical info, track insertion points, perform
    // distribution iff needed. Return true if the add is handled.
    _addNode: function(node, ref_node) {
      var root = this.getOwnerRoot();
      if (root) {
        // note: we always need to see if an insertion point is added
        // since this saves logical tree info; however, invalidation state
        // needs
        var ipAdded = this._maybeAddInsertionPoint(node, this.node);
        // invalidate insertion points IFF not already invalid!
        if (!root._invalidInsertionPoints) {
          root._invalidInsertionPoints = ipAdded;
        }
        this._addNodeToHost(root.host, node);
      }
      if (TreeApi.Logical.hasChildNodes(this.node)) {
        TreeApi.Logical.recordInsertBefore(node, this.node, ref_node);
      }
      // if not distributing and not adding to host, do a fast path addition
      var handled = this._maybeDistribute(node) ||
        this.node.shadyRoot;
      // if shady is handling this node,
      // the actual dom may not be removed if the node or fragment contents
      // remain undistributed so we ensure removal here.
      // NOTE: we only remove from existing location iff shady dom is involved.
      // This is because a node fragment is passed to the native add method
      // which expects to see fragment children. Regular elements must also
      // use this check because not doing so causes separation of
      // attached/detached and breaks, for example,
      // dom-if's attached/detached checks.
      if (handled) {
        if (node.nodeType === Node.DOCUMENT_FRAGMENT_NODE) {
          while (node.firstChild) {
            TreeApi.Composed.removeChild(node, node.firstChild);
          }
        } else {
          var parent = TreeApi.Composed.getParentNode(node);
          if (parent) {
            TreeApi.Composed.removeChild(parent, node);
          }
        }
      }
      return handled;
    },

    /**
      Removes the given `node` from the element's `lightChildren`.
      This method also performs dom composition.
    */
    removeChild: function(node) {
      if (TreeApi.Logical.getParentNode(node) !== this.node) {
        throw Error('The node to be removed is not a child of this node: ' +
          node);
      }
      if (!this._removeNode(node)) {
        // if removing from a shadyRoot, remove form host instead
        var container = this.node._isShadyRoot ? this.node.host : this.node;
        // not guaranteed to physically be in container; e.g.
        // undistributed nodes.
        var parent = TreeApi.Composed.getParentNode(node);
        if (container === parent) {
          TreeApi.Composed.removeChild(container, node);
        }
      }
      this.notifyObserver();
      return node;
    },

    // Try to remove node: update logical info and perform distribution iff
    // needed. Return true if the removal has been handled.
    // note that it's possible for both the node's host and its parent
    // to require distribution... both cases are handled here.
    _removeNode: function(node) {
      // important that we want to do this only if the node has a logical parent
      var logicalParent = TreeApi.Logical.hasParentNode(node) &&
        TreeApi.Logical.getParentNode(node);
      var distributed;
      var root = this._ownerShadyRootForNode(node);
      if (logicalParent) {
        // distribute node's parent iff needed
        distributed = dom(node)._maybeDistributeParent();
        TreeApi.Logical.recordRemoveChild(node, logicalParent);
        // remove node from root and distribute it iff needed
        if (root && this._removeDistributedChildren(root, node)) {
          root._invalidInsertionPoints = true;
          this._lazyDistribute(root.host);
        }
      }
      this._removeOwnerShadyRoot(node);
      if (root) {
        this._removeNodeFromHost(root.host, node);
      }
      return distributed;
    },

    replaceChild: function(node, ref_node) {
      this.insertBefore(node, ref_node);
      this.removeChild(ref_node);
      return node;
    },

    _hasCachedOwnerRoot: function(node) {
      return Boolean(node._ownerShadyRoot !== undefined);
    },

    getOwnerRoot: function() {
      return this._ownerShadyRootForNode(this.node);
    },

    _ownerShadyRootForNode: function(node) {
      if (!node) {
        return;
      }
      var root = node._ownerShadyRoot;
      if (root === undefined) {
        if (node._isShadyRoot) {
          root = node;
        } else {
          var parent = TreeApi.Logical.getParentNode(node);
          if (parent) {
            root = parent._isShadyRoot ? parent :
              this._ownerShadyRootForNode(parent);
          } else {
           root = null;
          }
        }
        // memo-ize result for performance but only memo-ize a false-y
        // result if node is in the document. This avoids a problem where a root
        // can be cached while an element is inside a fragment.
        // If this happens and we cache the result, the value can become stale
        // because for perf we avoid processing the subtree of added fragments.
        if (root || document.documentElement.contains(node)) {
          node._ownerShadyRoot = root;
        }
      }
      return root;
    },

    _maybeDistribute: function(node) {
      // TODO(sorvell): technically we should check non-fragment nodes for
      // <content> children but since this case is assumed to be exceedingly
      // rare, we avoid the cost and will address with some specific api
      // when the need arises.  For now, the user must call
      // distributeContent(true), which updates insertion points manually
      // and forces distribution.
      var fragContent = (node.nodeType === Node.DOCUMENT_FRAGMENT_NODE) &&
        !node.__noContent && dom(node).querySelector(CONTENT);
      var wrappedContent = fragContent &&
        (TreeApi.Logical.getParentNode(fragContent).nodeType !==
        Node.DOCUMENT_FRAGMENT_NODE);
      var hasContent = fragContent || (node.localName === CONTENT);
      // There are 2 possible cases where a distribution may need to occur:
      // 1. <content> being inserted (the host of the shady root where
      //    content is inserted needs distribution)
      // 2. children being inserted into parent with a shady root (parent
      //    needs distribution)
      if (hasContent) {
        var root = this.getOwnerRoot();
        if (root) {
          // note, insertion point list update is handled after node
          // mutations are complete
          this._lazyDistribute(root.host);
        }
      }
      var needsDist = this._nodeNeedsDistribution(this.node);
      if (needsDist) {
        this._lazyDistribute(this.node);
      }
      // Return true when distribution will fully handle the composition
      // Note that if a content was being inserted that was wrapped by a node,
      // and the parent does not need distribution, return false to allow
      // the nodes to be added directly, after which children may be
      // distributed and composed into the wrapping node(s)
      return needsDist || (hasContent && !wrappedContent);
    },

    /* note: parent argument is required since node may have an out
    of date parent at this point; returns true if a <content> is being added */
    _maybeAddInsertionPoint: function(node, parent) {
      var added;
      if (node.nodeType === Node.DOCUMENT_FRAGMENT_NODE &&
        !node.__noContent) {
        var c$ = dom(node).querySelectorAll(CONTENT);
        for (var i=0, n, np, na; (i<c$.length) && (n=c$[i]); i++) {
          np = TreeApi.Logical.getParentNode(n);
          // don't allow node's parent to be fragment itself
          if (np === node) {
            np = parent;
          }
          na = this._maybeAddInsertionPoint(n, np);
          added = added || na;
        }
      } else if (node.localName === CONTENT) {
        TreeApi.Logical.saveChildNodes(parent);
        TreeApi.Logical.saveChildNodes(node);
        added = true;
      }
      return added;
    },

    _updateInsertionPoints: function(host) {
      var i$ = host.shadyRoot._insertionPoints =
        dom(host.shadyRoot).querySelectorAll(CONTENT);
      // ensure <content>'s and their parents have logical dom info.
      for (var i=0, c; i < i$.length; i++) {
        c = i$[i];
        TreeApi.Logical.saveChildNodes(c);
        TreeApi.Logical.saveChildNodes(TreeApi.Logical.getParentNode(c));
      }
    },

    _nodeNeedsDistribution: function(node) {
      return node && node.shadyRoot &&
        DomApi.hasInsertionPoint(node.shadyRoot);
    },

    // a node being added is always in this same host as this.node.
    _addNodeToHost: function(host, node) {
      if (host._elementAdd) {
        host._elementAdd(node);
      }
    },

    _removeNodeFromHost: function(host, node) {
      if (host._elementRemove) {
        host._elementRemove(node);
      }
    },

    _removeDistributedChildren: function(root, container) {
      var hostNeedsDist;
      var ip$ = root._insertionPoints;
      for (var i=0; i<ip$.length; i++) {
        var content = ip$[i];
        if (this._contains(container, content)) {
          var dc$ = dom(content).getDistributedNodes();
          for (var j=0; j<dc$.length; j++) {
            hostNeedsDist = true;
            var node = dc$[j];
            var parent = TreeApi.Composed.getParentNode(node);
            if (parent) {
              TreeApi.Composed.removeChild(parent, node);
            }
          }
        }
      }
      return hostNeedsDist;
    },

    _contains: function(container, node) {
      while (node) {
        if (node == container) {
          return true;
        }
        node = TreeApi.Logical.getParentNode(node);
      }
    },

    _removeOwnerShadyRoot: function(node) {
      // optimization: only reset the tree if node is actually in a root
      if (this._hasCachedOwnerRoot(node)) {
        var c$ = TreeApi.Logical.getChildNodes(node);
        for (var i=0, l=c$.length, n; (i<l) && (n=c$[i]); i++) {
          this._removeOwnerShadyRoot(n);
        }
      }
      node._ownerShadyRoot = undefined;
    },

    // TODO(sorvell): This will fail if distribution that affects this
    // question is pending; this is expected to be exceedingly rare, but if
    // the issue comes up, we can force a flush in this case.
    _firstComposedNode: function(content) {
      var n$ = dom(content).getDistributedNodes();
      for (var i=0, l=n$.length, n, p$; (i<l) && (n=n$[i]); i++) {
        p$ = dom(n).getDestinationInsertionPoints();
        // means that we're composed to this spot.
        if (p$[p$.length-1] === content) {
          return n;
        }
      }
    },

    // TODO(sorvell): consider doing native QSA and filtering results.
    querySelector: function(selector) {
      // match selector and halt on first result.
      var result = this._query(function(n) {
        return DomApi.matchesSelector.call(n, selector);
      }, this.node, function(n) {
        return Boolean(n);
      })[0];
      return result || null;
    },

    querySelectorAll: function(selector) {
      return this._query(function(n) {
        return DomApi.matchesSelector.call(n, selector);
      }, this.node);
    },

    getDestinationInsertionPoints: function() {
      return this.node._destinationInsertionPoints || [];
    },

    getDistributedNodes: function() {
      return this.node._distributedNodes || [];
    },

    _clear: function() {
      while (this.childNodes.length) {
        this.removeChild(this.childNodes[0]);
      }
    },

    setAttribute: function(name, value) {
      this.node.setAttribute(name, value);
      this._maybeDistributeParent();
    },

    removeAttribute: function(name) {
      this.node.removeAttribute(name);
      this._maybeDistributeParent();
    },

    _maybeDistributeParent: function() {
      if (this._nodeNeedsDistribution(this.parentNode)) {
        this._lazyDistribute(this.parentNode);
        return true;
      }
    },

    cloneNode: function(deep) {
      var n = nativeCloneNode.call(this.node, false);
      if (deep) {
        var c$ = this.childNodes;
        var d = dom(n);
        for (var i=0, nc; i < c$.length; i++) {
          nc = dom(c$[i]).cloneNode(true);
          d.appendChild(nc);
        }
      }
      return n;
    },

    importNode: function(externalNode, deep) {
      // for convenience use this node's ownerDoc if the node isn't a document
      var doc = this.node instanceof Document ? this.node :
        this.node.ownerDocument;
      var n = nativeImportNode.call(doc, externalNode, false);
      if (deep) {
        var c$ = TreeApi.Logical.getChildNodes(externalNode);
        var d = dom(n);
        for (var i=0, nc; i < c$.length; i++) {
          nc = dom(doc).importNode(c$[i], true);
          d.appendChild(nc);
        }
      }
      return n;
    },

    _getComposedInnerHTML: function() {
      return getInnerHTML(this.node, true);
    }

  });

  Object.defineProperties(DomApi.prototype, {

    activeElement: {
      get: function() {
        var active = document.activeElement;
        if (!active) {
          return null;
        }
        var isShadyRoot = !!this.node._isShadyRoot;
        if (this.node !== document) {
          // If this node isn't a document or shady root, then it doesn't have
          // an active element.
          if (!isShadyRoot) {
            return null;
          }
          // If this shady root's host is the active element or the active
          // element is not a descendant of the host (in the composed tree),
          // then it doesn't have an active element.
          if (this.node.host === active ||
              !this.node.host.contains(active)) {
            return null;
          }
        }
        // This node is either the document or a shady root of which the active
        // element is a (composed) descendant of its host; iterate upwards to
        // find the active element's most shallow host within it.
        var activeRoot = dom(active).getOwnerRoot();
        while (activeRoot && activeRoot !== this.node) {
          active = activeRoot.host;
          activeRoot = dom(active).getOwnerRoot();
        }
        if (this.node === document) {
          // This node is the document, so activeRoot should be null.
          return activeRoot ? null : active;
        } else {
          // This node is a non-document shady root, and it should be
          // activeRoot.
          return activeRoot === this.node ? active : null;
        }
      },
      configurable: true
    },

    childNodes: {
      get: function() {
        var c$ = TreeApi.Logical.getChildNodes(this.node);
        return Array.isArray(c$) ? c$ : TreeApi.arrayCopyChildNodes(this.node);
      },
      configurable: true
    },

    children: {
      get: function() {
        if (TreeApi.Logical.hasChildNodes(this.node)) {
          return Array.prototype.filter.call(this.childNodes, function(n) {
            return (n.nodeType === Node.ELEMENT_NODE);
          });
        } else {
          return TreeApi.arrayCopyChildren(this.node);
        }
      },
      configurable: true
    },

    parentNode: {
      get: function() {
        return TreeApi.Logical.getParentNode(this.node);
      },
      configurable: true
    },

    firstChild: {
      get: function() {
        return TreeApi.Logical.getFirstChild(this.node);
      },
      configurable: true
    },

    lastChild: {
      get: function() {
        return TreeApi.Logical.getLastChild(this.node);
      },
      configurable: true
    },

    nextSibling: {
      get: function() {
        return TreeApi.Logical.getNextSibling(this.node);
      },
      configurable: true
    },

    previousSibling: {
      get: function() {
        return TreeApi.Logical.getPreviousSibling(this.node);
      },
      configurable: true
    },

    firstElementChild: {
      get: function() {
        return TreeApi.Logical.getFirstElementChild(this.node);
      },
      configurable: true
    },

    lastElementChild: {
      get: function() {
        return TreeApi.Logical.getLastElementChild(this.node);
      },
      configurable: true
    },

    nextElementSibling: {
      get: function() {
        return TreeApi.Logical.getNextElementSibling(this.node);
      },
      configurable: true
    },

    previousElementSibling: {
      get: function() {
        return TreeApi.Logical.getPreviousElementSibling(this.node);
      },
      configurable: true
    },

    // textContent / innerHTML
    textContent: {
      get: function() {
        var nt = this.node.nodeType;
        if (nt === Node.TEXT_NODE || nt === Node.COMMENT_NODE) {
          return this.node.textContent;
        } else {
          var tc = [];
          for (var i = 0, cn = this.childNodes, c; (c = cn[i]); i++) {
            if (c.nodeType !== Node.COMMENT_NODE) {
              tc.push(c.textContent);
            }
          }
          return tc.join('');
        }
      },
      set: function(text) {
        var nt = this.node.nodeType;
        if (nt === Node.TEXT_NODE || nt === Node.COMMENT_NODE) {
          this.node.textContent = text;
        } else {
          this._clear();
          if (text) {
            this.appendChild(document.createTextNode(text));
          }
        }
      },
      configurable: true
    },

    innerHTML: {
      get: function() {
        var nt = this.node.nodeType;
        if (nt === Node.TEXT_NODE || nt === Node.COMMENT_NODE) {
          return null;
        } else {
          return getInnerHTML(this.node);
        }
      },
      set: function(text) {
        var nt = this.node.nodeType;
        if (nt !== Node.TEXT_NODE || nt !== Node.COMMENT_NODE) {
          this._clear();
          var d = document.createElement('div');
          d.innerHTML = text;
          // here, appendChild may move nodes async so we cannot rely
          // on node position when copying
          var c$ = TreeApi.arrayCopyChildNodes(d);
          for (var i=0; i < c$.length; i++) {
            this.appendChild(c$[i]);
          }
        }
      },
      configurable: true
    }

  });

  DomApi.hasInsertionPoint = function(root) {
    return Boolean(root && root._insertionPoints.length);
  };

})();
(function() {
  'use strict';

  var Settings = Polymer.Settings;
  var TreeApi = Polymer.TreeApi;
  var DomApi = Polymer.DomApi;

  // *************** Configure DomApi for Shadow DOM!! ***************
  if (!Settings.useShadow) {
    return;
  }

  Polymer.Base.extend(DomApi.prototype, {

    querySelectorAll: function(selector) {
      return TreeApi.arrayCopy(this.node.querySelectorAll(selector));
    },

    getOwnerRoot: function() {
      var n = this.node;
      while (n) {
        if (n.nodeType === Node.DOCUMENT_FRAGMENT_NODE && n.host) {
          return n;
        }
        n = n.parentNode;
      }
    },

    importNode: function(externalNode, deep) {
      var doc = this.node instanceof Document ? this.node :
        this.node.ownerDocument;
      return doc.importNode(externalNode, deep);
    },

    getDestinationInsertionPoints: function() {
      var n$ = this.node.getDestinationInsertionPoints &&
        this.node.getDestinationInsertionPoints();
      return n$ ? TreeApi.arrayCopy(n$) : [];
    },

    getDistributedNodes: function() {
      var n$ = this.node.getDistributedNodes &&
        this.node.getDistributedNodes();
      return n$ ? TreeApi.arrayCopy(n$) : [];
    }

  });

  Object.defineProperties(DomApi.prototype, {

    activeElement: {
      get: function() {
        var node = DomApi.wrap(this.node);
        var activeElement = node.activeElement;
        // Prevents `activeElement` from returning elements outside of the
        // ShadowRoot, even if they would become descendants of the ShadowRoot
        // in the composed tree. See w3c/webcomponents#358.
        return node.contains(activeElement) ? activeElement : null;
      },
      configurable: true
    },

    childNodes: {
      get: function() {
        return TreeApi.arrayCopyChildNodes(this.node);
      },
      configurable: true
    },

    children: {
      get: function() {
        return TreeApi.arrayCopyChildren(this.node);
      },
      configurable: true
    },

    // textContent / innerHTML
    textContent: {
      get: function() {
        return this.node.textContent;
      },
      set: function(value) {
        return this.node.textContent = value;
      },
      configurable: true
    },

    innerHTML: {
      get: function() {
        return this.node.innerHTML;
      },
      set: function(value) {
        return this.node.innerHTML = value;
      },
      configurable: true
    }

  });

  var forwardMethods = function(m$) {
    for (var i=0; i < m$.length; i++) {
      forwardMethod(m$[i]);
    }
  };

  var forwardMethod = function(method) {
    DomApi.prototype[method] = function() {
      return this.node[method].apply(this.node, arguments);
    }
  };

  forwardMethods(['cloneNode', 'appendChild', 'insertBefore',
    'removeChild', 'replaceChild', 'setAttribute', 'removeAttribute',
    'querySelector']);

  var forwardProperties = function(f$) {
    for (var i=0; i < f$.length; i++) {
      forwardProperty(f$[i]);
    }
  };

  var forwardProperty = function(name) {
    Object.defineProperty(DomApi.prototype, name, {
      get: function() {
        return this.node[name];
      },
      configurable: true
    });
  };

  forwardProperties(['parentNode', 'firstChild', 'lastChild',
    'nextSibling', 'previousSibling', 'firstElementChild',
    'lastElementChild', 'nextElementSibling', 'previousElementSibling']);

})();
/**
   * `Polymer.dom.flush()` causes any asynchronously queued actions to be
   * flushed synchronously. It should be used sparingly as calling it frequently
   * can negatively impact performance since work is often deferred for
   * efficiency. Calling `Polymer.dom.flush()` is useful, for example, when
   * an element has to measure itself and is unsure about the state of its
   * internal or compoased DOM.
   */
  Polymer.Base.extend(Polymer.dom, {

    _flushGuard: 0,
    _FLUSH_MAX: 100,
    _needsTakeRecords: !Polymer.Settings.useNativeCustomElements,
    _debouncers: [],
    _staticFlushList: [],
    _finishDebouncer: null,

    // flush and debounce exposed as statics on Polymer.dom
    flush: function() {
      this._flushGuard = 0;
      this._prepareFlush();
      while (this._debouncers.length && this._flushGuard < this._FLUSH_MAX) {
        // Avoid using an index in this loop to ensure flush is safe to be
        // called reentrantly from a debouncer callback being flushed
        while (this._debouncers.length) {
          this._debouncers.shift().complete();
        }
        // clear the list of debouncers
        if (this._finishDebouncer) {
          this._finishDebouncer.complete();
        }
        this._prepareFlush();
        this._flushGuard++;
      }
      if (this._flushGuard >= this._FLUSH_MAX) {
        console.warn('Polymer.dom.flush aborted. Flush may not be complete.')
      }
    },

    _prepareFlush: function() {
      // TODO(sorvell): There is currently not a good way
      // to process all custom elements mutations under SD polyfill because
      // these mutations may be inside shadowRoots.
      // again make any pending CE mutations that might trigger debouncer
      // additions go...
      if (this._needsTakeRecords) {
        CustomElements.takeRecords();
      }
      for (var i=0; i < this._staticFlushList.length; i++) {
        this._staticFlushList[i]();
      }
    },

    // add to the static list of methods to call when flushing
    addStaticFlush: function(fn) {
      this._staticFlushList.push(fn);
    },

    // remove a function from the static list of methods to call when flushing
    removeStaticFlush: function(fn) {
      var i = this._staticFlushList.indexOf(fn);
      if (i >= 0) {
        this._staticFlushList.splice(i, 1);
      }
    },

    addDebouncer: function(debouncer) {
      this._debouncers.push(debouncer);
      // ensure the list of active debouncers is cleared when done.
      this._finishDebouncer = Polymer.Debounce(this._finishDebouncer,
        this._finishFlush);
    },

    _finishFlush: function() {
      Polymer.dom._debouncers = [];
    }

  });
Polymer.EventApi = (function() {
  'use strict';

  var DomApi = Polymer.DomApi.ctor;
  var Settings = Polymer.Settings;


  /**
   * DomApi.Event allows maniuplation of events compatible with
   * the scoping concepts in Shadow DOM and compatible with both Shady DOM
   * and Shadow DOM. The general usage is
   * `Polymer.dom(event).property`. The `path` property returns `event.path`
   * matching Shadow DOM. The `rootTarget` property returns the first node
   * in the `path` and is the original event target. The `localTarget` property
   * matches event.target under Shadow DOM and is the scoped event target.
   */
  DomApi.Event = function(event) {
    this.event = event;
  };

  if (Settings.useShadow) {

    DomApi.Event.prototype = {

      get rootTarget() {
        return this.event.path[0];
      },

      get localTarget() {
        return this.event.target;
      },

      get path() {
        var path = this.event.path;
        if (!Array.isArray(path)) {
          path = Array.prototype.slice.call(path);
        }
        return path;
      }

    };

  } else {

    DomApi.Event.prototype = {

      get rootTarget() {
        return this.event.target;
      },

      get localTarget() {
        var current = this.event.currentTarget;
        var currentRoot = current && Polymer.dom(current).getOwnerRoot();
        var p$ = this.path;
        for (var i=0; i < p$.length; i++) {
          if (Polymer.dom(p$[i]).getOwnerRoot() === currentRoot) {
            return p$[i];
          }
        }
      },

      // TODO(sorvell): simulate event.path. This probably incorrect for
      // non-bubbling events.
      get path() {
        if (!this.event._path) {
          var path = [];
          var current = this.rootTarget;
          while (current) {
            path.push(current);
            var insertionPoints = Polymer.dom(current).getDestinationInsertionPoints();
            if (insertionPoints.length) {
              for (var i = 0; i < insertionPoints.length - 1; i++) {
                path.push(insertionPoints[i]);
              }
              current = insertionPoints[insertionPoints.length - 1];
            } else {
              current = Polymer.dom(current).parentNode || current.host;
            }
          }
          // event path includes window in most recent native implementations
          path.push(window);
          this.event._path = path;
        }
        return this.event._path;
      }

    };

  }

  var factory = function(event) {
    if (!event.__eventApi) {
      event.__eventApi = new DomApi.Event(event);
    }
    return event.__eventApi;
  };

  return {
    factory: factory
  };

})();
(function() {
  'use strict';

  var DomApi = Polymer.DomApi.ctor;

  var useShadow = Polymer.Settings.useShadow;

  /**
   * DomApi.classList allows maniuplation of `classList` compatible with 
   * Polymer.dom. The general usage is 
   * `Polymer.dom(node).classList.method(arguments)` where methods and arguments
   * match native DOM.
   */
  Object.defineProperty(DomApi.prototype, 'classList', {
    get: function() {
      if (!this._classList) {
        this._classList = new DomApi.ClassList(this);
      }
      return this._classList;
    },
    configurable: true
  });

  DomApi.ClassList = function(host) {
    this.domApi = host;
    this.node = host.node;
  }

  DomApi.ClassList.prototype = {

    add: function() {
      this.node.classList.add.apply(this.node.classList, arguments);
      this._distributeParent();
    },

    remove: function() {
      this.node.classList.remove.apply(this.node.classList, arguments);
      this._distributeParent();
    },

    toggle: function() {
      this.node.classList.toggle.apply(this.node.classList, arguments);
      this._distributeParent();
    },

    _distributeParent: function() {
      if (!useShadow) {
        this.domApi._maybeDistributeParent();
      }
    },

    contains: function() {
      return this.node.classList.contains.apply(this.node.classList,
        arguments);
    }
  }

})();
(function() {
  'use strict';

    var DomApi = Polymer.DomApi.ctor;
    var Settings = Polymer.Settings;

    /**
     * DomApi.EffectiveNodesObserver tracks changes to an element's
     * effective child nodes, the same list returned from
     * `Polymer.dom(node).getEffectiveChildNodes()`.
     * It is not meant to be used directly; it is used by
     * `Polymer.dom(node).observeNodes(callback)` to observe changes.
     */
    DomApi.EffectiveNodesObserver = function(domApi) {
      this.domApi = domApi;
      this.node = this.domApi.node;
      this._listeners = [];
    };

    DomApi.EffectiveNodesObserver.prototype = {

      addListener: function(callback) {
        if (!this._isSetup) {
          this._setup();
          this._isSetup = true;
        }
        var listener = {fn: callback, _nodes: []};
        this._listeners.push(listener);
        this._scheduleNotify();
        return listener;
      },

      removeListener: function(handle) {
        var i = this._listeners.indexOf(handle);
        if (i >= 0) {
          this._listeners.splice(i, 1);
          handle._nodes = [];
        }
        if (!this._hasListeners()) {
          this._cleanup();
          this._isSetup = false;
        }
      },

      _setup: function() {
        this._observeContentElements(this.domApi.childNodes);
      },

      _cleanup: function() {
        this._unobserveContentElements(this.domApi.childNodes);
      },

      _hasListeners: function() {
        return Boolean(this._listeners.length);
      },

      _scheduleNotify: function() {
        if (this._debouncer) {
          this._debouncer.stop();
        }
        this._debouncer = Polymer.Debounce(this._debouncer,
          this._notify);
        this._debouncer.context = this;
        Polymer.dom.addDebouncer(this._debouncer);
      },

      notify: function() {
        if (this._hasListeners()) {
          this._scheduleNotify();
        }
      },

      _notify: function() {
        this._beforeCallListeners();
        this._callListeners();
      },

      _beforeCallListeners: function() {
        this._updateContentElements();
      },

      _updateContentElements: function() {
        this._observeContentElements(this.domApi.childNodes);
      },

      _observeContentElements: function(elements) {
        for (var i=0, n; (i < elements.length) && (n=elements[i]); i++) {
          if (this._isContent(n)) {
            n.__observeNodesMap = n.__observeNodesMap || new WeakMap();
            if (!n.__observeNodesMap.has(this)) {
              n.__observeNodesMap.set(this, this._observeContent(n));
            }
          }
        }
      },

      _observeContent: function(content) {
        var self = this;
        var h = Polymer.dom(content).observeNodes(function() {
          self._scheduleNotify();
        });
        h._avoidChangeCalculation = true;
        return h;
      },

      _unobserveContentElements: function(elements) {
        for (var i=0, n, h; (i < elements.length) && (n=elements[i]); i++) {
          if (this._isContent(n)) {
            h = n.__observeNodesMap.get(this);
            if (h) {
              Polymer.dom(n).unobserveNodes(h);
              n.__observeNodesMap.delete(this);
            }
          }
        }
      },

      _isContent: function(node) {
        return (node.localName === 'content');
      },

      _callListeners: function() {
        var o$ = this._listeners;
        var nodes = this._getEffectiveNodes();
        for (var i=0, o; (i < o$.length) && (o=o$[i]); i++) {
          var info = this._generateListenerInfo(o, nodes);
          if (info || o._alwaysNotify) {
            this._callListener(o, info);
          }
        }
      },

      _getEffectiveNodes: function() {
        return this.domApi.getEffectiveChildNodes()
      },

      _generateListenerInfo: function(listener, newNodes) {
        if (listener._avoidChangeCalculation) {
          return true;
        }
        var oldNodes = listener._nodes;
        var info = {
          target: this.node,
          addedNodes: [],
          removedNodes: []
        };
        var splices = Polymer.ArraySplice.calculateSplices(newNodes, oldNodes);
        // process removals
        for (var i=0, s; (i<splices.length) && (s=splices[i]); i++) {
          for (var j=0, n; (j < s.removed.length) && (n=s.removed[j]); j++) {
            info.removedNodes.push(n);
          }
        }
        // process adds
        for (i=0, s; (i<splices.length) && (s=splices[i]); i++) {
          for (j=s.index; j < s.index + s.addedCount; j++) {
            info.addedNodes.push(newNodes[j]);
          }
        }
        // update cache
        listener._nodes = newNodes;
        if (info.addedNodes.length || info.removedNodes.length) {
          return info;
        }
      },

      _callListener: function(listener, info) {
        return listener.fn.call(this.node, info);
      },

      enableShadowAttributeTracking: function() {}

    };

    if (Settings.useShadow) {

      var baseSetup = DomApi.EffectiveNodesObserver.prototype._setup;
      var baseCleanup = DomApi.EffectiveNodesObserver.prototype._cleanup;

      Polymer.Base.extend(DomApi.EffectiveNodesObserver.prototype, {

        _setup: function() {
          if (!this._observer) {
            var self = this;
            this._mutationHandler = function(mxns) {
              if (mxns && mxns.length) {
                self._scheduleNotify();
              }
            };
            this._observer = new MutationObserver(this._mutationHandler);
            this._boundFlush = function() {
              self._flush();
            }
            Polymer.dom.addStaticFlush(this._boundFlush);
            // NOTE: subtree true is way too aggressive, but it easily catches
            // attribute changes on children. These changes otherwise require
            // attribute observers on every child. Testing has shown this
            // approach to be more efficient.
            // TODO(sorvell): do we still need to include an option to defeat
            // attribute tracking?
            this._observer.observe(this.node, { childList: true });
          }
          baseSetup.call(this);
        },

        _cleanup: function() {
          this._observer.disconnect();
          this._observer = null;
          this._mutationHandler = null;
          Polymer.dom.removeStaticFlush(this._boundFlush);
          baseCleanup.call(this);
        },

        _flush: function() {
          if (this._observer) {
            this._mutationHandler(this._observer.takeRecords());
          }
        },

        enableShadowAttributeTracking: function() {
          if (this._observer) {
            // provoke all listeners needed for <content> observation
            // to always call listeners when no-op changes occur (which may
            // affect lower distributions.
            this._makeContentListenersAlwaysNotify();
            this._observer.disconnect();
            this._observer.observe(this.node, {
              childList: true,
              attributes: true,
              subtree: true
            });
            var root = this.domApi.getOwnerRoot();
            var host = root && root.host;
            if (host && Polymer.dom(host).observer) {
              Polymer.dom(host).observer.enableShadowAttributeTracking();
            }
          }
        },

        _makeContentListenersAlwaysNotify: function() {
          for (var i=0, h; i < this._listeners.length ; i++) {
            h = this._listeners[i];
            h._alwaysNotify = h._isContentListener;
          }
        }

      });

    }

})();
(function() {
  'use strict';

    var DomApi = Polymer.DomApi.ctor;
    var Settings = Polymer.Settings;

    /**
     * DomApi.DistributedNodesObserver notifies when the list returned by 
     * a <content> element's `getDistributedNodes()` may have changed.
     * It is not meant to be used directly; it is used by
     * `Polymer.dom(node).observeNodes(callback)` to observe changes to
     * `<content>.getDistributedNodes()`.
     */
    DomApi.DistributedNodesObserver = function(domApi) {
      DomApi.EffectiveNodesObserver.call(this, domApi);
    };

    DomApi.DistributedNodesObserver.prototype = 
      Object.create(DomApi.EffectiveNodesObserver.prototype);

    Polymer.Base.extend(DomApi.DistributedNodesObserver.prototype, {

      // NOTE: ShadyDOM distribute provokes notification of these observers
      // so no setup is required.
      _setup: function() {},

      _cleanup: function() {},

      // no need to update sub-elements since <content> does not nest
      // (but note that <slot> will)
      _beforeCallListeners: function() {},

      _getEffectiveNodes: function() {
        return this.domApi.getDistributedNodes();
      }

    });

    if (Settings.useShadow) {
      
      Polymer.Base.extend(DomApi.DistributedNodesObserver.prototype, {
        
        // NOTE: Under ShadowDOM we must observe the host element for
        // changes.
        _setup: function() {
          if (!this._observer) {
            var root = this.domApi.getOwnerRoot();
            var host = root && root.host;
            if (host) {
              var self = this;
              this._observer = Polymer.dom(host).observeNodes(function() {
                self._scheduleNotify();
              });
              // NOTE: we identify this listener as needed for <content>
              // notification so that enableShadowAttributeTracking 
              // can find these observers an ensure that we pass always 
              // pass notifications down.
              this._observer._isContentListener = true;
              if (this._hasAttrSelect()) {
                Polymer.dom(host).observer.enableShadowAttributeTracking();
              }
            }
          }
        },

        _hasAttrSelect: function() {
          var select = this.node.getAttribute('select');
          return select && select.match(/[[.]+/);
        },

        _cleanup: function() {
          var root = this.domApi.getOwnerRoot();
          var host = root && root.host;
          if (host) {
            Polymer.dom(host).unobserveNodes(this._observer);
          }
          this._observer = null;
        }

      });
    
    }

})();
(function() {
    /**
      Implements a pared down version of ShadowDOM's scoping, which is easy to
      polyfill across browsers.
    */
    var DomApi = Polymer.DomApi;
    var TreeApi = Polymer.TreeApi;

    Polymer.Base._addFeature({

      _prepShady: function() {
        // Use this system iff localDom is needed.
        this._useContent = this._useContent || Boolean(this._template);
      },

      _setupShady: function() {
        // object shaping...
        this.shadyRoot = null;
        if (!this.__domApi) {
          this.__domApi = null;
        }
        if (!this.__dom) {
          this.__dom = null;
        }
        if (!this._ownerShadyRoot) {
          this._ownerShadyRoot = undefined;
        }
      },

      // called as part of content initialization, prior to template stamping
      _poolContent: function() {
        if (this._useContent) {
          // capture lightChildren to help reify dom scoping
          TreeApi.Logical.saveChildNodes(this);
        }
      },

      // called as part of content initialization, after template stamping
      _setupRoot: function() {
        if (this._useContent) {
          this._createLocalRoot();
          // light elements may not be upgraded if they are light children
          // and there is no configuration flow (no dataHost) and they are
          // removed from document by shadyDOM distribution
          // so we ensure this here
          if (!this.dataHost) {
            upgradeLogicalChildren(TreeApi.Logical.getChildNodes(this));
          }
        }
      },

      _createLocalRoot: function() {
        this.shadyRoot = this.root;
        this.shadyRoot._distributionClean = false;
        this.shadyRoot._hasDistributed = false;
        this.shadyRoot._isShadyRoot = true;
        this.shadyRoot._dirtyRoots = [];
        // capture insertion point list
        var i$ = this.shadyRoot._insertionPoints = !this._notes ||
          this._notes._hasContent ?
          this.shadyRoot.querySelectorAll('content') : [];
        // save logical tree info
        // a. for shadyRoot
        // b. for insertion points (fallback)
        // c. for parents of insertion points
        TreeApi.Logical.saveChildNodes(this.shadyRoot);
        for (var i=0, c; i < i$.length; i++) {
          c = i$[i];
          TreeApi.Logical.saveChildNodes(c);
          TreeApi.Logical.saveChildNodes(c.parentNode);
        }
        this.shadyRoot.host = this;
      },

      /**
       * Return the element whose local dom within which this element
       * is contained. This is a shorthand for
       * `Polymer.dom(this).getOwnerRoot().host`.
       */
      get domHost() {
        var root = Polymer.dom(this).getOwnerRoot();
        return root && root.host;
      },

      /**
       * Force this element to distribute its children to its local dom.
       * A user should call `distributeContent` if distribution has been
       * invalidated due to changes to selectors on child elements that
       * effect distribution that were not made via `Polymer.dom`.
       * For example, if an element contains an insertion point with
       * `<content select=".foo">` and a `foo` class is added to a child,
       * then `distributeContent` must be called to update
       * local dom distribution.
       * @method distributeContent
       * @param {boolean} updateInsertionPoints Shady DOM does not detect
       *   <content> insertion that is nested in a sub-tree being appended.
       *   Set to true to distribute to newly added nested <content>'s.
       */
      distributeContent: function(updateInsertionPoints) {
        if (this.shadyRoot) {
          this.shadyRoot._invalidInsertionPoints =
            this.shadyRoot._invalidInsertionPoints || updateInsertionPoints;
          // Distribute the host that's the top of this element's distribution
          // tree. Distributing that host will *always* distibute this element.
          var host = getTopDistributingHost(this);
          Polymer.dom(this)._lazyDistribute(host);
        }
      },

      _distributeContent: function() {
        if (this._useContent && !this.shadyRoot._distributionClean) {
          if (this.shadyRoot._invalidInsertionPoints) {
            Polymer.dom(this)._updateInsertionPoints(this);
            this.shadyRoot._invalidInsertionPoints = false;
          }
          // logically distribute self
          this._beginDistribute();
          this._distributeDirtyRoots();
          this._finishDistribute();
        }
      },

      _beginDistribute: function() {
        if (this._useContent && DomApi.hasInsertionPoint(this.shadyRoot)) {
          // reset distributions
          this._resetDistribution();
          // compute which nodes should be distributed where
          // TODO(jmesserly): this is simplified because we assume a single
          // ShadowRoot per host and no `<shadow>`.
          this._distributePool(this.shadyRoot, this._collectPool());
        }
      },

      _distributeDirtyRoots: function() {
        var c$ = this.shadyRoot._dirtyRoots;
        for (var i=0, l= c$.length, c; (i<l) && (c=c$[i]); i++) {
          c._distributeContent();
        }
        this.shadyRoot._dirtyRoots = [];
      },

      _finishDistribute: function() {
        // compose self
        if (this._useContent) {
          // note: it's important to mark this clean before distribution
          // so that attachment that provokes additional distribution (e.g.
          // adding something to your parentNode) works
          this.shadyRoot._distributionClean = true;
          if (DomApi.hasInsertionPoint(this.shadyRoot)) {
            this._composeTree();
            // NOTE: send a signal to insertion points that we have distributed
            // which informs effective children observers
            notifyContentObservers(this.shadyRoot);
          } else {
            if (!this.shadyRoot._hasDistributed) {
              TreeApi.Composed.clearChildNodes(this);
              this.appendChild(this.shadyRoot);
            } else {
              // simplified non-tree walk composition
              var children = this._composeNode(this);
              this._updateChildNodes(this, children);
            }
          }
          // NOTE: send a signal to any Polymer.dom node observers
          // to report the initial set of childNodes
          if (!this.shadyRoot._hasDistributed) {
            notifyInitialDistribution(this);
          }
          this.shadyRoot._hasDistributed = true;
        }
      },

      /**
       * Polyfill for Element.prototype.matches, which is sometimes still
       * prefixed.
       *
       * @method elementMatches
       * @param {string} selector Selector to test.
       * @param {Element=} node Element to test the selector against.
       * @return {boolean} Whether the element matches the selector.
       */
      elementMatches: function(selector, node) {
        // Alternatively we could just polyfill it somewhere.
        // Note that the arguments are reversed from what you might expect.
        node = node || this;
        return DomApi.matchesSelector.call(node, selector);
      },

      // Many of the following methods are all conceptually static, but they are
      // included here as "protected" methods to allow overriding.

      _resetDistribution: function() {
        // light children
        var children = TreeApi.Logical.getChildNodes(this);
        for (var i = 0; i < children.length; i++) {
          var child = children[i];
          if (child._destinationInsertionPoints) {
            child._destinationInsertionPoints = undefined;
          }
          if (isInsertionPoint(child)) {
            clearDistributedDestinationInsertionPoints(child);
          }
        }
        // insertion points
        var root = this.shadyRoot;
        var p$ = root._insertionPoints;
        for (var j = 0; j < p$.length; j++) {
          p$[j]._distributedNodes = [];
        }
      },

      // Gather the pool of nodes that should be distributed. We will combine
      // these with the "content root" to arrive at the composed tree.
      _collectPool: function() {
        var pool = [];
        var children = TreeApi.Logical.getChildNodes(this);
        for (var i = 0; i < children.length; i++) {
          var child = children[i];
          if (isInsertionPoint(child)) {
            pool.push.apply(pool, child._distributedNodes);
          } else {
            pool.push(child);
          }
        }
        return pool;
      },

      // perform "logical" distribution; note, no actual dom is moved here,
      // instead elements are distributed into a `content._distributedNodes`
      // array where applicable.
      _distributePool: function(node, pool) {
        var p$ = node._insertionPoints;
        for (var i=0, l=p$.length, p; (i<l) && (p=p$[i]); i++) {
          this._distributeInsertionPoint(p, pool);
          // provoke redistribution on insertion point parents
          // must do this on all candidate hosts since distribution in this
          // scope invalidates their distribution.
          maybeRedistributeParent(p, this);
        }
      },

      _distributeInsertionPoint: function(content, pool) {
        // distribute nodes from the pool that this selector matches
        var anyDistributed = false;
        for (var i=0, l=pool.length, node; i < l; i++) {
          node=pool[i];
          // skip nodes that were already used
          if (!node) {
            continue;
          }
          // distribute this node if it matches
          if (this._matchesContentSelect(node, content)) {
            distributeNodeInto(node, content);
            // remove this node from the pool
            pool[i] = undefined;
            // since at least one node matched, we won't need fallback content
            anyDistributed = true;
          }
        }
        // Fallback content if nothing was distributed here
        if (!anyDistributed) {
          var children = TreeApi.Logical.getChildNodes(content);
          for (var j = 0; j < children.length; j++) {
            distributeNodeInto(children[j], content);
          }
        }
      },

      // Reify dom such that it is at its correct rendering position
      // based on logical distribution.
      _composeTree: function() {
        this._updateChildNodes(this, this._composeNode(this));
        var p$ = this.shadyRoot._insertionPoints;
        for (var i=0, l=p$.length, p, parent; (i<l) && (p=p$[i]); i++) {
          parent = TreeApi.Logical.getParentNode(p);
          if (!parent._useContent && (parent !== this) &&
            (parent !== this.shadyRoot)) {
            this._updateChildNodes(parent, this._composeNode(parent));
          }
        }
      },

      // Returns the list of nodes which should be rendered inside `node`.
      _composeNode: function(node) {
        var children = [];
        var c$ = TreeApi.Logical.getChildNodes(node.shadyRoot || node);
        for (var i = 0; i < c$.length; i++) {
          var child = c$[i];
          if (isInsertionPoint(child)) {
            var distributedNodes = child._distributedNodes;
            for (var j = 0; j < distributedNodes.length; j++) {
              var distributedNode = distributedNodes[j];
              if (isFinalDestination(child, distributedNode)) {
                children.push(distributedNode);
              }
            }
          } else {
            children.push(child);
          }
        }
        return children;
      },

      // Ensures that the rendered node list inside `container` is `children`.
      _updateChildNodes: function(container, children) {
        var composed = TreeApi.Composed.getChildNodes(container);
        var splices =
          Polymer.ArraySplice.calculateSplices(children, composed);
        // process removals
        for (var i=0, d=0, s; (i<splices.length) && (s=splices[i]); i++) {
          for (var j=0, n; (j < s.removed.length) && (n=s.removed[j]); j++) {
            // check if the node is still where we expect it is before trying
            // to remove it; this can happen if Polymer.dom moves a node and
            // then schedules its previous host for distribution resulting in
            // the node being removed here.
            if (TreeApi.Composed.getParentNode(n) === container) {
              TreeApi.Composed.removeChild(container, n);
            }
            composed.splice(s.index + d, 1);
          }
          d -= s.addedCount;
        }
        // process adds
        for (var i=0, s, next; (i<splices.length) && (s=splices[i]); i++) { //eslint-disable-line no-redeclare
          next = composed[s.index];
          for (j=s.index, n; j < s.index + s.addedCount; j++) {
            n = children[j];
            TreeApi.Composed.insertBefore(container, n, next);
            // TODO(sorvell): is this splice strictly needed?
            composed.splice(j, 0, n);
          }
        }
      },

      _matchesContentSelect: function(node, contentElement) {
        var select = contentElement.getAttribute('select');
        // no selector matches all nodes (including text)
        if (!select) {
          return true;
        }
        select = select.trim();
        // same thing if it had only whitespace
        if (!select) {
          return true;
        }
        // selectors can only match Elements
        if (!(node instanceof Element)) {
          return false;
        }
        // only valid selectors can match:
        //   TypeSelector
        //   *
        //   ClassSelector
        //   IDSelector
        //   AttributeSelector
        //   negation
        var validSelectors = /^(:not\()?[*.#[a-zA-Z_|]/;
        if (!validSelectors.test(select)) {
          return false;
        }
        return this.elementMatches(select, node);
      },

      // system override point
      _elementAdd: function() {},

      // system override point
      _elementRemove: function() {}

    });

    function distributeNodeInto(child, insertionPoint) {
      insertionPoint._distributedNodes.push(child);
      var points = child._destinationInsertionPoints;
      if (!points) {
        child._destinationInsertionPoints = [insertionPoint];
      } else {
        points.push(insertionPoint);
      }
    }

    function clearDistributedDestinationInsertionPoints(content) {
      var e$ = content._distributedNodes;
      if (e$) {
        for (var i=0; i < e$.length; i++) {
          var d = e$[i]._destinationInsertionPoints;
          if (d) {
            // this is +1 because these insertion points are *not* in this scope
            d.splice(d.indexOf(content)+1, d.length);
          }
        }
      }
    }

    // dirty a shadyRoot if a change may trigger reprojection!
    function maybeRedistributeParent(content, host) {
      // only get logical parent.
      var parent = TreeApi.Logical.getParentNode(content);
      if (parent && parent.shadyRoot &&
          DomApi.hasInsertionPoint(parent.shadyRoot) &&
          parent.shadyRoot._distributionClean) {
        parent.shadyRoot._distributionClean = false;
        host.shadyRoot._dirtyRoots.push(parent);
      }
    }

    function isFinalDestination(insertionPoint, node) {
      var points = node._destinationInsertionPoints;
      return points && points[points.length - 1] === insertionPoint;
    }

    function isInsertionPoint(node) {
      // TODO(jmesserly): we could add back 'shadow' support here.
      return node.localName == 'content';
    }

    // returns the host that's the top of this host's distribution tree
    function getTopDistributingHost(host) {
      while (host && hostNeedsRedistribution(host)) {
        host = host.domHost;
      }
      return host;
    }

    // Return true if a host's children includes
    // an insertion point that selects selectively
    function hostNeedsRedistribution(host) {
      var c$ = TreeApi.Logical.getChildNodes(host);
      for (var i=0, c; i < c$.length; i++) {
        c = c$[i];
        if (c.localName && c.localName === 'content') {
          return host.domHost;
        }
      }
    }

    function notifyContentObservers(root) {
      for (var i=0, c; i < root._insertionPoints.length; i++) {
        c = root._insertionPoints[i];
        if (DomApi.hasApi(c)) {
          Polymer.dom(c).notifyObserver();
        }
      }
    }

    function notifyInitialDistribution(host) {
      if (DomApi.hasApi(host)) {
        Polymer.dom(host).notifyObserver();
      }
    }

    var needsUpgrade = window.CustomElements && !CustomElements.useNative;

    function upgradeLogicalChildren(children) {
      if (needsUpgrade && children) {
        for (var i=0; i < children.length; i++) {
          CustomElements.upgrade(children[i]);
        }
      }
    }
  })();
/**
    Implements `shadyRoot` compatible dom scoping using native ShadowDOM.
  */

  // Transform styles if not using ShadowDOM or if flag is set.

  if (Polymer.Settings.useShadow) {

    Polymer.Base._addFeature({

      // no-op's when ShadowDOM is in use
      _poolContent: function() {},
      _beginDistribute: function() {},
      distributeContent: function() {},
      _distributeContent: function() {},
      _finishDistribute: function() {},
      
      // create a shadowRoot
      _createLocalRoot: function() {
        this.createShadowRoot();
        this.shadowRoot.appendChild(this.root);
        this.root = this.shadowRoot;
      }

    });

  };
Polymer.Async = {

  _currVal: 0,
  _lastVal: 0,
  _callbacks: [],
  _twiddleContent: 0,
  _twiddle: document.createTextNode(''),

  run: function (callback, waitTime) {
    if (waitTime > 0) {
      return ~setTimeout(callback, waitTime);
    } else {
      this._twiddle.textContent = this._twiddleContent++;
      this._callbacks.push(callback);
      return this._currVal++;
    }
  },

  cancel: function(handle) {
    if (handle < 0) {
      clearTimeout(~handle);
    } else {
      var idx = handle - this._lastVal;
      if (idx >= 0) {
        if (!this._callbacks[idx]) {
          throw 'invalid async handle: ' + handle;
        }
        this._callbacks[idx] = null;
      }
    }
  },

  _atEndOfMicrotask: function() {
    var len = this._callbacks.length;
    for (var i=0; i<len; i++) {
      var cb = this._callbacks[i];
      if (cb) {
        try {
          cb();
        } catch(e) {
          // Clear queue up to this point & start over after throwing
          i++;
          this._callbacks.splice(0, i);
          this._lastVal += i;
          this._twiddle.textContent = this._twiddleContent++;
          throw e;
        }
      }
    }
    this._callbacks.splice(0, len);
    this._lastVal += len;
  }
};

new window.MutationObserver(function() {
    Polymer.Async._atEndOfMicrotask();
  }).observe(Polymer.Async._twiddle, {characterData: true});
Polymer.Debounce = (function() {
  
  // usage
  
  // invoke cb.call(this) in 100ms, unless the job is re-registered,
  // which resets the timer
  // 
  // this.job = this.debounce(this.job, cb, 100)
  //
  // returns a handle which can be used to re-register a job

  var Async = Polymer.Async;
  
  var Debouncer = function(context) {
    this.context = context;
    var self = this;
    this.boundComplete = function() {
      self.complete();
    }
  };
  
  Debouncer.prototype = {
    go: function(callback, wait) {
      var h;
      this.finish = function() {
        Async.cancel(h);
      };
      h = Async.run(this.boundComplete, wait);
      this.callback = callback;
    },
    stop: function() {
      if (this.finish) {
        this.finish();
        this.finish = null;
        this.callback = null;
      }
    },
    complete: function() {
      if (this.finish) {
        var callback = this.callback;
        this.stop();
        callback.call(this.context);
      }
    }
  };

  function debounce(debouncer, callback, wait) {
    if (debouncer) {
      debouncer.stop();
    } else {
      debouncer = new Debouncer(this);
    }
    debouncer.go(callback, wait);
    return debouncer;
  }
  
  // exports 

  return debounce;
  
})();
Polymer.Base._addFeature({

    _setupDebouncers: function() {
      this._debouncers = {};
    },

    /**
     * Call `debounce` to collapse multiple requests for a named task into
     * one invocation which is made after the wait time has elapsed with
     * no new request.  If no wait time is given, the callback will be called
     * at microtask timing (guaranteed before paint).
     *
     *     debouncedClickAction: function(e) {
     *       // will not call `processClick` more than once per 100ms
     *       this.debounce('click', function() {
     *        this.processClick();
     *       }, 100);
     *     }
     *
     * @method debounce
     * @param {String} jobName String to indentify the debounce job.
     * @param {Function} callback Function that is called (with `this`
     *   context) when the wait time elapses.
     * @param {number} wait Optional wait time in milliseconds (ms) after the
     *   last signal that must elapse before invoking `callback`
     */
    debounce: function(jobName, callback, wait) {
      return this._debouncers[jobName] = Polymer.Debounce.call(this,
        this._debouncers[jobName], callback, wait);
    },

    /**
     * Returns whether a named debouncer is active.
     *
     * @method isDebouncerActive
     * @param {String} jobName The name of the debouncer started with `debounce`
     * @return {boolean} Whether the debouncer is active (has not yet fired).
     */
    isDebouncerActive: function(jobName) {
      var debouncer = this._debouncers[jobName];
      return !!(debouncer && debouncer.finish);
    },

    /**
     * Immediately calls the debouncer `callback` and inactivates it.
     *
     * @method flushDebouncer
     * @param {String} jobName The name of the debouncer started with `debounce`
     */
    flushDebouncer: function(jobName) {
      var debouncer = this._debouncers[jobName];
      if (debouncer) {
        debouncer.complete();
      }
    },

    /**
     * Cancels an active debouncer.  The `callback` will not be called.
     *
     * @method cancelDebouncer
     * @param {String} jobName The name of the debouncer started with `debounce`
     */
    cancelDebouncer: function(jobName) {
      var debouncer = this._debouncers[jobName];
      if (debouncer) {
        debouncer.stop();
      }
    }

  });
Polymer.DomModule = document.createElement('dom-module');

  Polymer.Base._addFeature({

    _registerFeatures: function() {
      // identity
      this._prepIs();
      // shared behaviors
      this._prepBehaviors();
      // factory
      this._prepConstructor();
      // template
      this._prepTemplate();
      // dom encapsulation
      this._prepShady();
      // fast access to property info
      this._prepPropertyInfo();
    },

    _prepBehavior: function(b) {
      this._addHostAttributes(b.hostAttributes);
    },

    _initFeatures: function() {
      this._registerHost();
      if (this._template) {
        // manage local dom
        this._poolContent();
        // host stack
        this._beginHosting();
        // instantiate template
        this._stampTemplate();
        // host stack
        this._endHosting();
      }
      // install host attributes
      this._marshalHostAttributes();
      // setup debouncers
      this._setupDebouncers();
      // instance shared behaviors
      this._marshalBehaviors();
      // top-down initial distribution, configuration, & ready callback
      this._tryReady();
    },

    _marshalBehavior: function(b) {
    }

  });
/**
 * Scans a template to produce an annotation list that that associates
 * metadata culled from markup with tree locations
 * metadata and information to associate the metadata with nodes in an instance.
 *
 * Supported expressions include:
 *
 * Double-mustache annotations in text content. The annotation must be the only
 * content in the tag, compound expressions are not supported.
 *
 *     <[tag]>{{annotation}}<[tag]>
 *
 * Double-escaped annotations in an attribute, either {{}} or [[]].
 *
 *     <[tag] someAttribute="{{annotation}}" another="[[annotation]]"><[tag]>
 *
 * `on-` style event declarations.
 *
 *     <[tag] on-<event-name>="annotation"><[tag]>
 *
 * Note that the `annotations` feature does not implement any behaviors
 * associated with these expressions, it only captures the data.
 *
 * Generated data-structure:
 *
 *     [
 *       {
 *         id: '<id>',
 *         events: [
 *           {
 *             name: '<name>'
 *             value: '<annotation>'
 *           }, ...
 *         ],
 *         bindings: [
 *           {
 *             kind: ['text'|'attribute'],
 *             mode: ['{'|'['],
 *             name: '<name>'
 *             value: '<annotation>'
 *           }, ...
 *         ],
 *         // TODO(sjmiles): this is annotation-parent, not node-parent
 *         parent: <reference to parent annotation object>,
 *         index: <integer index in parent's childNodes collection>
 *       },
 *       ...
 *     ]
 *
 * @class Template feature
 */

  // null-array (shared empty array to avoid null-checks)
  Polymer.nar = [];

  Polymer.Annotations = {

    // preprocess-time

    // construct and return a list of annotation records
    // by scanning `template`'s content
    //
    parseAnnotations: function(template) {
      var list = [];
      var content = template._content || template.content;
      this._parseNodeAnnotations(content, list,
        template.hasAttribute('strip-whitespace'));
      return list;
    },

    // add annotations gleaned from subtree at `node` to `list`
    _parseNodeAnnotations: function(node, list, stripWhiteSpace) {
      return node.nodeType === Node.TEXT_NODE ?
        this._parseTextNodeAnnotation(node, list) :
          // TODO(sjmiles): are there other nodes we may encounter
          // that are not TEXT_NODE but also not ELEMENT?
          this._parseElementAnnotations(node, list, stripWhiteSpace);
    },

    _bindingRegex: (function() {
      var IDENT  = '(?:' + '[a-zA-Z_$][\\w.:$\\-*]*' + ')';
      var NUMBER = '(?:' + '[-+]?[0-9]*\\.?[0-9]+(?:[eE][-+]?[0-9]+)?' + ')';
      var SQUOTE_STRING = '(?:' + '\'(?:[^\'\\\\]|\\\\.)*\'' + ')';
      var DQUOTE_STRING = '(?:' + '"(?:[^"\\\\]|\\\\.)*"' + ')';
      var STRING = '(?:' + SQUOTE_STRING + '|' + DQUOTE_STRING + ')';
      var ARGUMENT = '(?:' + IDENT + '|' + NUMBER + '|' +  STRING + '\\s*' + ')';
      var ARGUMENTS = '(?:' + ARGUMENT + '(?:,\\s*' + ARGUMENT + ')*' + ')';
      var ARGUMENT_LIST = '(?:' + '\\(\\s*' +
                                    '(?:' + ARGUMENTS + '?' + ')' +
                                  '\\)\\s*' + ')';
      var BINDING = '(' + IDENT + '\\s*' + ARGUMENT_LIST + '?' + ')'; // Group 3
      var OPEN_BRACKET = '(\\[\\[|{{)' + '\\s*';
      var CLOSE_BRACKET = '(?:]]|}})';
      var NEGATE = '(?:(!)\\s*)?'; // Group 2
      var EXPRESSION = OPEN_BRACKET + NEGATE + BINDING + CLOSE_BRACKET;
      return new RegExp(EXPRESSION, "g");
    })(),

    // TODO(kschaaf): We could modify this to allow an escape mechanism by
    // looking for the escape sequence in each of the matches and converting
    // the part back to a literal type, and then bailing if only literals
    // were found
    _parseBindings: function(text) {
      var re = this._bindingRegex;
      var parts = [];
      var lastIndex = 0;
      var m;
      // Example: "literal1{{prop}}literal2[[!compute(foo,bar)]]final"
      // Regex matches:
      //        Iteration 1:  Iteration 2:
      // m[1]: '{{'          '[['
      // m[2]: ''            '!'
      // m[3]: 'prop'        'compute(foo,bar)'
      while ((m = re.exec(text)) !== null) {
        // Add literal part
        if (m.index > lastIndex) {
          parts.push({literal: text.slice(lastIndex, m.index)});
        }
        // Add binding part
        // Mode (one-way or two)
        var mode = m[1][0];
        var negate = Boolean(m[2]);
        var value = m[3].trim();
        var customEvent, notifyEvent, colon;
        if (mode == '{' && (colon = value.indexOf('::')) > 0) {
          notifyEvent = value.substring(colon + 2);
          value = value.substring(0, colon);
          customEvent = true;
        }
        parts.push({
          compoundIndex: parts.length,
          value: value,
          mode: mode,
          negate: negate,
          event: notifyEvent,
          customEvent: customEvent
        });
        lastIndex = re.lastIndex;
      }
      // Add a final literal part
      if (lastIndex && lastIndex < text.length) {
        var literal = text.substring(lastIndex);
        if (literal) {
          parts.push({
            literal: literal
          });
        }
      }
      if (parts.length) {
        return parts;
      }
    },

    _literalFromParts: function(parts) {
      var s = '';
      for (var i=0; i<parts.length; i++) {
        var literal = parts[i].literal;
        s += literal || '';
      }
      return s;
    },

    // add annotations gleaned from TextNode `node` to `list`
    _parseTextNodeAnnotation: function(node, list) {
      var parts = this._parseBindings(node.textContent);
      if (parts) {
        // Initialize the textContent with any literal parts
        // NOTE: default to a space here so the textNode remains; some browsers
        // (IE) evacipate an empty textNode following cloneNode/importNode.
        node.textContent = this._literalFromParts(parts) || ' ';
        var annote = {
          bindings: [{
            kind: 'text',
            name: 'textContent',
            parts: parts,
            isCompound: parts.length !== 1
          }]
        };
        list.push(annote);
        return annote;
      }
    },

    // add annotations gleaned from Element `node` to `list`
    _parseElementAnnotations: function(element, list, stripWhiteSpace) {
      var annote = {
        bindings: [],
        events: []
      };
      if (element.localName === 'content') {
        list._hasContent = true;
      }
      this._parseChildNodesAnnotations(element, annote, list, stripWhiteSpace);
      // TODO(sjmiles): is this for non-ELEMENT nodes? If so, we should
      // change the contract of this method, or filter these out above.
      if (element.attributes) {
        this._parseNodeAttributeAnnotations(element, annote, list);
        // TODO(sorvell): ad hoc callback for doing work on elements while
        // leveraging annotator's tree walk.
        // Consider adding an node callback registry and moving specific
        // processing out of this module.
        if (this.prepElement) {
          this.prepElement(element);
        }
      }
      if (annote.bindings.length || annote.events.length || annote.id) {
        list.push(annote);
      }
      return annote;
    },

    // add annotations gleaned from children of `root` to `list`, `root`'s
    // `annote` is supplied as it is the annote.parent of added annotations
    _parseChildNodesAnnotations: function(root, annote, list, stripWhiteSpace) {
      if (root.firstChild) {
        var node = root.firstChild;
        var i = 0;
        while (node) {
          var next = node.nextSibling;
          if (node.localName === 'template' &&
            !node.hasAttribute('preserve-content')) {
            this._parseTemplate(node, i, list, annote);
          }
          // collapse adjacent textNodes: fixes an IE issue that can cause
          // text nodes to be inexplicably split =(
          // note that root.normalize() should work but does not so we do this
          // manually.
          if (node.nodeType === Node.TEXT_NODE) {
            var n = next;
            while (n && (n.nodeType === Node.TEXT_NODE)) {
              node.textContent += n.textContent;
              next = n.nextSibling;
              root.removeChild(n);
              n = next;
            }
            // optionally strip whitespace
            if (stripWhiteSpace && !node.textContent.trim()) {
              root.removeChild(node);
              // decrement index since node is removed
              i--;
            }
          }
          // if this node didn't get evacipated, parse it.
          if (node.parentNode) {
            var childAnnotation = this._parseNodeAnnotations(node, list,
              stripWhiteSpace);
            if (childAnnotation) {
              childAnnotation.parent = annote;
              childAnnotation.index = i;
            }
          }
          node = next;
          i++;
        }
      }
    },

    // 1. Parse annotations from the template and memoize them on
    //    content._notes (recurses into nested templates)
    // 2. Remove template.content and store it in annotation list, where it
    //    will be the responsibility of the host to set it back to the template
    //    (this is both an optimization to avoid re-stamping nested template
    //    children and avoids a bug in Chrome where nested template children
    //    upgrade)
    _parseTemplate: function(node, index, list, parent) {
      // TODO(sjmiles): simply altering the .content reference didn't
      // work (there was some confusion, might need verification)
      var content = document.createDocumentFragment();
      content._notes = this.parseAnnotations(node);
      content.appendChild(node.content);
      // TODO(sjmiles): using `nar` to avoid unnecessary allocation;
      // in general the handling of these arrays needs some cleanup
      // in this module
      list.push({
        bindings: Polymer.nar,
        events: Polymer.nar,
        templateContent: content,
        parent: parent,
        index: index
      });
    },

    // add annotation data from attributes to the `annotation` for node `node`
    // TODO(sjmiles): the distinction between an `annotation` and
    // `annotation data` is not as clear as it could be
    _parseNodeAttributeAnnotations: function(node, annotation) {
      // Make copy of original attribute list, since the order may change
      // as attributes are added and removed
      var attrs = Array.prototype.slice.call(node.attributes);
      for (var i=attrs.length-1, a; (a=attrs[i]); i--) {
        var n = a.name;
        var v = a.value;
        var b;
        // events (on-*)
        if (n.slice(0, 3) === 'on-') {
          node.removeAttribute(n);
          annotation.events.push({
            name: n.slice(3),
            value: v
          });
        }
        // bindings (other attributes)
        else if ((b = this._parseNodeAttributeAnnotation(node, n, v))) {
          annotation.bindings.push(b);
        }
        // static id
        else if (n === 'id') {
          annotation.id = v;
        }
      }
    },

    // construct annotation data from a generic attribute, or undefined
    _parseNodeAttributeAnnotation: function(node, name, value) {
      var parts = this._parseBindings(value);
      if (parts) {
        // Attribute or property
        var origName = name;
        var kind = 'property';
        if (name[name.length-1] == '$') {
          name = name.slice(0, -1);
          kind = 'attribute';
        }
        // Initialize attribute bindings with any literal parts
        var literal = this._literalFromParts(parts);
        if (literal && kind == 'attribute') {
          node.setAttribute(name, literal);
        }
        // Clear attribute before removing, since IE won't allow removing
        // `value` attribute if it previously had a value (can't
        // unconditionally set '' before removing since attributes with `$`
        // can't be set using setAttribute)
        if (node.localName === 'input' && origName === 'value') {
          node.setAttribute(origName, '');
        }
        // Remove annotation
        node.removeAttribute(origName);
        // Case hackery: attributes are lower-case, but bind targets
        // (properties) are case sensitive. Gambit is to map dash-case to
        // camel-case: `foo-bar` becomes `fooBar`.
        // Attribute bindings are excepted.
        var propertyName = Polymer.CaseMap.dashToCamelCase(name);
        if (kind === 'property') {
          name = propertyName;
        }
        return {
          kind: kind,
          name: name,
          propertyName: propertyName,
          parts: parts,
          literal: literal,
          isCompound: parts.length !== 1
        };
      }
    },

    // instance-time

    findAnnotatedNode: function(root, annote) {
      // recursively ascend tree until we hit root
      var parent = annote.parent &&
        Polymer.Annotations.findAnnotatedNode(root, annote.parent);
      // unwind the stack, returning the indexed node at each level
      if (parent) {
        // note: marginally faster than indexing via childNodes
        // (http://jsperf.com/childnodes-lookup)
        for (var n=parent.firstChild, i=0; n; n=n.nextSibling) {
          if (annote.index === i++) {
            return n;
          }
        }
      } else {
        return root;
      }
    }

  };
(function() {

    // path fixup for urls in cssText that's expected to 
    // come from a given ownerDocument
    function resolveCss(cssText, ownerDocument) {
      return cssText.replace(CSS_URL_RX, function(m, pre, url, post) {
        return pre + '\'' + 
          resolve(url.replace(/["']/g, ''), ownerDocument) + 
          '\'' + post;
      });
    }

    // url fixup for urls in an element's attributes made relative to 
    // ownerDoc's base url
    function resolveAttrs(element, ownerDocument) {
      for (var name in URL_ATTRS) {
        var a$ = URL_ATTRS[name];
        for (var i=0, l=a$.length, a, at, v; (i<l) && (a=a$[i]); i++) {
          if (name === '*' || element.localName === name) {
            at = element.attributes[a];
            v = at && at.value;
            if (v && (v.search(BINDING_RX) < 0)) {
              at.value = (a === 'style') ?
                resolveCss(v, ownerDocument) :
                resolve(v, ownerDocument);
            }
          }
        }
      }
    }

    function resolve(url, ownerDocument) {
      // do not resolve '#' links, they are used for routing
      if (url && url[0] === '#') {
        return url;
      }      
      var resolver = getUrlResolver(ownerDocument);
      resolver.href = url;
      return resolver.href || url;
    }

    var tempDoc;
    var tempDocBase;
    function resolveUrl(url, baseUri) {
      if (!tempDoc) {
        tempDoc = document.implementation.createHTMLDocument('temp');
        tempDocBase = tempDoc.createElement('base');
        tempDoc.head.appendChild(tempDocBase);
      }
      tempDocBase.href = baseUri;
      return resolve(url, tempDoc);
    }

    function getUrlResolver(ownerDocument) {
      return ownerDocument.__urlResolver || 
        (ownerDocument.__urlResolver = ownerDocument.createElement('a'));
    }

    var CSS_URL_RX = /(url\()([^)]*)(\))/g;
    var URL_ATTRS = {
      '*': ['href', 'src', 'style', 'url'],
      form: ['action']
    };
    var BINDING_RX = /\{\{|\[\[/;

    // exports
    Polymer.ResolveUrl = {
      resolveCss: resolveCss,
      resolveAttrs: resolveAttrs,
      resolveUrl: resolveUrl
    };

  })();
/**
 * Scans a template to produce an annotation object that stores expression
 * metadata along with information to associate the metadata with nodes in an
 * instance.
 *
 * Elements with `id` in the template are noted and marshaled into an
 * the `$` hash in an instance.
 *
 * Example
 *
 *     &lt;template>
 *       &lt;div id="foo">&lt;/div>
 *     &lt;/template>
 *     &lt;script>
 *      Polymer({
 *        task: function() {
 *          this.$.foo.style.color = 'red';
 *        }
 *      });
 *     &lt;/script>
 *
 * Other expressions that are noted include:
 *
 * Double-mustache annotations in text content. The annotation must be the only
 * content in the tag, compound expressions are not (currently) supported.
 *
 *     <[tag]>{{path.to.host.property}}<[tag]>
 *
 * Double-mustache annotations in an attribute.
 *
 *     <[tag] someAttribute="{{path.to.host.property}}"><[tag]>
 *
 * Only immediate host properties can automatically trigger side-effects.
 * Setting `host.path` in the example above triggers the binding, setting
 * `host.path.to.host.property` does not.
 *
 * `on-` style event declarations.
 *
 *     <[tag] on-<event-name>="{{hostMethodName}}"><[tag]>
 *
 * Note: **the `annotations` feature does not actually implement the behaviors
 * associated with these expressions, it only captures the data**.
 *
 * Other optional features contain actual data implementations.
 *
 * @class standard feature: annotations
 */

/*

Scans a template to produce an annotation map that stores expression metadata
and information that associates the metadata to nodes in a template instance.

Supported annotations are:

  * id attributes
  * binding annotations in text nodes
    * double-mustache expressions: {{expression}}
    * double-bracket expressions: [[expression]]
  * binding annotations in attributes
    * attribute-bind expressions: name="{{expression}} || [[expression]]"
    * property-bind expressions: name*="{{expression}} || [[expression]]"
    * property-bind expressions: name:="expression"
  * event annotations
    * event delegation directives: on-<eventName>="expression"

Generated data-structure:

  [
    {
      id: '<id>',
      events: [
        {
          mode: ['auto'|''],
          name: '<name>'
          value: '<expression>'
        }, ...
      ],
      bindings: [
        {
          kind: ['text'|'attribute'|'property'],
          mode: ['auto'|''],
          name: '<name>'
          value: '<expression>'
        }, ...
      ],
      // TODO(sjmiles): confusingly, this is annotation-parent, not node-parent
      parent: <reference to parent annotation>,
      index: <integer index in parent's childNodes collection>
    },
    ...
  ]

TODO(sjmiles): this module should produce either syntactic metadata
(e.g. double-mustache, double-bracket, star-attr), or semantic metadata
(e.g. manual-bind, auto-bind, property-bind). Right now it's half and half.

*/

  Polymer.Base._addFeature({

    // registration-time

    _prepAnnotations: function() {
      if (!this._template) {
        this._notes = [];
      } else {
        // TODO(sorvell): ad hoc method of plugging behavior into Annotations
        var self = this;
        Polymer.Annotations.prepElement = function(element) {
          self._prepElement(element);
        }
        if (this._template._content && this._template._content._notes) {
          this._notes = this._template._content._notes;
        }  else {
          this._notes = Polymer.Annotations.parseAnnotations(this._template);
          this._processAnnotations(this._notes);
        }
        Polymer.Annotations.prepElement = null;
      }
    },

    _processAnnotations: function(notes) {
      for (var i=0; i<notes.length; i++) {
        var note = notes[i];
        // Parse bindings for methods & path roots (models)
        for (var j=0; j<note.bindings.length; j++) {
          var b = note.bindings[j];
          for (var k=0; k<b.parts.length; k++) {
            var p = b.parts[k];
            if (!p.literal) {
              var signature = this._parseMethod(p.value);
              if (signature) {
                p.signature = signature;
              } else {
                p.model = this._modelForPath(p.value);
              }
            }
          }
        }
        // Recurse into nested templates & bind parent props
        if (note.templateContent) {
          this._processAnnotations(note.templateContent._notes);
          var pp = note.templateContent._parentProps =
            this._discoverTemplateParentProps(note.templateContent._notes);
          var bindings = [];
          for (var prop in pp) {
            var name = '_parent_' + prop;
            bindings.push({
              index: note.index,
              kind: 'property',
              name: name,
              propertyName: name,
              parts: [{
                mode: '{',
                model: prop,
                value: prop
              }]
            });
          }
          note.bindings = note.bindings.concat(bindings);
        }
      }
    },

    // Finds all bindings in template content and stores the path roots in
    // the path members in content._parentProps. Each outer template merges
    // inner _parentProps to propagate inner parent property needs to outer
    // templates.
    _discoverTemplateParentProps: function(notes) {
      var pp = {};
      for (var i=0, n; (i<notes.length) && (n=notes[i]); i++) {
        // Find all bindings to parent.* and spread them into _parentPropChain
        for (var j=0, b$=n.bindings, b; (j<b$.length) && (b=b$[j]); j++) {
          for (var k=0, p$=b.parts, p; (k<p$.length) && (p=p$[k]); k++) {
            if (p.signature) {
              var args = p.signature.args;
              for (var kk=0; kk<args.length; kk++) {
                var model = args[kk].model;
                if (model) {
                  pp[model] = true;
                }
              }
              if (p.signature.dynamicFn) {
                pp[p.signature.method] = true;
              }
            } else {
              if (p.model) {
                pp[p.model] = true;
              }
            }
          }
        }
        // Merge child _parentProps into this _parentProps
        if (n.templateContent) {
          var tpp = n.templateContent._parentProps;
          Polymer.Base.mixin(pp, tpp);
        }
      }
      return pp;
    },

    _prepElement: function(element) {
      Polymer.ResolveUrl.resolveAttrs(element, this._template.ownerDocument);
    },

    // instance-time

    _findAnnotatedNode: Polymer.Annotations.findAnnotatedNode,

    // marshal all teh things
    _marshalAnnotationReferences: function() {
      if (this._template) {
        this._marshalIdNodes();
        this._marshalAnnotatedNodes();
        this._marshalAnnotatedListeners();
      }
    },

    // push configuration references at configure time
    _configureAnnotationReferences: function() {
      var notes = this._notes;
      var nodes = this._nodes;
      for (var i=0; i<notes.length; i++) {
        var note = notes[i];
        var node = nodes[i];
        this._configureTemplateContent(note, node);
        this._configureCompoundBindings(note, node);
      }
    },

    // nested template contents have been stored prototypically to avoid
    // unnecessary duplication, here we put references to the
    // indirected contents onto the nested template instances
    _configureTemplateContent: function(note, node) {
      if (note.templateContent) {
        // note: we can rely on _nodes being set here and having the same
        // index as _notes
        node._content = note.templateContent;
      }
    },

    // Compound bindings utilize private storage on the node to store
    // the current state of each value that will be concatenated to generate
    // the final property/attribute/text value
    // Here we initialize the private storage array on the node with any
    // literal parts that won't change (could get fancy and use WeakMap),
    // and configure property bindings to children with the literal parts
    // (textContent and annotations were already initialized in the template)
    _configureCompoundBindings: function(note, node) {
      var bindings = note.bindings;
      for (var i=0; i<bindings.length; i++) {
        var binding = bindings[i];
        if (binding.isCompound) {
          // Create compound storage map
          var storage = node.__compoundStorage__ ||
            (node.__compoundStorage__ = {});
          var parts = binding.parts;
          // Copy literals from parts into storage for this binding
          var literals = new Array(parts.length);
          for (var j=0; j<parts.length; j++) {
            literals[j] = parts[j].literal;
          }
          var name = binding.name;
          storage[name] = literals;
          // Configure properties with their literal parts
          if (binding.literal && binding.kind == 'property') {
            if (node._configValue) {
              node._configValue(name, binding.literal);
            } else {
              node[name] = binding.literal;
            }
          }
        }
      }
    },

    // construct `$` map (from id annotations)
    _marshalIdNodes: function() {
      this.$ = {};
      for (var i=0, l=this._notes.length, a; (i<l) && (a=this._notes[i]); i++) {
        if (a.id) {
          this.$[a.id] = this._findAnnotatedNode(this.root, a);
        }
      }
    },

    // concretize `_nodes` map (from anonymous annotations)
    _marshalAnnotatedNodes: function() {
      if (this._notes && this._notes.length) {
        var r = new Array(this._notes.length);
        for (var i=0; i < this._notes.length; i++) {
          r[i] = this._findAnnotatedNode(this.root, this._notes[i]);
        }
        this._nodes = r;
      }
    },

    // install event listeners (from event annotations)
    _marshalAnnotatedListeners: function() {
      for (var i=0, l=this._notes.length, a; (i<l) && (a=this._notes[i]); i++) {
        if (a.events && a.events.length) {
          var node = this._findAnnotatedNode(this.root, a);
          for (var j=0, e$=a.events, e; (j<e$.length) && (e=e$[j]); j++) {
            this.listen(node, e.name, e.value);
          }
        }
      }
    }

  });
/**
   * Supports `listeners` object.
   *
   * Example:
   *
   *
   *     Polymer({
   *
   *       listeners: {
   *         // `click` events on the host are delegated to `clickHandler`
   *         'click': 'clickHandler'
   *       },
   *
   *       ...
   *
   *     });
   *
   *
   * @class standard feature: events
   *
   */

  Polymer.Base._addFeature({

    /**
     * Object containing entries specifying event listeners to create on each
     * instance of this element, where keys specify the event name and values
     * specify the name of the handler method to call on this prototype.
     *
     * Example:
     *
     *
     *     Polymer({
     *
     *       listeners: {
     *         // `click` events on the host are delegated to `clickHandler`
     *         'tap': 'tapHandler'
     *       },
     *
     *       ...
     *
     *     });
     */
    listeners: {},

    // TODO(sorvell): need to deprecate listening for a.b.
    // In the interim, we need to keep a map of listeners by node name
    // to avoid these string searches at instance time.
    _listenListeners: function(listeners) {
      var node, name, eventName;
      for (eventName in listeners) {
        if (eventName.indexOf('.') < 0) {
          node = this;
          name = eventName;
        } else {
          name = eventName.split('.');
          node = this.$[name[0]];
          name = name[1];
        }
        this.listen(node, name, listeners[eventName]);
      }
    },

    /**
     * Convenience method to add an event listener on a given element,
     * late bound to a named method on this element.
     *
     * @method listen
     * @param {Element} node Element to add event listener to.
     * @param {string} eventName Name of event to listen for.
     * @param {string} methodName Name of handler method on `this` to call.
     */
    listen: function(node, eventName, methodName) {
      var handler = this._recallEventHandler(this, eventName, node, methodName);
      // reuse cache'd handler
      if (!handler) {
        handler = this._createEventHandler(node, eventName, methodName);
      }
      // don't call _listen if we are already listening
      if (handler._listening) {
        return;
      }
      this._listen(node, eventName, handler);
      handler._listening = true;
    },

    _boundListenerKey: function(eventName, methodName) {
      return (eventName + ':' + methodName);
    },

    _recordEventHandler: function(host, eventName, target, methodName, handler) {
      var hbl = host.__boundListeners;
      if (!hbl) {
        hbl = host.__boundListeners = new WeakMap();
      }
      var bl = hbl.get(target);
      if (!bl) {
        bl = {};
        hbl.set(target, bl);
      }
      var key = this._boundListenerKey(eventName, methodName);
      bl[key] = handler;
    },

    _recallEventHandler: function(host, eventName, target, methodName) {
      var hbl = host.__boundListeners;
      if (!hbl) {
        return;
      }
      var bl = hbl.get(target);
      if (!bl) {
        return;
      }
      var key = this._boundListenerKey(eventName, methodName);
      return bl[key];
    },

    _createEventHandler: function(node, eventName, methodName) {
      var host = this;
      var handler = function(e) {
        if (host[methodName]) {
          host[methodName](e, e.detail);
        } else {
          host._warn(host._logf('_createEventHandler', 'listener method `' +
            methodName + '` not defined'));
        }
      };
      handler._listening = false;
      this._recordEventHandler(host, eventName, node, methodName, handler);
      return handler;
    },

    /**
     * Convenience method to remove an event listener from a given element,
     * late bound to a named method on this element.
     *
     * @method unlisten
     * @param {Element} node Element to remove event listener from.
     * @param {string} eventName Name of event to stop listening to.
     * @param {string} methodName Name of handler method on `this` to not call
     anymore.
     */
    unlisten: function(node, eventName, methodName) {
      // leave handler in map for cache purposes
      var handler = this._recallEventHandler(this, eventName, node, methodName);
      if (handler) {
        this._unlisten(node, eventName, handler);
        handler._listening = false;
      }
    },

    _listen: function(node, eventName, handler) {
      node.addEventListener(eventName, handler);
    },

    _unlisten: function(node, eventName, handler) {
      node.removeEventListener(eventName, handler);
    }
  });
(function() {

  'use strict';

  var wrap = Polymer.DomApi.wrap;

  // detect native touch action support
  var HAS_NATIVE_TA = typeof document.head.style.touchAction === 'string';
  var GESTURE_KEY = '__polymerGestures';
  var HANDLED_OBJ = '__polymerGesturesHandled';
  var TOUCH_ACTION = '__polymerGesturesTouchAction';
  // radius for tap and track
  var TAP_DISTANCE = 25;
  var TRACK_DISTANCE = 5;
  // number of last N track positions to keep
  var TRACK_LENGTH = 2;

  // Disabling "mouse" handlers for 2500ms is enough
  var MOUSE_TIMEOUT = 2500;
  var MOUSE_EVENTS = ['mousedown', 'mousemove', 'mouseup', 'click'];
  // an array of bitmask values for mapping MouseEvent.which to MouseEvent.buttons
  var MOUSE_WHICH_TO_BUTTONS = [0, 1, 4, 2];
  var MOUSE_HAS_BUTTONS = (function() {
    try {
      return new MouseEvent('test', {buttons: 1}).buttons === 1;
    } catch (e) {
      return false;
    }
  })();

  // Check for touch-only devices
  var IS_TOUCH_ONLY = navigator.userAgent.match(/iP(?:[oa]d|hone)|Android/);

  // touch will make synthetic mouse events
  // `preventDefault` on touchend will cancel them,
  // but this breaks `<input>` focus and link clicks
  // disable mouse handlers for MOUSE_TIMEOUT ms after
  // a touchend to ignore synthetic mouse events
  var mouseCanceller = function(mouseEvent) {
    // skip synthetic mouse events
    mouseEvent[HANDLED_OBJ] = {skip: true};
    // disable "ghost clicks"
    if (mouseEvent.type === 'click') {
      var path = Polymer.dom(mouseEvent).path;
      for (var i = 0; i < path.length; i++) {
        if (path[i] === POINTERSTATE.mouse.target) {
          return;
        }
      }
      mouseEvent.preventDefault();
      mouseEvent.stopPropagation();
    }
  };

  function setupTeardownMouseCanceller(setup) {
    for (var i = 0, en; i < MOUSE_EVENTS.length; i++) {
      en = MOUSE_EVENTS[i];
      if (setup) {
        document.addEventListener(en, mouseCanceller, true);
      } else {
        document.removeEventListener(en, mouseCanceller, true);
      }
    }
  }

  function ignoreMouse() {
    if (IS_TOUCH_ONLY) {
      return;
    }
    if (!POINTERSTATE.mouse.mouseIgnoreJob) {
      setupTeardownMouseCanceller(true);
    }
    var unset = function() {
      setupTeardownMouseCanceller();
      POINTERSTATE.mouse.target = null;
      POINTERSTATE.mouse.mouseIgnoreJob = null;
    };
    POINTERSTATE.mouse.mouseIgnoreJob =
      Polymer.Debounce(POINTERSTATE.mouse.mouseIgnoreJob, unset, MOUSE_TIMEOUT);
  }

  function hasLeftMouseButton(ev) {
    var type = ev.type;
    // exit early if the event is not a mouse event
    if (MOUSE_EVENTS.indexOf(type) === -1) {
      return false;
    }
    // ev.button is not reliable for mousemove (0 is overloaded as both left button and no buttons)
    // instead we use ev.buttons (bitmask of buttons) or fall back to ev.which (deprecated, 0 for no buttons, 1 for left button)
    if (type === 'mousemove') {
      // allow undefined for testing events
      var buttons = ev.buttons === undefined ? 1 : ev.buttons;
      if ((ev instanceof window.MouseEvent) && !MOUSE_HAS_BUTTONS) {
        buttons = MOUSE_WHICH_TO_BUTTONS[ev.which] || 0;
      }
      // buttons is a bitmask, check that the left button bit is set (1)
      return Boolean(buttons & 1);
    } else {
      // allow undefined for testing events
      var button = ev.button === undefined ? 0 : ev.button;
      // ev.button is 0 in mousedown/mouseup/click for left button activation
      return button === 0;
    }
  }

  function isSyntheticClick(ev) {
    if (ev.type === 'click') {
      // ev.detail is 0 for HTMLElement.click in most browsers
      if (ev.detail === 0) {
        return true;
      }
      // in the worst case, check that the x/y position of the click is within
      // the bounding box of the target of the event
      // Thanks IE 10 >:(
      var t = Gestures.findOriginalTarget(ev);
      var bcr = t.getBoundingClientRect();
      // use page x/y to account for scrolling
      var x = ev.pageX, y = ev.pageY;
      // ev is a synthetic click if the position is outside the bounding box of the target
      return !((x >= bcr.left && x <= bcr.right) && (y >= bcr.top && y <= bcr.bottom));
    }
    return false;
  }

  var POINTERSTATE = {
    mouse: {
      target: null,
      mouseIgnoreJob: null
    },
    touch: {
      x: 0,
      y: 0,
      id: -1,
      scrollDecided: false
    }
  };

  function firstTouchAction(ev) {
    var path = Polymer.dom(ev).path;
    var ta = 'auto';
    for (var i = 0, n; i < path.length; i++) {
      n = path[i];
      if (n[TOUCH_ACTION]) {
        ta = n[TOUCH_ACTION];
        break;
      }
    }
    return ta;
  }

  function trackDocument(stateObj, movefn, upfn) {
    stateObj.movefn = movefn;
    stateObj.upfn = upfn;
    document.addEventListener('mousemove', movefn);
    document.addEventListener('mouseup', upfn);
  }

  function untrackDocument(stateObj) {
    document.removeEventListener('mousemove', stateObj.movefn);
    document.removeEventListener('mouseup', stateObj.upfn);
    stateObj.movefn = null;
    stateObj.upfn = null;
  }

  var Gestures = {
    gestures: {},
    recognizers: [],

    deepTargetFind: function(x, y) {
      var node = document.elementFromPoint(x, y);
      var next = node;
      // this code path is only taken when native ShadowDOM is used
      // if there is a shadowroot, it may have a node at x/y
      // if there is not a shadowroot, exit the loop
      while (next && next.shadowRoot) {
        // if there is a node at x/y in the shadowroot, look deeper
        next = next.shadowRoot.elementFromPoint(x, y);
        if (next) {
          node = next;
        }
      }
      return node;
    },
    // a cheaper check than Polymer.dom(ev).path[0];
    findOriginalTarget: function(ev) {
      // shadowdom
      if (ev.path) {
        return ev.path[0];
      }
      // shadydom
      return ev.target;
    },
    handleNative: function(ev) {
      var handled;
      var type = ev.type;
      var node = wrap(ev.currentTarget);
      var gobj = node[GESTURE_KEY];
      if (!gobj) {
        return;
      }
      var gs = gobj[type];
      if (!gs) {
        return;
      }
      if (!ev[HANDLED_OBJ]) {
        ev[HANDLED_OBJ] = {};
        if (type.slice(0, 5) === 'touch') {
          var t = ev.changedTouches[0];
          if (type === 'touchstart') {
            // only handle the first finger
            if (ev.touches.length === 1) {
              POINTERSTATE.touch.id = t.identifier;
            }
          }
          if (POINTERSTATE.touch.id !== t.identifier) {
            return;
          }
          if (!HAS_NATIVE_TA) {
            if (type === 'touchstart' || type === 'touchmove') {
              Gestures.handleTouchAction(ev);
            }
          }
          // disable synth mouse events, unless this event is itself simulated
          if (type === 'touchend') {
            POINTERSTATE.mouse.target = Polymer.dom(ev).rootTarget;
            // ignore syntethic mouse events after a touch
            ignoreMouse();
          }
        }
      }
      handled = ev[HANDLED_OBJ];
      // used to ignore synthetic mouse events
      if (handled.skip) {
        return;
      }
      var recognizers = Gestures.recognizers;
      // reset recognizer state
      for (var i = 0, r; i < recognizers.length; i++) {
        r = recognizers[i];
        if (gs[r.name] && !handled[r.name]) {
          if (r.flow && r.flow.start.indexOf(ev.type) > -1 && r.reset) {
            r.reset();
          }
        }
      }
      // enforce gesture recognizer order
      for (i = 0, r; i < recognizers.length; i++) {
        r = recognizers[i];
        if (gs[r.name] && !handled[r.name]) {
          handled[r.name] = true;
          r[type](ev);
        }
      }
    },

    handleTouchAction: function(ev) {
      var t = ev.changedTouches[0];
      var type = ev.type;
      if (type === 'touchstart') {
        POINTERSTATE.touch.x = t.clientX;
        POINTERSTATE.touch.y = t.clientY;
        POINTERSTATE.touch.scrollDecided = false;
      } else if (type === 'touchmove') {
        if (POINTERSTATE.touch.scrollDecided) {
          return;
        }
        POINTERSTATE.touch.scrollDecided = true;
        var ta = firstTouchAction(ev);
        var prevent = false;
        var dx = Math.abs(POINTERSTATE.touch.x - t.clientX);
        var dy = Math.abs(POINTERSTATE.touch.y - t.clientY);
        if (!ev.cancelable) {
          // scrolling is happening
        } else if (ta === 'none') {
          prevent = true;
        } else if (ta === 'pan-x') {
          prevent = dy > dx;
        } else if (ta === 'pan-y') {
          prevent = dx > dy;
        }
        if (prevent) {
          ev.preventDefault();
        } else {
          Gestures.prevent('track');
        }
      }
    },

    // automate the event listeners for the native events
    add: function(node, evType, handler) {
      // SD polyfill: handle case where `node` is unwrapped, like `document`
      node = wrap(node);
      var recognizer = this.gestures[evType];
      var deps = recognizer.deps;
      var name = recognizer.name;
      var gobj = node[GESTURE_KEY];
      if (!gobj) {
        node[GESTURE_KEY] = gobj = {};
      }
      for (var i = 0, dep, gd; i < deps.length; i++) {
        dep = deps[i];
        // don't add mouse handlers on iOS because they cause gray selection overlays
        if (IS_TOUCH_ONLY && MOUSE_EVENTS.indexOf(dep) > -1) {
          continue;
        }
        gd = gobj[dep];
        if (!gd) {
          gobj[dep] = gd = {_count: 0};
        }
        if (gd._count === 0) {
          node.addEventListener(dep, this.handleNative);
        }
        gd[name] = (gd[name] || 0) + 1;
        gd._count = (gd._count || 0) + 1;
      }
      node.addEventListener(evType, handler);
      if (recognizer.touchAction) {
        this.setTouchAction(node, recognizer.touchAction);
      }
    },

    // automate event listener removal for native events
    remove: function(node, evType, handler) {
      // SD polyfill: handle case where `node` is unwrapped, like `document`
      node = wrap(node);
      var recognizer = this.gestures[evType];
      var deps = recognizer.deps;
      var name = recognizer.name;
      var gobj = node[GESTURE_KEY];
      if (gobj) {
        for (var i = 0, dep, gd; i < deps.length; i++) {
          dep = deps[i];
          gd = gobj[dep];
          if (gd && gd[name]) {
            gd[name] = (gd[name] || 1) - 1;
            gd._count = (gd._count || 1) - 1;
            if (gd._count === 0) {
              node.removeEventListener(dep, this.handleNative);
            }
          }
        }
      }
      node.removeEventListener(evType, handler);
    },

    register: function(recog) {
      this.recognizers.push(recog);
      for (var i = 0; i < recog.emits.length; i++) {
        this.gestures[recog.emits[i]] = recog;
      }
    },

    findRecognizerByEvent: function(evName) {
      for (var i = 0, r; i < this.recognizers.length; i++) {
        r = this.recognizers[i];
        for (var j = 0, n; j < r.emits.length; j++) {
          n = r.emits[j];
          if (n === evName) {
            return r;
          }
        }
      }
      return null;
    },

    // set scrolling direction on node to check later on first move
    // must call this before adding event listeners!
    setTouchAction: function(node, value) {
      if (HAS_NATIVE_TA) {
        node.style.touchAction = value;
      }
      node[TOUCH_ACTION] = value;
    },

    fire: function(target, type, detail) {
      var ev = Polymer.Base.fire(type, detail, {
        node: target,
        bubbles: true,
        cancelable: true
      });

      // forward `preventDefault` in a clean way
      if (ev.defaultPrevented) {
        var se = detail.sourceEvent;
        // sourceEvent may be a touch, which is not preventable this way
        if (se && se.preventDefault) {
          se.preventDefault();
        }
      }
    },

    prevent: function(evName) {
      var recognizer = this.findRecognizerByEvent(evName);
      if (recognizer.info) {
        recognizer.info.prevent = true;
      }
    },
    /**
     * Reset the 2500ms timeout on processing mouse input after detecting touch input.
     *
     * Touch inputs create synthesized mouse inputs anywhere from 0 to 2000ms after the touch.
     * This method should only be called during testing with simulated touch inputs.
     * Calling this method in production may cause duplicate taps or other gestures.
     *
     * @method resetMouseCanceller
     */
    resetMouseCanceller: function() {
      if (POINTERSTATE.mouse.mouseIgnoreJob) {
        POINTERSTATE.mouse.mouseIgnoreJob.complete();
      }
    }
  };

  Gestures.register({
    name: 'downup',
    deps: ['mousedown', 'touchstart', 'touchend'],
    flow: {
      start: ['mousedown', 'touchstart'],
      end: ['mouseup', 'touchend']
    },
    emits: ['down', 'up'],

    info: {
      movefn: null,
      upfn: null
    },

    reset: function() {
      untrackDocument(this.info);
    },

    mousedown: function(e) {
      if (!hasLeftMouseButton(e)) {
        return;
      }
      var t = Gestures.findOriginalTarget(e);
      var self = this;
      var movefn = function movefn(e) {
        if (!hasLeftMouseButton(e)) {
          self.fire('up', t, e);
          untrackDocument(self.info);
        }
      };
      var upfn = function upfn(e) {
        if (hasLeftMouseButton(e)) {
          self.fire('up', t, e);
        }
        untrackDocument(self.info);
      };
      trackDocument(this.info, movefn, upfn);
      this.fire('down', t, e);
    },
    touchstart: function(e) {
      this.fire('down', Gestures.findOriginalTarget(e), e.changedTouches[0]);
    },
    touchend: function(e) {
      this.fire('up', Gestures.findOriginalTarget(e), e.changedTouches[0]);
    },
    fire: function(type, target, event) {
      Gestures.fire(target, type, {
        x: event.clientX,
        y: event.clientY,
        sourceEvent: event,
        prevent: function(e) {
          return Gestures.prevent(e);
        }
      });
    }
  });

  Gestures.register({
    name: 'track',
    touchAction: 'none',
    deps: ['mousedown', 'touchstart', 'touchmove', 'touchend'],
    flow: {
      start: ['mousedown', 'touchstart'],
      end: ['mouseup', 'touchend']
    },
    emits: ['track'],

    info: {
      x: 0,
      y: 0,
      state: 'start',
      started: false,
      moves: [],
      addMove: function(move) {
        if (this.moves.length > TRACK_LENGTH) {
          this.moves.shift();
        }
        this.moves.push(move);
      },
      movefn: null,
      upfn: null,
      prevent: false
    },

    reset: function() {
      this.info.state = 'start';
      this.info.started = false;
      this.info.moves = [];
      this.info.x = 0;
      this.info.y = 0;
      this.info.prevent = false;
      untrackDocument(this.info);
    },

    hasMovedEnough: function(x, y) {
      if (this.info.prevent) {
        return false;
      }
      if (this.info.started) {
        return true;
      }
      var dx = Math.abs(this.info.x - x);
      var dy = Math.abs(this.info.y - y);
      return (dx >= TRACK_DISTANCE || dy >= TRACK_DISTANCE);
    },

    mousedown: function(e) {
      if (!hasLeftMouseButton(e)) {
        return;
      }
      var t = Gestures.findOriginalTarget(e);
      var self = this;
      var movefn = function movefn(e) {
        var x = e.clientX, y = e.clientY;
        if (self.hasMovedEnough(x, y)) {
          // first move is 'start', subsequent moves are 'move', mouseup is 'end'
          self.info.state = self.info.started ? (e.type === 'mouseup' ? 'end' : 'track') : 'start';
          if (self.info.state === 'start') {
            // iff tracking, always prevent tap
            Gestures.prevent('tap');
          }
          self.info.addMove({x: x, y: y});
          if (!hasLeftMouseButton(e)) {
            // always fire "end"
            self.info.state = 'end';
            untrackDocument(self.info);
          }
          self.fire(t, e);
          self.info.started = true;
        }
      };
      var upfn = function upfn(e) {
        if (self.info.started) {
          movefn(e);
        }

        // remove the temporary listeners
        untrackDocument(self.info);
      };
      // add temporary document listeners as mouse retargets
      trackDocument(this.info, movefn, upfn);
      this.info.x = e.clientX;
      this.info.y = e.clientY;
    },

    touchstart: function(e) {
      var ct = e.changedTouches[0];
      this.info.x = ct.clientX;
      this.info.y = ct.clientY;
    },

    touchmove: function(e) {
      var t = Gestures.findOriginalTarget(e);
      var ct = e.changedTouches[0];
      var x = ct.clientX, y = ct.clientY;
      if (this.hasMovedEnough(x, y)) {
        if (this.info.state === 'start') {
          // iff tracking, always prevent tap
          Gestures.prevent('tap');
        }
        this.info.addMove({x: x, y: y});
        this.fire(t, ct);
        this.info.state = 'track';
        this.info.started = true;
      }
    },

    touchend: function(e) {
      var t = Gestures.findOriginalTarget(e);
      var ct = e.changedTouches[0];
      // only trackend if track was started and not aborted
      if (this.info.started) {
        // reset started state on up
        this.info.state = 'end';
        this.info.addMove({x: ct.clientX, y: ct.clientY});
        this.fire(t, ct);
      }
    },

    fire: function(target, touch) {
      var secondlast = this.info.moves[this.info.moves.length - 2];
      var lastmove = this.info.moves[this.info.moves.length - 1];
      var dx = lastmove.x - this.info.x;
      var dy = lastmove.y - this.info.y;
      var ddx, ddy = 0;
      if (secondlast) {
        ddx = lastmove.x - secondlast.x;
        ddy = lastmove.y - secondlast.y;
      }
      return Gestures.fire(target, 'track', {
        state: this.info.state,
        x: touch.clientX,
        y: touch.clientY,
        dx: dx,
        dy: dy,
        ddx: ddx,
        ddy: ddy,
        sourceEvent: touch,
        hover: function() {
          return Gestures.deepTargetFind(touch.clientX, touch.clientY);
        }
      });
    }

  });

  Gestures.register({
    name: 'tap',
    deps: ['mousedown', 'click', 'touchstart', 'touchend'],
    flow: {
      start: ['mousedown', 'touchstart'],
      end: ['click', 'touchend']
    },
    emits: ['tap'],
    info: {
      x: NaN,
      y: NaN,
      prevent: false
    },
    reset: function() {
      this.info.x = NaN;
      this.info.y = NaN;
      this.info.prevent = false;
    },
    save: function(e) {
      this.info.x = e.clientX;
      this.info.y = e.clientY;
    },

    mousedown: function(e) {
      if (hasLeftMouseButton(e)) {
        this.save(e);
      }
    },
    click: function(e) {
      if (hasLeftMouseButton(e)) {
        this.forward(e);
      }
    },

    touchstart: function(e) {
      this.save(e.changedTouches[0]);
    },
    touchend: function(e) {
      this.forward(e.changedTouches[0]);
    },

    forward: function(e) {
      var dx = Math.abs(e.clientX - this.info.x);
      var dy = Math.abs(e.clientY - this.info.y);
      var t = Gestures.findOriginalTarget(e);
      // dx,dy can be NaN if `click` has been simulated and there was no `down` for `start`
      if (isNaN(dx) || isNaN(dy) || (dx <= TAP_DISTANCE && dy <= TAP_DISTANCE) || isSyntheticClick(e)) {
        // prevent taps from being generated if an event has canceled them
        if (!this.info.prevent) {
          Gestures.fire(t, 'tap', {
            x: e.clientX,
            y: e.clientY,
            sourceEvent: e
          });
        }
      }
    }
  });

  var DIRECTION_MAP = {
    x: 'pan-x',
    y: 'pan-y',
    none: 'none',
    all: 'auto'
  };

  Polymer.Base._addFeature({

    _setupGestures: function() {
      this.__polymerGestures = null;
    },

    // override _listen to handle gestures
    _listen: function(node, eventName, handler) {
      if (Gestures.gestures[eventName]) {
        Gestures.add(node, eventName, handler);
      } else {
        node.addEventListener(eventName, handler);
      }
    },
    // override _unlisten to handle gestures
    _unlisten: function(node, eventName, handler) {
      if (Gestures.gestures[eventName]) {
        Gestures.remove(node, eventName, handler);
      } else {
        node.removeEventListener(eventName, handler);
      }
    },
    /**
     * Override scrolling behavior to all direction, one direction, or none.
     *
     * Valid scroll directions:
     *   - 'all': scroll in any direction
     *   - 'x': scroll only in the 'x' direction
     *   - 'y': scroll only in the 'y' direction
     *   - 'none': disable scrolling for this node
     *
     * @method setScrollDirection
     * @param {String=} direction Direction to allow scrolling
     * Defaults to `all`.
     * @param {HTMLElement=} node Element to apply scroll direction setting.
     * Defaults to `this`.
     */
    setScrollDirection: function(direction, node) {
      node = node || this;
      Gestures.setTouchAction(node, DIRECTION_MAP[direction] || 'auto');
    }
  });

  // export

  Polymer.Gestures = Gestures;

})();
Polymer.Base._addFeature({

    /**
     * Convenience method to run `querySelector` on this local DOM scope.
     *
     * This function calls `Polymer.dom(this.root).querySelector(slctr)`.
     *
     * @method $$
     * @param {string} slctr Selector to run on this local DOM scope
     * @return {Element} Element found by the selector, or null if not found.
     */
    $$: function(slctr) {
      return Polymer.dom(this.root).querySelector(slctr);
    },

    /**
     * Toggles a CSS class on or off.
     *
     * @method toggleClass
     * @param {String} name CSS class name
     * @param {boolean=} bool Boolean to force the class on or off.
     *    When unspecified, the state of the class will be reversed.
     * @param {HTMLElement=} node Node to target.  Defaults to `this`.
     */
    toggleClass: function(name, bool, node) {
      node = node || this;
      if (arguments.length == 1) {
        bool = !node.classList.contains(name);
      }
      if (bool) {
        Polymer.dom(node).classList.add(name);
      } else {
        Polymer.dom(node).classList.remove(name);
      }
    },

    /**
     * Toggles an HTML attribute on or off.
     *
     * @method toggleAttribute
     * @param {String} name HTML attribute name
     * @param {boolean=} bool Boolean to force the attribute on or off.
     *    When unspecified, the state of the attribute will be reversed.
     * @param {HTMLElement=} node Node to target.  Defaults to `this`.
     */
    toggleAttribute: function(name, bool, node) {
      node = node || this;
      if (arguments.length == 1) {
        bool = !node.hasAttribute(name);
      }
      if (bool) {
        Polymer.dom(node).setAttribute(name, '');
      } else {
        Polymer.dom(node).removeAttribute(name);
      }
    },

    /**
     * Removes a class from one node, and adds it to another.
     *
     * @method classFollows
     * @param {String} name CSS class name
     * @param {HTMLElement} toElement New element to add the class to.
     * @param {HTMLElement} fromElement Old element to remove the class from.
     */
    classFollows: function(name, toElement, fromElement) {
      if (fromElement) {
        Polymer.dom(fromElement).classList.remove(name);
      }
      if (toElement) {
        Polymer.dom(toElement).classList.add(name);
      }
    },

    /**
     * Removes an HTML attribute from one node, and adds it to another.
     *
     * @method attributeFollows
     * @param {String} name HTML attribute name
     * @param {HTMLElement} toElement New element to add the attribute to.
     * @param {HTMLElement} fromElement Old element to remove the attribute from.
     */
    attributeFollows: function(name, toElement, fromElement) {
      if (fromElement) {
        Polymer.dom(fromElement).removeAttribute(name);
      }
      if (toElement) {
        Polymer.dom(toElement).setAttribute(name, '');
      }
    },

    /**
     * Returns a list of nodes that are the effective childNodes. The effective
     * childNodes list is the same as the element's childNodes except that
     * any `<content>` elements are replaced with the list of nodes distributed
     * to the `<content>`, the result of its `getDistributedNodes` method.
     *
     * @method getEffectiveChildNodes
     * @return {Array<Node>} List of effctive child nodes.
     */
    getEffectiveChildNodes: function() {
      return Polymer.dom(this).getEffectiveChildNodes();
    },

    /**
     * Returns a list of elements that are the effective children. The effective
     * children list is the same as the element's children except that
     * any `<content>` elements are replaced with the list of elements
     * distributed to the `<content>`.
     *
     * @method getEffectiveChildren
     * @return {Array<Node>} List of effctive children.
     */
    getEffectiveChildren: function() {
      var list = Polymer.dom(this).getEffectiveChildNodes();
      return list.filter(function(n) {
        return (n.nodeType === Node.ELEMENT_NODE);
      });
    },

    /**
     * Returns a string of text content that is the concatenation of the
     * text content's of the element's effective childNodes (the elements
     * returned by <a href="#getEffectiveChildNodes>getEffectiveChildNodes</a>.
     *
     * @method getEffectiveTextContent
     * @return {Array<Node>} List of effctive children.
     */
    getEffectiveTextContent: function() {
      var cn = this.getEffectiveChildNodes();
      var tc = [];
      for (var i=0, c; (c = cn[i]); i++) {
        if (c.nodeType !== Node.COMMENT_NODE) {
          tc.push(Polymer.dom(c).textContent);
        }
      }
      return tc.join('');
    },

    queryEffectiveChildren: function(slctr) {
      var e$ = Polymer.dom(this).queryDistributedElements(slctr);
      return e$ && e$[0];
    },

    queryAllEffectiveChildren: function(slctr) {
      return Polymer.dom(this).queryDistributedElements(slctr);
    },

    /**
     * Returns a list of nodes distributed to this element's `<content>`.
     *
     * If this element contains more than one `<content>` in its local DOM,
     * an optional selector may be passed to choose the desired content.
     *
     * @method getContentChildNodes
     * @param {String=} slctr CSS selector to choose the desired
     *   `<content>`.  Defaults to `content`.
     * @return {Array<Node>} List of distributed nodes for the `<content>`.
     */
    getContentChildNodes: function(slctr) {
      var content = Polymer.dom(this.root).querySelector(slctr || 'content');
      return content ? Polymer.dom(content).getDistributedNodes() : [];
    },

    /**
     * Returns a list of element children distributed to this element's
     * `<content>`.
     *
     * If this element contains more than one `<content>` in its
     * local DOM, an optional selector may be passed to choose the desired
     * content.  This method differs from `getContentChildNodes` in that only
     * elements are returned.
     *
     * @method getContentChildNodes
     * @param {String=} slctr CSS selector to choose the desired
     *   `<content>`.  Defaults to `content`.
     * @return {Array<HTMLElement>} List of distributed nodes for the
     *   `<content>`.
     */
    getContentChildren: function(slctr) {
      return this.getContentChildNodes(slctr).filter(function(n) {
        return (n.nodeType === Node.ELEMENT_NODE);
      });
    },


    /**
     * Dispatches a custom event with an optional detail value.
     *
     * @method fire
     * @param {String} type Name of event type.
     * @param {*=} detail Detail value containing event-specific
     *   payload.
     * @param {Object=} options Object specifying options.  These may include:
     *  `bubbles` (boolean, defaults to `true`),
     *  `cancelable` (boolean, defaults to false), and
     *  `node` on which to fire the event (HTMLElement, defaults to `this`).
     * @return {CustomEvent} The new event that was fired.
     */
    fire: function(type, detail, options) {
      options = options || Polymer.nob;
      var node = options.node || this;
      detail = (detail === null || detail === undefined) ? {} : detail;
      var bubbles = options.bubbles === undefined ? true : options.bubbles;
      var cancelable = Boolean(options.cancelable);
      var useCache = options._useCache;
      var event = this._getEvent(type, bubbles, cancelable, useCache);
      event.detail = detail;
      if (useCache) {
        this.__eventCache[type] = null;
      }
      node.dispatchEvent(event);
      if (useCache) {
        this.__eventCache[type] = event;
      }
      return event;
    },

    __eventCache: {},

    // NOTE: We optionally cache event objects for efficiency during high
    // freq. opts. This option cannot be used for events which may have
    // `stopPropagation` called on them. On Chrome and Safari (but not FF)
    // if `stopPropagation` is called, the event cannot be reused. It does not
    // dispatch again.
    _getEvent: function(type, bubbles, cancelable, useCache) {
      var event = useCache && this.__eventCache[type];
      if (!event || ((event.bubbles != bubbles) ||
          (event.cancelable != cancelable))) {
        event = new Event(type, {
          bubbles: Boolean(bubbles),
          cancelable: cancelable
        });
      }
      return event;
    },


    /**
     * Runs a callback function asyncronously.
     *
     * By default (if no waitTime is specified), async callbacks are run at
     * microtask timing, which will occur before paint.
     *
     * @method async
     * @param {Function} callback The callback function to run, bound to `this`.
     * @param {number=} waitTime Time to wait before calling the
     *   `callback`.  If unspecified or 0, the callback will be run at microtask
     *   timing (before paint).
     * @return {number} Handle that may be used to cancel the async job.
     */
    async: function(callback, waitTime) {
      var self = this;
      return Polymer.Async.run(function() {
        callback.call(self);
      }, waitTime);
    },

    /**
     * Cancels an async operation started with `async`.
     *
     * @method cancelAsync
     * @param {number} handle Handle returned from original `async` call to
     *   cancel.
     */
    cancelAsync: function(handle) {
      Polymer.Async.cancel(handle);
    },

    /**
     * Removes an item from an array, if it exists.
     *
     * If the array is specified by path, a change notification is
     * generated, so that observers, data bindings and computed
     * properties watching that path can update.
     *
     * If the array is passed directly, **no change
     * notification is generated**.
     *
     * @method arrayDelete
     * @param {String|Array} path Path to array from which to remove the item
     *   (or the array itself).
     * @param {any} item Item to remove.
     * @return {Array} Array containing item removed.
     */
    arrayDelete: function(path, item) {
      var index;
      if (Array.isArray(path)) {
        index = path.indexOf(item);
        if (index >= 0) {
          return path.splice(index, 1);
        }
      } else {
        var arr = this._get(path);
        index = arr.indexOf(item);
        if (index >= 0) {
          return this.splice(path, index, 1);
        }
      }
    },

    /**
     * Cross-platform helper for setting an element's CSS `transform` property.
     *
     * @method transform
     * @param {String} transform Transform setting.
     * @param {HTMLElement=} node Element to apply the transform to.
     * Defaults to `this`
     */
    transform: function(transform, node) {
      node = node || this;
      node.style.webkitTransform = transform;
      node.style.transform = transform;
    },

    /**
     * Cross-platform helper for setting an element's CSS `translate3d`
     * property.
     *
     * @method translate3d
     * @param {number} x X offset.
     * @param {number} y Y offset.
     * @param {number} z Z offset.
     * @param {HTMLElement=} node Element to apply the transform to.
     * Defaults to `this`.
     */
    translate3d: function(x, y, z, node) {
      node = node || this;
      this.transform('translate3d(' + x + ',' + y + ',' + z + ')', node);
    },

    /**
     * Convenience method for importing an HTML document imperatively.
     *
     * This method creates a new `<link rel="import">` element with
     * the provided URL and appends it to the document to start loading.
     * In the `onload` callback, the `import` property of the `link`
     * element will contain the imported document contents.
     *
     * @method importHref
     * @param {string} href URL to document to load.
     * @param {Function} onload Callback to notify when an import successfully
     *   loaded.
     * @param {Function} onerror Callback to notify when an import
     *   unsuccessfully loaded.
     * @param {boolean} optAsync True if the import should be loaded `async`.
     *   Defaults to `false`.
     * @return {HTMLLinkElement} The link element for the URL to be loaded.
     */
    importHref: function(href, onload, onerror, optAsync) {
      var l = document.createElement('link');
      l.rel = 'import';
      l.href = href;

      optAsync = Boolean(optAsync);
      if (optAsync) {
        l.setAttribute('async', '');
      }

      var self = this;
      if (onload) {
        l.onload = function(e) {
          return onload.call(self, e);
        }
      }
      if (onerror) {
        l.onerror = function(e) {
          return onerror.call(self, e);
        }
      }
      document.head.appendChild(l);
      return l;
    },

    /**
     * Convenience method for creating an element and configuring it.
     *
     * @method create
     * @param {string} tag HTML element tag to create.
     * @param {Object} props Object of properties to configure on the
     *    instance.
     * @return {Element} Newly created and configured element.
     */
    create: function(tag, props) {
      var elt = document.createElement(tag);
      if (props) {
        for (var n in props) {
          elt[n] = props[n];
        }
      }
      return elt;
    },

    /**
     * Checks whether an element is in this element's light DOM tree.
     *
     * @method isLightDescendant
     * @param {?Node} node The element to be checked.
     * @return {Boolean} true if node is in this element's light DOM tree.
     */
    isLightDescendant: function(node) {
      return this !== node && this.contains(node) &&
          Polymer.dom(this).getOwnerRoot() === Polymer.dom(node).getOwnerRoot();
    },

    /**
     * Checks whether an element is in this element's local DOM tree.
     *
     * @method isLocalDescendant
     * @param {HTMLElement=} node The element to be checked.
     * @return {Boolean} true if node is in this element's local DOM tree.
     */
    isLocalDescendant: function(node) {
      return this.root === Polymer.dom(node).getOwnerRoot();
    }

  });
Polymer.Bind = {

    // for prototypes (usually)
    prepareModel: function(model) {
      Polymer.Base.mixin(model, this._modelApi);
    },

    _modelApi: {

      _notifyChange: function(source, event, value) {
        value = value === undefined ? this[source] : value;
        event = event || Polymer.CaseMap.camelToDashCase(source) + '-changed';
        this.fire(event, {value: value},
          {bubbles: false, cancelable: false, _useCache: true});
      },

      // TODO(sjmiles): removing _notifyListener from here breaks accessors.html
      // as a standalone lib. This is temporary, as standard/configure.html
      // installs it's own version on Polymer.Base, and we need that to work
      // right now.
      // NOTE: exists as a hook for processing listeners
      /*
      _notifyListener: function(fn, e) {
        // NOTE: pass e.target because e.target can get lost if this function
        // is queued asynchrously
        return fn.call(this, e, e.target);
      },
      */

      // Called from accessors, where effects is pre-stored
      // in the closure for the accessor for efficiency
      _propertySetter: function(property, value, effects, fromAbove) {
        var old = this.__data__[property];
        // NaN is always not equal to itself,
        // if old and value are both NaN we treat them as equal
        // x === x is 10x faster, and equivalent to !isNaN(x)
        if (old !== value && (old === old || value === value)) {
          this.__data__[property] = value;
          if (typeof value == 'object') {
            this._clearPath(property);
          }
          if (this._propertyChanged) {
            this._propertyChanged(property, value, old);
          }
          if (effects) {
            this._effectEffects(property, value, effects, old, fromAbove);
          }
        }
        return old;
      },

      // Called during _applyConfig (well-known downward data-flow hot path)
      // in order to avoid firing notify events
      // TODO(kschaaf): downward bindings (e.g. _applyEffectValue) should also
      // use non-notifying setters but right now that would require looking
      // up readOnly property config in the hot-path
      __setProperty: function(property, value, quiet, node) {
        node = node || this;
        var effects = node._propertyEffects && node._propertyEffects[property];
        if (effects) {
          node._propertySetter(property, value, effects, quiet);
        } else {
          node[property] = value;
        }
      },

      _effectEffects: function(property, value, effects, old, fromAbove) {
        for (var i=0, l=effects.length, fx; (i<l) && (fx=effects[i]); i++) {
          fx.fn.call(this, property, value, fx.effect, old, fromAbove);
        }
      },

      _clearPath: function(path) {
        for (var prop in this.__data__) {
          if (prop.indexOf(path + '.') === 0) {
            this.__data__[prop] = undefined;
          }
        }
      }

    },

    // a prepared model can acquire effects

    ensurePropertyEffects: function(model, property) {
      if (!model._propertyEffects) {
        model._propertyEffects = {};
      }
      var fx = model._propertyEffects[property];
      if (!fx) {
        fx = model._propertyEffects[property] = [];
      }
      return fx;
    },

    addPropertyEffect: function(model, property, kind, effect) {
      var fx = this.ensurePropertyEffects(model, property);
      var propEffect = {
        kind: kind,
        effect: effect,
        fn: Polymer.Bind['_' + kind + 'Effect']
      };
      fx.push(propEffect);
      return propEffect;
    },

    createBindings: function(model) {
      //console.group(model.is);
      // map of properties to effects
      var fx$ = model._propertyEffects;
      if (fx$) {
        // for each property with effects
        for (var n in fx$) {
          // array of effects
          var fx = fx$[n];
          // effects have priority
          fx.sort(this._sortPropertyEffects);
          // create accessors
          this._createAccessors(model, n, fx);
        }
      }
      //console.groupEnd();
    },

    _sortPropertyEffects: (function() {
      // TODO(sjmiles): EFFECT_ORDER buried this way is not ideal,
      // but presumably the sort method is going to be a hot path and not
      // have a `this`. There is also a problematic dependency on effect.kind
      // values here, which are otherwise pluggable.
      var EFFECT_ORDER = {
        'compute': 0,
        'annotation': 1,
        'annotatedComputation': 2,
        'reflect': 3,
        'notify': 4,
        'observer': 5,
        'complexObserver': 6,
        'function': 7
      };
      return function(a, b) {
        return EFFECT_ORDER[a.kind] - EFFECT_ORDER[b.kind];
      };
    })(),

    // create accessors that implement effects

    _createAccessors: function(model, property, effects) {
      var defun = {
        get: function() {
          // TODO(sjmiles): elide delegation for performance, good ROI?
          return this.__data__[property];
        }
      };
      var setter = function(value) {
        this._propertySetter(property, value, effects);
      };
      // ReadOnly properties have a private setter only
      // TODO(kschaaf): Per current Bind factoring, we shouldn't
      // be interrogating the prototype here
      // TODO(sorvell): we want to avoid using `getPropertyInfo` here, but
      // this requires more data in `_propertyInfo`
      var info = model.getPropertyInfo && model.getPropertyInfo(property);
      if (info && info.readOnly) {
        // Computed properties are read-only (no property setter), but also don't
        // need a private setter since they should not be called by the user
        if (!info.computed) {
          model['_set' + this.upper(property)] = setter;
        }
      } else {
        defun.set = setter;
      }
      Object.defineProperty(model, property, defun);
    },

    upper: function(name) {
      return name[0].toUpperCase() + name.substring(1);
    },

    _addAnnotatedListener: function(model, index, property, path, event, negated) {
      if (!model._bindListeners) {
        model._bindListeners = [];
      }
      var fn = this._notedListenerFactory(property, path,
        this._isStructured(path), negated);
      var eventName = event ||
        (Polymer.CaseMap.camelToDashCase(property) + '-changed');
      model._bindListeners.push({
        index: index,
        property: property,
        path: path,
        changedFn: fn,
        event: eventName
      });
    },

    _isStructured: function(path) {
      return path.indexOf('.') > 0;
    },

    _isEventBogus: function(e, target) {
      return e.path && e.path[0] !== target;
    },

    _notedListenerFactory: function(property, path, isStructured, negated) {
      return function(target, value, targetPath) {
        if (targetPath) {
          this._notifyPath(this._fixPath(path, property, targetPath), value);
        } else {
          // TODO(sorvell): even though we have a `value` argument, we *must*
          // lookup the current value of the property. Multiple listeners and
          // queued events during configuration can theoretically lead to
          // divergence of the passed value from the current value, but we
          // really need to track down a specific case where this happens.
          value = target[property];

          if (negated) {
            value = !value;
          }

          if (!isStructured) {
            this[path] = value;
          } else {
            // TODO(kschaaf): dirty check avoids null references when the object has gone away
            if (this.__data__[path] != value) {
              this.set(path, value);
            }
          }
        }
      };
    },
    // for instances

    prepareInstance: function(inst) {
      inst.__data__ = Object.create(null);
    },

    setupBindListeners: function(inst) {
      var b$ = inst._bindListeners;
      for (var i=0, l=b$.length, info; (i<l) && (info=b$[i]); i++) {
        // Property listeners:
        // <node>.on.<property>-changed: <path]> = e.detail.value
        //console.log('[_setupBindListener]: [%s][%s] listening for [%s][%s-changed]', this.localName, info.path, info.id || info.index, info.property);
        //
        // TODO(sorvell): fix templatizer to support this before uncommenting
        // Optimization: only add bind listeners if the bound property is notifying...
        var node = inst._nodes[info.index];
        //var p = node._propertyInfo && node._propertyInfo[info.property];
        //if (node._prepParentProperties || !node._propertyInfo || (p && p.notify)) {
          this._addNotifyListener(node, inst, info.event, info.changedFn);
        //}
      }
    },

    // TODO(sorvell): note, adding these synchronously may impact performance,
    // measure and consider if we can defer until after first paint in some cases at least.
    _addNotifyListener: function(element, context, event, changedFn) {
      element.addEventListener(event, function(e) {
        return context._notifyListener(changedFn, e);
      });
    }
  };
Polymer.Base.extend(Polymer.Bind, {

    _shouldAddListener: function(effect) {
      return effect.name &&
             effect.kind != 'attribute' &&
             effect.kind != 'text' &&
             !effect.isCompound &&
             effect.parts[0].mode === '{';
    },

    _annotationEffect: function(source, value, effect) {
      if (source != effect.value) {
        value = this._get(effect.value);
        this.__data__[effect.value] = value;
      }
      this._applyEffectValue(effect, value);
    },

    _reflectEffect: function(source, value, effect) {
      this.reflectPropertyToAttribute(source, effect.attribute, value);
    },

    _notifyEffect: function(source, value, effect, old, fromAbove) {
      if (!fromAbove) {
        this._notifyChange(source, effect.event, value);
      }
    },

    // Raw effect for extension
    _functionEffect: function(source, value, fn, old, fromAbove) {
      fn.call(this, source, value, old, fromAbove);
    },

    _observerEffect: function(source, value, effect, old) {
      var fn = this[effect.method];
      if (fn) {
        fn.call(this, value, old);
      } else {
        this._warn(this._logf('_observerEffect', 'observer method `' +
          effect.method + '` not defined'));
      }
    },

    _complexObserverEffect: function(source, value, effect) {
      var fn = this[effect.method];
      if (fn) {
        var args = Polymer.Bind._marshalArgs(this.__data__, effect, source, value);
        if (args) {
          fn.apply(this, args);
        }
      } else if (effect.dynamicFn) {
        // dynamic functions can be just like every other property `undefined`
        // so we MUST ignore an undefined value here. (That's totally the
        // same guard we use within `_marshalArgs` and part of the spec.)
      } else {
        this._warn(this._logf('_complexObserverEffect', 'observer method `' +
          effect.method + '` not defined'));
      }
    },

    _computeEffect: function(source, value, effect) {
      var fn = this[effect.method];
      if (fn) {
        var args = Polymer.Bind._marshalArgs(this.__data__, effect, source, value);
        if (args) {
          var computedvalue = fn.apply(this, args);
          this.__setProperty(effect.name, computedvalue);
        }
      } else if (effect.dynamicFn) {
        // dynamic functions can be just like every other property `undefined`
        // so we MUST ignore an undefined value here. (That's totally the
        // same guard we use within `_marshalArgs` and part of the spec.)
      } else {
        this._warn(this._logf('_computeEffect', 'compute method `' +
          effect.method + '` not defined'));
      }
    },

    _annotatedComputationEffect: function(source, value, effect) {
      var computedHost = this._rootDataHost || this;
      var fn = computedHost[effect.method];
      if (fn) {
        var args = Polymer.Bind._marshalArgs(this.__data__, effect, source, value);
        if (args) {
          var computedvalue = fn.apply(computedHost, args);
          this._applyEffectValue(effect, computedvalue);
        }
      } else if (effect.dynamicFn) {
        // dynamic functions can be just like every other property `undefined`
        // so we MUST ignore an undefined value here. (That's totally the
        // same guard we use within `_marshalArgs` and part of the spec.)
      } else {
        computedHost._warn(computedHost._logf('_annotatedComputationEffect',
          'compute method `' + effect.method + '` not defined'));
      }
    },

    // path & value are used to fill in wildcard descriptor when effect is
    // being called as a result of a path notification
    _marshalArgs: function(model, effect, path, value) {
      var values = [];
      var args = effect.args;
      // Actually we should return early as soon as we see an `undefined`,
      // but dom-repeat relies on this behavior.
      var bailoutEarly = (args.length > 1 || effect.dynamicFn);
      for (var i=0, l=args.length; i<l; i++) {
        var arg = args[i];
        var name = arg.name;
        var v;
        if (arg.literal) {
          v = arg.value;
        } else if (path === name) {
          v = value;
        } else {
          // Take advantage of the fact that all values sent through the path
          // notifications system are cached on the model. Trivially, all the
          // user properties can be looked up there as well.
          v = model[name];
          if (v === undefined && arg.structured) {
            // All initial values and base assignments don't go through the
            // notifications API, so we must construct/evaluate the correct
            // value. (E.g. you assign a new object to `this.foo`, but your
            // observer actually listens to `foo.bar.quux`)
            v = Polymer.Base._get(name, model);
          }
        }
        if (bailoutEarly && v === undefined) {
          return;
        }
        if (arg.wildcard) {
          // Only send the actual path changed info if the change that
          // caused the observer to run matches this arg. Note that this holds
          // also true when `path === name`. We can skip this check b/c then
          // `name` and `v` already have the values we want.
          // Read the following as: `head(path) === name`.
          var matches = path.indexOf(name + '.') === 0;
          values[i] = {
            path: matches ? path : name,
            value: matches ? value : v,
            base: v
          };
        } else {
          values[i] = v;
        }
      }
      return values;
    }

  });
/**
   * Support for property side effects.
   *
   * Key for effect objects:
   *
   * property | ann | anCmp | cmp | obs | cplxOb | description
   * ---------|-----|-------|-----|-----|--------|----------------------------------------
   * method   |     | X     | X   | X   | X      | function name to call on instance
   * args     |     | X     | X   |     | X      | arg descriptors for triggers of fn
   * trigger  |     | X     | X   |     | X      | describes triggering dependency (one of args)
   * property |     |       | X   | X   |        | property for effect to set or get
   * name     | X   |       |     |     |        | annotation value (text inside {{...}})
   * kind     | X   | X     |     |     |        | binding type (property or attribute)
   * index    | X   | X     |     |     |        | node index to set
   *
   */

  Polymer.Base._addFeature({

    _addPropertyEffect: function(property, kind, effect) {
      var prop = Polymer.Bind.addPropertyEffect(this, property, kind, effect);
      // memoize path function for faster lookup.
      prop.pathFn = this['_' + prop.kind + 'PathEffect'];
    },

    // prototyping

    _prepEffects: function() {
      Polymer.Bind.prepareModel(this);
      this._addAnnotationEffects(this._notes);
    },

    _prepBindings: function() {
      Polymer.Bind.createBindings(this);
    },

    _addPropertyEffects: function(properties) {
      if (properties) {
        for (var p in properties) {
          var prop = properties[p];
          if (prop.observer) {
            this._addObserverEffect(p, prop.observer);
          }
          if (prop.computed) {
            // Computed properties are implicitly readOnly
            prop.readOnly = true;
            this._addComputedEffect(p, prop.computed);
          }
          if (prop.notify) {
            this._addPropertyEffect(p, 'notify', {
              event: Polymer.CaseMap.camelToDashCase(p) + '-changed'});
          }
          if (prop.reflectToAttribute) {
            var attr = Polymer.CaseMap.camelToDashCase(p);
            if (attr[0] === '-') {
              this._warn(this._logf('_addPropertyEffects', 'Property ' + p + ' cannot be reflected to attribute ' + attr + ' because "-" is not a valid starting attribute name. Use a lowercase first letter for the property instead.'));
            } else {
              this._addPropertyEffect(p, 'reflect', {
                attribute: attr
              });
            }
          }
          if (prop.readOnly) {
            // Ensure accessor is created
            Polymer.Bind.ensurePropertyEffects(this, p);
          }
        }
      }
    },

    _addComputedEffect: function(name, expression) {
      var sig = this._parseMethod(expression);

      var dynamicFn = sig.dynamicFn;

      for (var i=0, arg; (i<sig.args.length) && (arg=sig.args[i]); i++) {
        this._addPropertyEffect(arg.model, 'compute', {
          method: sig.method,
          args: sig.args,
          trigger: arg,
          name: name,
          dynamicFn: dynamicFn
        });
      }
      if (dynamicFn) {
        this._addPropertyEffect(sig.method, 'compute', {
          method: sig.method,
          args: sig.args,
          trigger: null,
          name: name,
          dynamicFn: dynamicFn
        });
      }
    },

    _addObserverEffect: function(property, observer) {
      this._addPropertyEffect(property, 'observer', {
        method: observer,
        property: property
      });
    },

    _addComplexObserverEffects: function(observers) {
      if (observers) {
        for (var i=0, o; (i<observers.length) && (o=observers[i]); i++)  {
          this._addComplexObserverEffect(o);
        }
      }
    },

    _addComplexObserverEffect: function(observer) {
      var sig = this._parseMethod(observer);

      if (!sig) {
        throw new Error("Malformed observer expression '" + observer + "'");
      }

      var dynamicFn = sig.dynamicFn;

      for (var i=0, arg; (i<sig.args.length) && (arg=sig.args[i]); i++) {
        this._addPropertyEffect(arg.model, 'complexObserver', {
          method: sig.method,
          args: sig.args,
          trigger: arg,
          dynamicFn: dynamicFn
        });
      }
      if (dynamicFn) {
        this._addPropertyEffect(sig.method, 'complexObserver', {
          method: sig.method,
          args: sig.args,
          trigger: null,
          dynamicFn: dynamicFn
        });
      }
    },

    _addAnnotationEffects: function(notes) {
      // process annotations that have been parsed from template
      for (var i=0, note; (i<notes.length) && (note=notes[i]); i++)  {
        // where to find the node in the concretized list
        var b$ = note.bindings;
        for (var j=0, binding; (j<b$.length) && (binding=b$[j]); j++) {
          this._addAnnotationEffect(binding, i);
        }
      }
    },

    _addAnnotationEffect: function(note, index) {
      // TODO(sjmiles): annotations have 'effects' proper and 'listener'
      if (Polymer.Bind._shouldAddListener(note)) {
        // <node>.on.<dash-case-property>-changed: <path> = e.detail.value
        Polymer.Bind._addAnnotatedListener(this, index,
          note.name, note.parts[0].value, note.parts[0].event, note.parts[0].negate);
      }
      for (var i=0; i<note.parts.length; i++) {
        var part = note.parts[i];
        if (part.signature) {
          this._addAnnotatedComputationEffect(note, part, index);
        } else if (!part.literal) {
          // add 'annotation' binding effect for property 'model'
          if (note.kind === 'attribute' && note.name[0] === '-') {
            this._warn(this._logf('_addAnnotationEffect', 'Cannot set attribute ' + note.name + ' because "-" is not a valid attribute starting character'));
          } else {
            this._addPropertyEffect(part.model, 'annotation', {
              kind: note.kind,
              index: index,
              name: note.name,
              propertyName: note.propertyName,
              value: part.value,
              isCompound: note.isCompound,
              compoundIndex: part.compoundIndex,
              event: part.event,
              customEvent: part.customEvent,
              negate: part.negate
            });
          }
        }
      }
    },

    _addAnnotatedComputationEffect: function(note, part, index) {
      var sig = part.signature;
      if (sig.static) {
        this.__addAnnotatedComputationEffect('__static__', index, note, part, null);
      } else {
        for (var i=0, arg; (i<sig.args.length) && (arg=sig.args[i]); i++) {
          if (!arg.literal) {
            this.__addAnnotatedComputationEffect(arg.model, index, note, part,
              arg);
          }
        }
        if (sig.dynamicFn) {
          // trigger=null is sufficient as long as we don't allow paths to be
          // used. If we change our mind, we must first implement this in the
          // effects anyway where we basically do a `fn = this[methodName]` at
          // the moment.
          this.__addAnnotatedComputationEffect(
              sig.method, index, note, part, null);
        }
      }
    },

    __addAnnotatedComputationEffect: function(property, index, note, part, trigger) {
      this._addPropertyEffect(property, 'annotatedComputation', {
        index: index,
        isCompound: note.isCompound,
        compoundIndex: part.compoundIndex,
        kind: note.kind,
        name: note.name,
        negate: part.negate,
        method: part.signature.method,
        args: part.signature.args,
        trigger: trigger,
        dynamicFn: part.signature.dynamicFn
      });
    },

    // method expressions are of the form: `name([arg1, arg2, .... argn])`
    _parseMethod: function(expression) {
      // tries to match valid javascript property names
      var m = expression.match(/([^\s]+?)\(([\s\S]*)\)/);
      if (m) {
        var sig = { method: m[1], static: true };
        // TODO(kaste): Optimize/memoize `getPropertyInfo`.
        if (this.getPropertyInfo(sig.method) !== Polymer.nob) {
          sig.static = false;
          sig.dynamicFn = true;
        }
        if (m[2].trim()) {
          // replace escaped commas with comma entity, split on un-escaped commas
          var args = m[2].replace(/\\,/g, '&comma;').split(',');
          return this._parseArgs(args, sig);
        } else {
          sig.args = Polymer.nar;
          return sig;
        }
      }
    },

    _parseArgs: function(argList, sig) {
      sig.args = argList.map(function(rawArg) {
        var arg = this._parseArg(rawArg);
        if (!arg.literal) {
          sig.static = false;
        }
        return arg;
      }, this);
      return sig;
    },

    _parseArg: function(rawArg) {
      // clean up whitespace
      var arg = rawArg.trim()
        // replace comma entity with comma
        .replace(/&comma;/g, ',')
        // repair extra escape sequences; note only commas strictly need
        // escaping, but we allow any other char to be escaped since its
        // likely users will do this
        .replace(/\\(.)/g, '\$1')
        ;
      // basic argument descriptor
      var a = {
        name: arg
      };
      // detect literal value (must be String or Number)
      var fc = arg[0];
      if (fc === '-') {
        fc = arg[1];
      }
      if (fc >= '0' && fc <= '9') {
        fc = '#';
      }
      switch(fc) {
        case "'":
        case '"':
          a.value = arg.slice(1, -1);
          a.literal = true;
          break;
        case '#':
          a.value = Number(arg);
          a.literal = true;
          break;
      }
      // if not literal, look for structured path
      if (!a.literal) {
        a.model = this._modelForPath(arg);
        // detect structured path (has dots)
        a.structured = arg.indexOf('.') > 0;
        if (a.structured) {
          a.wildcard = (arg.slice(-2) == '.*');
          if (a.wildcard) {
            a.name = arg.slice(0, -2);
          }
        }
      }
      return a;
    },

    // instancing
    _marshalInstanceEffects: function() {
      Polymer.Bind.prepareInstance(this);
      if (this._bindListeners) {
        Polymer.Bind.setupBindListeners(this);
      }
    },

    _applyEffectValue: function(info, value) {
      var node = this._nodes[info.index];
      var property = info.name;

      value = this._computeFinalAnnotationValue(node, property, value, info);

      // For better interop, dirty check before setting when custom events
      // are used, since the target element may not dirty check (e.g. <input>)
      if (info.customEvent && node[property] === value) {
        return;
      }

      if (info.kind == 'attribute') {
        this.serializeValueToAttribute(value, property, node);
      } else {
        var pinfo = node._propertyInfo && node._propertyInfo[property];
        if (pinfo && pinfo.readOnly) {
          return;
        }
        // Ideally we would call setProperty using fromAbove: true to avoid
        // spinning the wheel needlessly, but we found that users were listening
        // for change events outside of bindings
        this.__setProperty(property, value, false, node);
      }
    },

    _computeFinalAnnotationValue: function(node, property, value, info) {
      if (info.negate) {
        value = !value;
      }

      if (info.isCompound) {
        var storage = node.__compoundStorage__[property];
        storage[info.compoundIndex] = value;
        value = storage.join('');
      }

      if (info.kind !== 'attribute') {
        // TODO(sorvell): consider pre-processing the following two string
        // comparisons in the hot path so this can be a boolean check
        if (property === 'className') {
          value = this._scopeElementClass(node, value);
        }
        // Some browsers serialize `undefined` to `"undefined"`
        if (property === 'textContent' ||
            (node.localName == 'input' && property == 'value')) {
          value = value == undefined ? '' : value;
        }
      }
      return value;
    },

    _executeStaticEffects: function() {
      if (this._propertyEffects && this._propertyEffects.__static__) {
        this._effectEffects('__static__', null, this._propertyEffects.__static__);
      }
    }

  });
(function() {
  /*
    Process inputs efficiently via a configure lifecycle callback.
    Configure is called top-down, host before local dom. Users should
    implement configure to supply a set of default values for the element by
    returning an object containing the properties and values to set.

    Configured values are not immediately set, instead they are set when
    an element becomes ready, after its local dom is ready. This ensures
    that any user change handlers are not called before ready time.

  */

  /*
  Implementation notes:

  Configured values are collected into _config. At ready time, properties
  are set to the values in _config. This ensures properties are set child
  before host and change handlers are called only at ready time. The host
  will reset a value already propagated to a child, but this is not
  inefficient because of dirty checking at the set point.

  Bind notification events are sent when properties are set at ready time
  and thus received by the host before it is ready. Since notifications result
  in property updates and this triggers side effects, handling notifications
  is deferred until ready time.

  In general, events can be heard before an element is ready. This may occur
  when a user sends an event in a change handler or listens to a data event
  directly (on-foo-changed).
  */

  var usePolyfillProto = Polymer.Settings.usePolyfillProto;

  Polymer.Base._addFeature({

    // storage for configuration
    _setupConfigure: function(initialConfig) {
      this._config = {};
      this._handlers = [];
      this._aboveConfig = null;
      if (initialConfig) {
        // don't accept undefined values in intialConfig
        for (var i in initialConfig) {
          if (initialConfig[i] !== undefined) {
            this._config[i] = initialConfig[i];
          }
        }
      }
    },

    // static attributes are deserialized into _config
    _marshalAttributes: function() {
      this._takeAttributesToModel(this._config);
    },

    _attributeChangedImpl: function(name) {
      var model = this._clientsReadied ? this : this._config;
      this._setAttributeToProperty(model, name);
    },

    // at configure time values are stored in _config
    _configValue: function(name, value) {
      var info = this._propertyInfo[name];
      if (!info || !info.readOnly) {
        this._config[name] = value;
      }
    },

    // Override polymer-mini thunk
    _beforeClientsReady: function() {
      this._configure();
    },

    // configure: returns user supplied default property values
    // combines with _config to create final property values
    _configure: function() {
      // some annotation data needs to be handed from host to client
      // e.g. hand template content stored in notes to children as part of
      // configure flow so templates have their content at ready time
      this._configureAnnotationReferences();
      // save copy of configuration that came from above
      this._aboveConfig = this.mixin({}, this._config);
      // get individual default values from property configs
      var config = {};
      // mixed-in behaviors
      for (var i=0; i < this.behaviors.length; i++) {
        this._configureProperties(this.behaviors[i].properties, config);
      }
      // prototypical behavior
      this._configureProperties(this.properties, config);
      // TODO(sorvell): it *may* be faster to loop over _propertyInfo but
      // there are some test issues.
      //this._configureProperties(this._propertyInfo, config);
      // override local configuration with configuration from above
      this.mixin(config, this._aboveConfig);
      // this is the new _config, which are the final values to be applied
      this._config = config;
      // pass configuration data to bindings
      if (this._clients && this._clients.length) {
        this._distributeConfig(this._config);
      }
    },

    _configureProperties: function(properties, config) {
      for (var i in properties) {
        var c = properties[i];
        // Allow properties set before upgrade on the instance
        // to override default values. This allows late upgrade + an early set
        // to not b0rk accessors on the prototype.
        // Perf testing has shown `hasOwnProperty` to be ok here.
        if (!usePolyfillProto && this.hasOwnProperty(i) &&
            this._propertyEffects && this._propertyEffects[i]) {
          config[i] = this[i];
          delete this[i];
        } else if (c.value !== undefined) {
          var value = c.value;
          if (typeof value == 'function') {
            // pass existing config values (this._config) to value function
            value = value.call(this, this._config);
          }
          config[i] = value;
        }
      }
    },

    // distribute config values to bound nodes.
    _distributeConfig: function(config) {
      var fx$ = this._propertyEffects;
      if (fx$) {
        for (var p in config) {
          var fx = fx$[p];
          if (fx) {
            for (var i=0, l=fx.length, x; (i<l) && (x=fx[i]); i++) {
              // TODO(kschaaf): computed annotations are excluded from top-down
              // configure for now; to be revisited
              if (x.kind === 'annotation') {
                var node = this._nodes[x.effect.index];
                var name = x.effect.propertyName;
                // seeding configuration only
                var isAttr = (x.effect.kind == 'attribute');
                var hasEffect = (node._propertyEffects &&
                  node._propertyEffects[name]);
                if (node._configValue && (hasEffect || !isAttr)) {
                  var value = (p === x.effect.value) ? config[p] :
                    this._get(x.effect.value, config);
                  value = this._computeFinalAnnotationValue(node, name, value,
                                                            x.effect);
                  if (isAttr) {
                    // For attribute bindings, flow through the same ser/deser
                    // process to ensure the value is the same as if it were
                    // bound through the attribute
                    value = node.deserialize(this.serialize(value),
                      node._propertyInfo[name].type);
                  }
                  node._configValue(name, value);
                }
              }
            }
          }
        }
      }
    },

    // Override polymer-mini thunk
    _afterClientsReady: function() {
      // process static effects, e.g. computations that have only literal arguments
      this._executeStaticEffects();
      this._applyConfig(this._config, this._aboveConfig);
      this._flushHandlers();
    },

    // NOTE: values are already propagated to children via
    // _distributeConfig so propagation triggered by effects here is
    // redundant, but safe due to dirty checking
    _applyConfig: function(config, aboveConfig) {
      for (var n in config) {
        // Don't stomp on values that may have been set by other side effects
        if (this[n] === undefined) {
          // Call _propertySet for any properties with accessors, which will
          // initialize read-only properties also; set quietly if value was
          // configured from above, as opposed to default
          this.__setProperty(n, config[n], n in aboveConfig);
        }
      }
    },

    // NOTE: Notifications can be processed before ready since
    // they are sent at *child* ready time. Since notifications cause side
    // effects and side effects must not be processed before ready time,
    // handling is queue/defered until then.
    _notifyListener: function(fn, e) {
      if (!Polymer.Bind._isEventBogus(e, e.target)) {
        var value, path;
        if (e.detail) {
          value = e.detail.value;
          path = e.detail.path;
        }
        if (!this._clientsReadied) {
          this._queueHandler([fn, e.target, value, path]);
        } else {
          return fn.call(this, e.target, value, path);
        }
      }
    },

    _queueHandler: function(args) {
      this._handlers.push(args);
    },

    _flushHandlers: function() {
      var h$ = this._handlers;
      for (var i=0, l=h$.length, h; (i<l) && (h=h$[i]); i++) {
        h[0].call(this, h[1], h[2], h[3]);
      }
      // reset handlers array
      //
      // If an element holds a reference to a CustomEvent with a detail
      // property, Chrome will leak memory across page refreshes
      // https://crbug.com/529941
      this._handlers = [];
    }

  });

})();
/**
   * Changes to an object sub-field (aka "path") via a binding
   * (e.g. `<x-foo value="{{item.subfield}}"`) will notify other elements bound to
   * the same object automatically.
   *
   * When modifying a sub-field of an object imperatively
   * (e.g. `this.item.subfield = 42`), in order to have the new value propagated
   * to other elements, a special `set(path, value)` API is provided.
   * `set` sets the object field at the path specified, and then notifies the
   * binding system so that other elements bound to the same path will update.
   *
   * Example:
   *
   *     Polymer({
   *
   *       is: 'x-date',
   *
   *       properties: {
   *         date: {
   *           type: Object,
   *           notify: true
   *          }
   *       },
   *
   *       attached: function() {
   *         this.date = {};
   *         setInterval(function() {
   *           var d = new Date();
   *           // Required to notify elements bound to date of changes to sub-fields
   *           // this.date.seconds = d.getSeconds(); <-- Will not notify
   *           this.set('date.seconds', d.getSeconds());
   *           this.set('date.minutes', d.getMinutes());
   *           this.set('date.hours', d.getHours() % 12);
   *         }.bind(this), 1000);
   *       }
   *
   *     });
   *
   *  Allows bindings to `date` sub-fields to update on changes:
   *
   *     <x-date date="{{date}}"></x-date>
   *
   *     Hour: <span>{{date.hours}}</span>
   *     Min:  <span>{{date.minutes}}</span>
   *     Sec:  <span>{{date.seconds}}</span>
   *
   * @class data feature: path notification
   */

  (function() {
    // Using strict here to ensure fast argument manipulation in array methods
    'use strict';

    Polymer.Base._addFeature({
      /**
       * Notify that a path has changed.
       *
       * Example:
       *
       *     this.item.user.name = 'Bob';
       *     this.notifyPath('item.user.name');
       *
       * @param {string} path Path that should be notified.
      */
      notifyPath: function(path, value, fromAbove) {
        // Convert any array indices to keys before notifying path
        var info = {};
        var v = this._get(path, this, info);
        if (arguments.length === 1) {
          value = v;
        }
        // Notify change to key-based path
        if (info.path) {
          this._notifyPath(info.path, value, fromAbove);
        }
      },

      // Note: this implemetation only accepts key-based array paths
      _notifyPath: function(path, value, fromAbove) {
        var old = this._propertySetter(path, value);
        // manual dirty checking for now...
        // NaN is always not equal to itself,
        // if old and value are both NaN we treat them as equal
        // x === x is 10x faster, and equivalent to !isNaN(x)
        if (old !== value && (old === old || value === value)) {
          // console.group((this.localName || this.dataHost.id + '-' + this.dataHost.dataHost.index) + '#' + (this.id || this.index) + ' ' + path, value);
          // Take path effects at this level for exact path matches,
          // and notify down for any bindings to a subset of this path
          this._pathEffector(path, value);
          // Send event to notify the path change upwards
          // Optimization: don't notify up if we know the notification
          // is coming from above already (avoid wasted event dispatch)
          if (!fromAbove) {
            // TODO(sorvell): should only notify if notify: true?
            this._notifyPathUp(path, value);
          }
          // console.groupEnd((this.localName || this.dataHost.id + '-' + this.dataHost.dataHost.index) + '#' + (this.id || this.index) + ' ' + path, value);
          return true;
        }
      },

      /**
        Converts a path to an array of path parts.  A path may be specified
        as a dotted string or an array of one or more dotted strings (or numbers,
        for number-valued keys).
      */
      _getPathParts: function(path) {
        if (Array.isArray(path)) {
          var parts = [];
          for (var i=0; i<path.length; i++) {
            var args = path[i].toString().split('.');
            for (var j=0; j<args.length; j++) {
              parts.push(args[j]);
            }
          }
          return parts;
        } else {
          return path.toString().split('.');
        }
      },

      /**
       * Convienence method for setting a value to a path and notifying any
       * elements bound to the same path.
       *
       * Note, if any part in the path except for the last is undefined,
       * this method does nothing (this method does not throw when
       * dereferencing undefined paths).
       *
       * @method set
       * @param {(string|Array<(string|number)>)} path Path to the value
       *   to write.  The path may be specified as a string (e.g. `foo.bar.baz`)
       *   or an array of path parts (e.g. `['foo.bar', 'baz']`).  Note that
       *   bracketed expressions are not supported; string-based path parts
       *   *must* be separated by dots.  Note that when dereferencing array
       *   indices, the index may be used as a dotted part directly
       *   (e.g. `users.12.name` or `['users', 12, 'name']`).
       * @param {*} value Value to set at the specified path.
       * @param {Object=} root Root object from which the path is evaluated.
      */
      set: function(path, value, root) {
        var prop = root || this;
        var parts = this._getPathParts(path);
        var array;
        var last = parts[parts.length-1];
        if (parts.length > 1) {
          // Loop over path parts[0..n-2] and dereference
          for (var i=0; i<parts.length-1; i++) {
            var part = parts[i];
            if (array && part[0] == '#') {
              // Part was key; lookup item in collection
              prop = Polymer.Collection.get(array).getItem(part);
            } else {
              // Get item from simple property dereference
              prop = prop[part];
              if (array && (parseInt(part, 10) == part)) {
                // Translate array indices to collection keys for path notificaiton
                parts[i] = Polymer.Collection.get(array).getKey(prop);
              }
            }
            if (!prop) {
              return;
            }
            // Cache previous part if it is an array
            array = Array.isArray(prop) ? prop : null;
          }
          // Special handling when last part is a array item: need to replace
          // item in collection associated with key for that item
          if (array) {
            var coll = Polymer.Collection.get(array);
            var old, key;
            if (last[0] == '#') {
              // Part was key; lookup item in collection
              key = last;
              old = coll.getItem(key);
              // Update last part from key to index: O(n) lookup unavoidable
              last = array.indexOf(old);
              // Replace item associated with key in collection
              coll.setItem(key, value);
            } else if (parseInt(last, 10) == last) {
              // Dereference index & lookup collection key
              old = prop[last];
              key = coll.getKey(old);
              // Translate array indices to collection keys for path notificaiton
              parts[i] = key;
              // Replace item associated with key in collection
              coll.setItem(key, value);
            }
          }
          // Set value to object at end of path
          prop[last] = value;
          // Notify observers of path change
          if (!root) {
            this._notifyPath(parts.join('.'), value);
          }
        } else {
          // Simple property set
          prop[path] = value;
        }
      },

      /**
       * Convienence method for reading a value from a path.
       *
       * Note, if any part in the path is undefined, this method returns
       * `undefined` (this method does not throw when dereferencing undefined
       * paths).
       *
       * @method get
       * @param {(string|Array<(string|number)>)} path Path to the value
       *   to read.  The path may be specified as a string (e.g. `foo.bar.baz`)
       *   or an array of path parts (e.g. `['foo.bar', 'baz']`).  Note that
       *   bracketed expressions are not supported; string-based path parts
       *   *must* be separated by dots.  Note that when dereferencing array
       *   indices, the index may be used as a dotted part directly
       *   (e.g. `users.12.name` or `['users', 12, 'name']`).
       * @param {Object=} root Root object from which the path is evaluated.
       * @return {*} Value at the path, or `undefined` if any part of the path
       *   is undefined.
       */
      get: function(path, root) {
        return this._get(path, root);
      },

      // If `info` object is supplied, a `path` property will be added to it
      // containing the path with array indices converted to keys, for use
      // by the private _notifyPath / _notifySplice implementations
      _get: function(path, root, info) {
        var prop = root || this;
        var parts = this._getPathParts(path);
        var array;
        // Loop over path parts[0..n-1] and dereference
        for (var i=0; i<parts.length; i++) {
          if (!prop) {
            return;
          }
          var part = parts[i];
          if (array && part[0] == '#') {
            // Part was key; lookup item in collection
            prop = Polymer.Collection.get(array).getItem(part);
          } else {
            // Get item from simple property dereference
            prop = prop[part];
            if (info && array && (parseInt(part, 10) == part)) {
              // Translate array indices to collection keys for path notificaiton
              parts[i] = Polymer.Collection.get(array).getKey(prop);
            }
          }
          // Cache previous part if it is an array
          array = Array.isArray(prop) ? prop : null;
        }
        if (info) {
          info.path = parts.join('.');
        }
        return prop;
      },

      _pathEffector: function(path, value) {
        // get root property
        var model = this._modelForPath(path);
        // search property effects of the root property for 'annotation' effects
        var fx$ = this._propertyEffects && this._propertyEffects[model];
        if (fx$) {
          for (var i=0, fx; (i<fx$.length) && (fx=fx$[i]); i++) {
            // use memoized path functions
            var fxFn = fx.pathFn;
            if (fxFn) {
              fxFn.call(this, path, value, fx.effect);
            }
          }
        }
        // notify runtime-bound paths
        if (this._boundPaths) {
          this._notifyBoundPaths(path, value);
        }
      },

      _annotationPathEffect: function(path, value, effect) {
        if (effect.value === path || effect.value.indexOf(path + '.') === 0) {
          // TODO(sorvell): ideally the effect function is on this prototype
          // so we don't have to call it like this.
          Polymer.Bind._annotationEffect.call(this, path, value, effect);
        } else if ((path.indexOf(effect.value + '.') === 0) && !effect.negate) {
          // locate the bound node
          var node = this._nodes[effect.index];
          if (node && node._notifyPath) {
            var p = this._fixPath(effect.name , effect.value, path);
            node._notifyPath(p, value, true);
          }
        }
      },

      _complexObserverPathEffect: function(path, value, effect) {
        if (this._pathMatchesEffect(path, effect)) {
          Polymer.Bind._complexObserverEffect.call(this, path, value, effect);
        }
      },

      _computePathEffect: function(path, value, effect) {
        if (this._pathMatchesEffect(path, effect)) {
          Polymer.Bind._computeEffect.call(this, path, value, effect);
        }
      },

      _annotatedComputationPathEffect: function(path, value, effect) {
        if (this._pathMatchesEffect(path, effect)) {
          Polymer.Bind._annotatedComputationEffect.call(this, path, value, effect);
        }
      },

      _pathMatchesEffect: function(path, effect) {
        var effectArg = effect.trigger.name;
        return (effectArg == path) ||
          (effectArg.indexOf(path + '.') === 0) ||
          (effect.trigger.wildcard && path.indexOf(effectArg) === 0);
      },

      /**
       * Aliases one data path as another, such that path notifications from one
       * are routed to the other.
       *
       * @method linkPaths
       * @param {string} to Target path to link.
       * @param {string} from Source path to link.
       */
      linkPaths: function(to, from) {
        this._boundPaths = this._boundPaths || {};
        if (from) {
          this._boundPaths[to] = from;
          // this.set(to, this._get(from));
        } else {
          this.unlinkPaths(to);
          // this.set(to, from);
        }
      },

      /**
       * Removes a data path alias previously established with `linkPaths`.
       *
       * Note, the path to unlink should be the target (`to`) used when
       * linking the paths.
       *
       * @method unlinkPaths
       * @param {string} path Target path to unlink.
       */
      unlinkPaths: function(path) {
        if (this._boundPaths) {
          delete this._boundPaths[path];
        }
      },

      _notifyBoundPaths: function(path, value) {
        for (var a in this._boundPaths) {
          var b = this._boundPaths[a];
          if (path.indexOf(a + '.') == 0) {
            this._notifyPath(this._fixPath(b, a, path), value);
          } else if (path.indexOf(b + '.') == 0) {
            this._notifyPath(this._fixPath(a, b, path), value);
          }
        }
      },

      _fixPath: function(property, root, path) {
        return property + path.slice(root.length);
      },

      _notifyPathUp: function(path, value) {
        var rootName = this._modelForPath(path);
        var dashCaseName = Polymer.CaseMap.camelToDashCase(rootName);
        var eventName = dashCaseName + this._EVENT_CHANGED;
        // use a cached event here (_useCache: true) for efficiency
        this.fire(eventName, {
          path: path,
          value: value
        }, {bubbles: false, _useCache: true});
      },

      _modelForPath: function(path) {
        var dot = path.indexOf('.');
        return (dot < 0) ? path : path.slice(0, dot);
      },

      _EVENT_CHANGED: '-changed',

      /**
       * Notify that an array has changed.
       *
       * Example:
       *
       *     this.items = [ {name: 'Jim'}, {name: 'Todd'}, {name: 'Bill'} ];
       *     ...
       *     this.items.splice(1, 1, {name: 'Sam'});
       *     this.items.push({name: 'Bob'});
       *     this.notifySplices('items', [
       *       { index: 1, removed: [{name: 'Todd'}], addedCount: 1, obect: this.items, type: 'splice' },
       *       { index: 3, removed: [], addedCount: 1, object: this.items, type: 'splice'}
       *     ]);
       *
       * @param {string} path Path that should be notified.
       * @param {Array} splices Array of splice records indicating ordered
       *   changes that occurred to the array. Each record should have the
       *   following fields:
       *    * index: index at which the change occurred
       *    * removed: array of items that were removed from this index
       *    * addedCount: number of new items added at this index
       *    * object: a reference to the array in question
       *    * type: the string literal 'splice'
       *
       *   Note that splice records _must_ be normalized such that they are
       *   reported in index order (raw results from `Object.observe` are not
       *   ordered and must be normalized/merged before notifying).
      */
      notifySplices: function(path, splices) {
        var info = {};
        var array = this._get(path, this, info);
        // Notify change to key-based path
        this._notifySplices(array, info.path, splices);
      },

      // Note: this implemetation only accepts key-based array paths
      _notifySplices: function(array, path, splices) {
        var change = {
          keySplices: Polymer.Collection.applySplices(array, splices),
          indexSplices: splices
        };
        var splicesPath = path + '.splices';
        this._notifyPath(splicesPath, change);
        this._notifyPath(path + '.length', array.length);
        // All path notification values are cached on `this.__data__`.
        // Null here to allow potentially large splice records to be GC'ed.
        this.__data__[splicesPath] = {keySplices: null, indexSplices: null};
      },

      _notifySplice: function(array, path, index, added, removed) {
        this._notifySplices(array, path, [{
          index: index,
          addedCount: added,
          removed: removed,
          object: array,
          type: 'splice'
        }]);
      },

      /**
       * Adds items onto the end of the array at the path specified.
       *
       * The arguments after `path` and return value match that of
       * `Array.prototype.push`.
       *
       * This method notifies other paths to the same array that a
       * splice occurred to the array.
       *
       * @method push
       * @param {String} path Path to array.
       * @param {...any} var_args Items to push onto array
       * @return {number} New length of the array.
       */
      push: function(path) {
        var info = {};
        var array = this._get(path, this, info);
        var args = Array.prototype.slice.call(arguments, 1);
        var len = array.length;
        var ret = array.push.apply(array, args);
        if (args.length) {
          this._notifySplice(array, info.path, len, args.length, []);
        }
        return ret;
      },

      /**
       * Removes an item from the end of array at the path specified.
       *
       * The arguments after `path` and return value match that of
       * `Array.prototype.pop`.
       *
       * This method notifies other paths to the same array that a
       * splice occurred to the array.
       *
       * @method pop
       * @param {String} path Path to array.
       * @return {any} Item that was removed.
       */
      pop: function(path) {
        var info = {};
        var array = this._get(path, this, info);
        var hadLength = Boolean(array.length);
        var args = Array.prototype.slice.call(arguments, 1);
        var ret = array.pop.apply(array, args);
        if (hadLength) {
          this._notifySplice(array, info.path, array.length, 0, [ret]);
        }
        return ret;
      },

      /**
       * Starting from the start index specified, removes 0 or more items
       * from the array and inserts 0 or more new itms in their place.
       *
       * The arguments after `path` and return value match that of
       * `Array.prototype.splice`.
       *
       * This method notifies other paths to the same array that a
       * splice occurred to the array.
       *
       * @method splice
       * @param {String} path Path to array.
       * @param {number} start Index from which to start removing/inserting.
       * @param {number} deleteCount Number of items to remove.
       * @param {...any} var_args Items to insert into array.
       * @return {Array} Array of removed items.
       */
      splice: function(path, start) {
        var info = {};
        var array = this._get(path, this, info);
        // Normalize fancy native splice handling of crazy start values
        if (start < 0) {
          start = array.length - Math.floor(-start);
        } else {
          start = Math.floor(start);
        }
        if (!start) {
          start = 0;
        }
        var args = Array.prototype.slice.call(arguments, 1);
        var ret = array.splice.apply(array, args);
        var addedCount = Math.max(args.length - 2, 0);
        if (addedCount || ret.length) {
          this._notifySplice(array, info.path, start, addedCount, ret);
        }
        return ret;
      },

      /**
       * Removes an item from the beginning of array at the path specified.
       *
       * The arguments after `path` and return value match that of
       * `Array.prototype.pop`.
       *
       * This method notifies other paths to the same array that a
       * splice occurred to the array.
       *
       * @method shift
       * @param {String} path Path to array.
       * @return {any} Item that was removed.
       */
      shift: function(path) {
        var info = {};
        var array = this._get(path, this, info);
        var hadLength = Boolean(array.length);
        var args = Array.prototype.slice.call(arguments, 1);
        var ret = array.shift.apply(array, args);
        if (hadLength) {
          this._notifySplice(array, info.path, 0, 0, [ret]);
        }
        return ret;
      },

      /**
       * Adds items onto the beginning of the array at the path specified.
       *
       * The arguments after `path` and return value match that of
       * `Array.prototype.push`.
       *
       * This method notifies other paths to the same array that a
       * splice occurred to the array.
       *
       * @method unshift
       * @param {String} path Path to array.
       * @param {...any} var_args Items to insert info array
       * @return {number} New length of the array.
       */
      unshift: function(path) {
        var info = {};
        var array = this._get(path, this, info);
        var args = Array.prototype.slice.call(arguments, 1);
        var ret = array.unshift.apply(array, args);
        if (args.length) {
          this._notifySplice(array, info.path, 0, args.length, []);
        }
        return ret;
      },

      // TODO(kschaaf): This is the path analogue to Polymer.Bind.prepareModel,
      // which provides API for path-based notification on elements with property
      // effects; this should be re-factored along with the Bind lib, either all on
      // Base or all in Bind (see issue https://github.com/Polymer/polymer/issues/2547).
      prepareModelNotifyPath: function(model) {
        this.mixin(model, {
          fire: Polymer.Base.fire,
          _getEvent: Polymer.Base._getEvent,
          __eventCache: Polymer.Base.__eventCache,
          notifyPath: Polymer.Base.notifyPath,
          _get: Polymer.Base._get,
          _EVENT_CHANGED: Polymer.Base._EVENT_CHANGED,
          _notifyPath: Polymer.Base._notifyPath,
          _notifyPathUp: Polymer.Base._notifyPathUp,
          _pathEffector: Polymer.Base._pathEffector,
          _annotationPathEffect: Polymer.Base._annotationPathEffect,
          _complexObserverPathEffect: Polymer.Base._complexObserverPathEffect,
          _annotatedComputationPathEffect: Polymer.Base._annotatedComputationPathEffect,
          _computePathEffect: Polymer.Base._computePathEffect,
          _modelForPath: Polymer.Base._modelForPath,
          _pathMatchesEffect: Polymer.Base._pathMatchesEffect,
          _notifyBoundPaths: Polymer.Base._notifyBoundPaths,
          _getPathParts: Polymer.Base._getPathParts
        });
      }

    });

  })();
Polymer.Base._addFeature({

    /**
     * Rewrites a given URL relative to the original location of the document
     * containing the `dom-module` for this element.  This method will return
     * the same URL before and after vulcanization.
     *
     * @method resolveUrl
     * @param {string} url URL to resolve.
     * @return {string} Rewritten URL relative to the import
     */
    resolveUrl: function(url) {
      // TODO(sorvell): do we want to put the module reference on the prototype?
      var module = Polymer.DomModule.import(this.is);
      var root = '';
      if (module) {
        var assetPath = module.getAttribute('assetpath') || '';
        root = Polymer.ResolveUrl.resolveUrl(assetPath, module.ownerDocument.baseURI);
      }
      return Polymer.ResolveUrl.resolveUrl(url, root);
    }

  });
/*
  Extremely simple css parser. Intended to be not more than what we need
  and definitely not necessarily correct =).
*/
Polymer.CssParse = (function() {

  return {
    // given a string of css, return a simple rule tree
    parse: function(text) {
      text = this._clean(text);
      return this._parseCss(this._lex(text), text);
    },

    // remove stuff we don't care about that may hinder parsing
    _clean: function (cssText) {
      return cssText.replace(this._rx.comments, '').replace(this._rx.port, '');
    },

    // super simple {...} lexer that returns a node tree
    _lex: function(text) {
      var root = {start: 0, end: text.length};
      var n = root;
      for (var i=0, l=text.length; i < l; i++) {
        switch (text[i]) {
          case this.OPEN_BRACE:
            //console.group(i);
            if (!n.rules) {
              n.rules = [];
            }
            var p = n;
            var previous = p.rules[p.rules.length-1];
            n = {start: i+1, parent: p, previous: previous};
            p.rules.push(n);
            break;
          case this.CLOSE_BRACE:
            //console.groupEnd(n.start);
            n.end = i+1;
            n = n.parent || root;
            break;
        }
      }
      return root;
    },

    // add selectors/cssText to node tree
    _parseCss: function(node, text) {
      var t = text.substring(node.start, node.end-1);
      node.parsedCssText = node.cssText = t.trim();
      if (node.parent) {
        var ss = node.previous ? node.previous.end : node.parent.start;
        t = text.substring(ss, node.start-1);
        t = this._expandUnicodeEscapes(t);
        t = t.replace(this._rx.multipleSpaces, ' ');
        // TODO(sorvell): ad hoc; make selector include only after last ;
        // helps with mixin syntax
        t = t.substring(t.lastIndexOf(';')+1);
        var s = node.parsedSelector = node.selector = t.trim();
        node.atRule = (s.indexOf(this.AT_START) === 0);
        // note, support a subset of rule types...
        if (node.atRule) {
          if (s.indexOf(this.MEDIA_START) === 0) {
            node.type = this.types.MEDIA_RULE;
          } else if (s.match(this._rx.keyframesRule)) {
            node.type = this.types.KEYFRAMES_RULE;
            node.keyframesName =
                node.selector.split(this._rx.multipleSpaces).pop();
          }
        } else {
          if (s.indexOf(this.VAR_START) === 0) {
            node.type = this.types.MIXIN_RULE;
          } else {
            node.type = this.types.STYLE_RULE;
          }
        }
      }
      var r$ = node.rules;
      if (r$) {
        for (var i=0, l=r$.length, r; (i<l) && (r=r$[i]); i++) {
          this._parseCss(r, text);
        }
      }
      return node;
    },

    // conversion of sort unicode escapes with spaces like `\33 ` (and longer) into
    // expanded form that doesn't require trailing space `\000033`
    _expandUnicodeEscapes : function(s) {
      return s.replace(/\\([0-9a-f]{1,6})\s/gi, function() {
        var code = arguments[1], repeat = 6 - code.length;
        while (repeat--) {
          code = '0' + code;
        }
        return '\\' + code;
      });
    },

    // stringify parsed css.
    stringify: function(node, preserveProperties, text) {
      text = text || '';
      // calc rule cssText
      var cssText = '';
      if (node.cssText || node.rules) {
        var r$ = node.rules;
        if (r$ && (preserveProperties || !this._hasMixinRules(r$))) {
          for (var i=0, l=r$.length, r; (i<l) && (r=r$[i]); i++) {
            cssText = this.stringify(r, preserveProperties, cssText);
          }
        } else {
          cssText = preserveProperties ? node.cssText :
            this.removeCustomProps(node.cssText);
          cssText = cssText.trim();
          if (cssText) {
            cssText = '  ' + cssText + '\n';
          }
        }
      }
      // emit rule if there is cssText
      if (cssText) {
        if (node.selector) {
          text += node.selector + ' ' + this.OPEN_BRACE + '\n';
        }
        text += cssText;
        if (node.selector) {
          text += this.CLOSE_BRACE + '\n\n';
        }
      }
      return text;
    },

    _hasMixinRules: function(rules) {
      return rules[0].selector.indexOf(this.VAR_START) === 0;
    },

    removeCustomProps: function(cssText) {
      cssText = this.removeCustomPropAssignment(cssText);
      return this.removeCustomPropApply(cssText);
    },

    removeCustomPropAssignment: function(cssText) {
      return cssText
        .replace(this._rx.customProp, '')
        .replace(this._rx.mixinProp, '');
    },

    removeCustomPropApply: function(cssText) {
      return cssText
        .replace(this._rx.mixinApply, '')
        .replace(this._rx.varApply, '');
    },

    types: {
      STYLE_RULE: 1,
      KEYFRAMES_RULE: 7,
      MEDIA_RULE: 4,
      MIXIN_RULE: 1000
    },

    OPEN_BRACE: '{',
    CLOSE_BRACE: '}',

    // helper regexp's
    _rx: {
      comments: /\/\*[^*]*\*+([^/*][^*]*\*+)*\//gim,
      port: /@import[^;]*;/gim,
      customProp: /(?:^[^;\-\s}]+)?--[^;{}]*?:[^{};]*?(?:[;\n]|$)/gim,
      mixinProp:  /(?:^[^;\-\s}]+)?--[^;{}]*?:[^{};]*?{[^}]*?}(?:[;\n]|$)?/gim,
      mixinApply: /@apply[\s]*\([^)]*?\)[\s]*(?:[;\n]|$)?/gim,
      varApply: /[^;:]*?:[^;]*?var\([^;]*\)(?:[;\n]|$)?/gim,
      keyframesRule: /^@[^\s]*keyframes/,
      multipleSpaces: /\s+/g
    },

    VAR_START: '--',
    MEDIA_START: '@media',
    AT_START: '@'

  };

})();
Polymer.StyleUtil = (function() {

    return {

      MODULE_STYLES_SELECTOR: 'style, link[rel=import][type~=css], template',
      INCLUDE_ATTR: 'include',

      toCssText: function(rules, callback, preserveProperties) {
        if (typeof rules === 'string') {
          rules = this.parser.parse(rules);
        }
        if (callback) {
          this.forEachRule(rules, callback);
        }
        return this.parser.stringify(rules, preserveProperties);
      },

      forRulesInStyles: function(styles, styleRuleCallback, keyframesRuleCallback) {
        if (styles) {
          for (var i=0, l=styles.length, s; (i<l) && (s=styles[i]); i++) {
            this.forEachRule(
                this.rulesForStyle(s),
                styleRuleCallback,
                keyframesRuleCallback);
          }
        }
      },

      rulesForStyle: function(style) {
        if (!style.__cssRules && style.textContent) {
          style.__cssRules =  this.parser.parse(style.textContent);
        }
        return style.__cssRules;
      },

      // Tests if a rule is a keyframes selector, which looks almost exactly
      // like a normal selector but is not (it has nothing to do with scoping
      // for example).
      isKeyframesSelector: function(rule) {
        return rule.parent &&
            rule.parent.type === this.ruleTypes.KEYFRAMES_RULE;
      },

      forEachRule: function(node, styleRuleCallback, keyframesRuleCallback) {
        if (!node) {
          return;
        }
        var skipRules = false;
        if (node.type === this.ruleTypes.STYLE_RULE) {
          styleRuleCallback(node);
        } else if (keyframesRuleCallback &&
                   node.type === this.ruleTypes.KEYFRAMES_RULE) {
          keyframesRuleCallback(node);
        } else if (node.type === this.ruleTypes.MIXIN_RULE) {
          skipRules = true;
        }
        var r$ = node.rules;
        if (r$ && !skipRules) {
          for (var i=0, l=r$.length, r; (i<l) && (r=r$[i]); i++) {
            this.forEachRule(r, styleRuleCallback, keyframesRuleCallback);
          }
        }
      },

      // add a string of cssText to the document.
      applyCss: function(cssText, moniker, target, contextNode) {
        var style = this.createScopeStyle(cssText, moniker);
        target = target || document.head;
        var after = (contextNode && contextNode.nextSibling) || 
          target.firstChild;
        this.__lastHeadApplyNode = style;
        return target.insertBefore(style, after);
      },

      createScopeStyle: function(cssText, moniker) {
        var style = document.createElement('style');
        if (moniker) {
          style.setAttribute('scope', moniker);
        }
        style.textContent = cssText;
        return style;
      },

      __lastHeadApplyNode: null,

      // insert a comment node as a styling position placeholder.
      applyStylePlaceHolder: function(moniker) {
        var placeHolder = document.createComment(' Shady DOM styles for ' + 
          moniker + ' ');
        var after = this.__lastHeadApplyNode ? 
          this.__lastHeadApplyNode.nextSibling : null;
        var scope = document.head;
        scope.insertBefore(placeHolder, after || scope.firstChild);
        this.__lastHeadApplyNode = placeHolder;
        return placeHolder;
      },

      cssFromModules: function(moduleIds, warnIfNotFound) {
        var modules = moduleIds.trim().split(' ');
        var cssText = '';
        for (var i=0; i < modules.length; i++) {
          cssText += this.cssFromModule(modules[i], warnIfNotFound);
        }
        return cssText;
      },

      // returns cssText of styles in a given module; also un-applies any
      // styles that apply to the document.
      cssFromModule: function(moduleId, warnIfNotFound) {
        var m = Polymer.DomModule.import(moduleId);
        if (m && !m._cssText) {
          m._cssText = this.cssFromElement(m);
        }
        if (!m && warnIfNotFound) {
          console.warn('Could not find style data in module named', moduleId);
        }
        return m && m._cssText || '';
      },

      // support lots of ways to discover css...
      cssFromElement: function(element) {
        var cssText = '';
        // if element is a template, get content from its .content
        var content = element.content || element;
        var e$ = Polymer.TreeApi.arrayCopy(
          content.querySelectorAll(this.MODULE_STYLES_SELECTOR));
        for (var i=0, e; i < e$.length; i++) {
          e = e$[i];
          // look inside templates for elements
          if (e.localName === 'template') {
            cssText += this.cssFromElement(e);
          } else {
            // style elements inside dom-modules will apply to the main document
            // we don't want this, so we remove them here.
            if (e.localName === 'style') {
              var include = e.getAttribute(this.INCLUDE_ATTR);
              // now support module refs on 'styling' elements
              if (include) {
                cssText += this.cssFromModules(include, true);
              }
              // get style element applied to main doc via HTMLImports polyfill
              e = e.__appliedElement || e;
              e.parentNode.removeChild(e);
              cssText += this.resolveCss(e.textContent, element.ownerDocument);
            // it's an import, assume this is a text file of css content.
            // TODO(sorvell): plan is to deprecate this way to get styles;
            // remember to add deprecation warning when this is done.
            } else if (e.import && e.import.body) {
              cssText += this.resolveCss(e.import.body.textContent, e.import);
            }
          }
        }
        return cssText;
      },

      resolveCss: Polymer.ResolveUrl.resolveCss,
      parser: Polymer.CssParse,
      ruleTypes: Polymer.CssParse.types

    };

  })();
Polymer.StyleTransformer = (function() {

    var nativeShadow = Polymer.Settings.useNativeShadow;
    var styleUtil = Polymer.StyleUtil;

    /* Transforms ShadowDOM styling into ShadyDOM styling

     * scoping:

        * elements in scope get scoping selector class="x-foo-scope"
        * selectors re-written as follows:

          div button -> div.x-foo-scope button.x-foo-scope

     * :host -> scopeName

     * :host(...) -> scopeName...

     * ::content -> ' '

     * ::shadow, /deep/: processed similar to ::content

     * :host-context(...): scopeName..., ... scopeName

    */
    var api = {

      // Given a node and scope name, add a scoping class to each node
      // in the tree. This facilitates transforming css into scoped rules.
      dom: function(node, scope, useAttr, shouldRemoveScope) {
        this._transformDom(node, scope || '', useAttr, shouldRemoveScope);
      },

      _transformDom: function(node, selector, useAttr, shouldRemoveScope) {
        if (node.setAttribute) {
          this.element(node, selector, useAttr, shouldRemoveScope);
        }
        var c$ = Polymer.dom(node).childNodes;
        for (var i=0; i<c$.length; i++) {
          this._transformDom(c$[i], selector, useAttr, shouldRemoveScope);
        }
      },

      element: function(element, scope, useAttr, shouldRemoveScope) {
        if (useAttr) {
          if (shouldRemoveScope) {
            element.removeAttribute(SCOPE_NAME);
          } else {
            element.setAttribute(SCOPE_NAME, scope);
          }
        } else {
          // note: if using classes, we add both the general 'style-scope' class
          // as well as the specific scope. This enables easy filtering of all
          // `style-scope` elements
          if (scope) {
            // note: svg on IE does not have classList so fallback to class
            if (element.classList) {
              if (shouldRemoveScope) {
                element.classList.remove(SCOPE_NAME);
                element.classList.remove(scope);
              } else {
                element.classList.add(SCOPE_NAME);
                element.classList.add(scope);
              }
            } else if (element.getAttribute) {
              var c = element.getAttribute(CLASS);
              if (shouldRemoveScope) {
                if (c) {
                  element.setAttribute(CLASS, c.replace(SCOPE_NAME, '')
                    .replace(scope, ''));
                }
              } else {
                element.setAttribute(CLASS, (c ? c + ' ' : '') +
                  SCOPE_NAME + ' ' + scope);
              }
            }
          }
        }
      },

      elementStyles: function(element, callback) {
        var styles = element._styles;
        var cssText = '';
        for (var i=0, l=styles.length, s; (i<l) && (s=styles[i]); i++) {
          var rules = styleUtil.rulesForStyle(s);
          cssText += nativeShadow ?
            styleUtil.toCssText(rules, callback) :
            this.css(rules, element.is, element.extends, callback,
            element._scopeCssViaAttr) + '\n\n';
        }
        return cssText.trim();
      },

      // Given a string of cssText and a scoping string (scope), returns
      // a string of scoped css where each selector is transformed to include
      // a class created from the scope. ShadowDOM selectors are also transformed
      // (e.g. :host) to use the scoping selector.
      css: function(rules, scope, ext, callback, useAttr) {
        var hostScope = this._calcHostScope(scope, ext);
        scope = this._calcElementScope(scope, useAttr);
        var self = this;
        return styleUtil.toCssText(rules, function(rule) {
          if (!rule.isScoped) {
            self.rule(rule, scope, hostScope);
            rule.isScoped = true;
          }
          if (callback) {
            callback(rule, scope, hostScope);
          }
        });
      },

      _calcElementScope: function (scope, useAttr) {
        if (scope) {
          return useAttr ?
            CSS_ATTR_PREFIX + scope + CSS_ATTR_SUFFIX :
            CSS_CLASS_PREFIX + scope;
        } else {
          return '';
        }
      },

      _calcHostScope: function(scope, ext) {
        return ext ? '[is=' +  scope + ']' : scope;
      },

      rule: function (rule, scope, hostScope) {
        this._transformRule(rule, this._transformComplexSelector,
          scope, hostScope);
      },

      // transforms a css rule to a scoped rule.
      _transformRule: function(rule, transformer, scope, hostScope) {
        var p$ = rule.selector.split(COMPLEX_SELECTOR_SEP);
        // we want to skip transformation of rules that appear in keyframes,
        // because they are keyframe selectors, not element selectors.
        if (!styleUtil.isKeyframesSelector(rule)) {
          for (var i=0, l=p$.length, p; (i<l) && (p=p$[i]); i++) {
            p$[i] = transformer.call(this, p, scope, hostScope);
          }
        }
        // NOTE: save transformedSelector for subsequent matching of elements
        // against selectors (e.g. when calculating style properties)
        rule.selector = rule.transformedSelector =
          p$.join(COMPLEX_SELECTOR_SEP);
      },

      _transformComplexSelector: function(selector, scope, hostScope) {
        var stop = false;
        var hostContext = false;
        var self = this;
        selector = selector.replace(CONTENT_START, HOST + ' $1');
        selector = selector.replace(SIMPLE_SELECTOR_SEP, function(m, c, s) {
          if (!stop) {
            var info = self._transformCompoundSelector(s, c, scope, hostScope);
            stop = stop || info.stop;
            hostContext = hostContext || info.hostContext;
            c = info.combinator;
            s = info.value;
          } else {
            s = s.replace(SCOPE_JUMP, ' ');
          }
          return c + s;
        });
        if (hostContext) {
          selector = selector.replace(HOST_CONTEXT_PAREN,
            function(m, pre, paren, post) {
              return pre + paren + ' ' + hostScope + post +
                COMPLEX_SELECTOR_SEP + ' ' + pre + hostScope + paren + post;
             });
        }
        return selector;
      },

      _transformCompoundSelector: function(selector, combinator, scope, hostScope) {
        // replace :host with host scoping class
        var jumpIndex = selector.search(SCOPE_JUMP);
        var hostContext = false;
        if (selector.indexOf(HOST_CONTEXT) >=0) {
          hostContext = true;
        } else if (selector.indexOf(HOST) >=0) {
          // :host(...) -> scopeName...
          selector = selector.replace(HOST_PAREN, function(m, host, paren) {
            return hostScope + paren;
          });
          // now normal :host
          selector = selector.replace(HOST, hostScope);
        // replace other selectors with scoping class
        } else if (jumpIndex !== 0) {
          selector = scope ? this._transformSimpleSelector(selector, scope) :
            selector;
        }
        // remove left-side combinator when dealing with ::content.
        if (selector.indexOf(CONTENT) >= 0) {
          combinator = '';
        }
        // process scope jumping selectors up to the scope jump and then stop
        // e.g. .zonk ::content > .foo ==> .zonk.scope > .foo
        var stop;
        if (jumpIndex >= 0) {
          selector = selector.replace(SCOPE_JUMP, ' ');
          stop = true;
        }
        return {value: selector, combinator: combinator, stop: stop,
          hostContext: hostContext};
      },

      _transformSimpleSelector: function(selector, scope) {
        var p$ = selector.split(PSEUDO_PREFIX);
        p$[0] += scope;
        return p$.join(PSEUDO_PREFIX);
      },

      documentRule: function(rule) {
        // reset selector in case this is redone.
        rule.selector = rule.parsedSelector;
        this.normalizeRootSelector(rule);
        if (!nativeShadow) {
          this._transformRule(rule, this._transformDocumentSelector);
        }
      },

      normalizeRootSelector: function(rule) {
        if (rule.selector === ROOT) {
          rule.selector = 'body';
        }
      },

      _transformDocumentSelector: function(selector) {
        return selector.match(SCOPE_JUMP) ?
          this._transformComplexSelector(selector, SCOPE_DOC_SELECTOR) :
          this._transformSimpleSelector(selector.trim(), SCOPE_DOC_SELECTOR);
      },

      SCOPE_NAME: 'style-scope'
    };

    var SCOPE_NAME = api.SCOPE_NAME;
    var SCOPE_DOC_SELECTOR = ':not([' + SCOPE_NAME + '])' +
      ':not(.' + SCOPE_NAME + ')';
    var COMPLEX_SELECTOR_SEP = ',';
    var SIMPLE_SELECTOR_SEP = /(^|[\s>+~]+)((?:\[.+?\]|[^\s>+~=\[])+)/g;
    var HOST = ':host';
    var ROOT = ':root';
    // NOTE: this supports 1 nested () pair for things like
    // :host(:not([selected]), more general support requires
    // parsing which seems like overkill
    var HOST_PAREN = /(:host)(?:\(((?:\([^)(]*\)|[^)(]*)+?)\))/g;
    var HOST_CONTEXT = ':host-context';
    var HOST_CONTEXT_PAREN = /(.*)(?::host-context)(?:\(((?:\([^)(]*\)|[^)(]*)+?)\))(.*)/;
    var CONTENT = '::content';
    var SCOPE_JUMP = /::content|::shadow|\/deep\//;
    var CSS_CLASS_PREFIX = '.';
    var CSS_ATTR_PREFIX = '[' + SCOPE_NAME + '~=';
    var CSS_ATTR_SUFFIX = ']';
    var PSEUDO_PREFIX = ':';
    var CLASS = 'class';
    var CONTENT_START = new RegExp('^(' + CONTENT + ')');

    // exports
    return api;

  })();
Polymer.StyleExtends = (function() {

  var styleUtil = Polymer.StyleUtil;

  return {

    hasExtends: function(cssText) {
      return Boolean(cssText.match(this.rx.EXTEND));
    },

    transform: function(style) {
      var rules = styleUtil.rulesForStyle(style);
      var self = this;
      styleUtil.forEachRule(rules, function(rule) {
        self._mapRuleOntoParent(rule);
        if (rule.parent) {
          var m;
          while ((m = self.rx.EXTEND.exec(rule.cssText))) {
            var extend = m[1];
            var extendor = self._findExtendor(extend, rule);
            if (extendor) {
              self._extendRule(rule, extendor);
            }
          }
        }
        rule.cssText = rule.cssText.replace(self.rx.EXTEND, '');
      });
      // strip unused % selectors
      return styleUtil.toCssText(rules, function(rule) {
        if (rule.selector.match(self.rx.STRIP)) {
          rule.cssText = '';
        }
      }, true);
    },

    _mapRuleOntoParent: function(rule) {
      if (rule.parent) {
        var map = rule.parent.map || (rule.parent.map = {});
        var parts = rule.selector.split(',');
        for (var i=0, p; i < parts.length; i++) {
          p = parts[i];
          map[p.trim()] = rule;
        }
        return map;
      }
    },

    _findExtendor: function(extend, rule) {
      return rule.parent && rule.parent.map && rule.parent.map[extend] ||
        this._findExtendor(extend, rule.parent);
    },

    _extendRule: function(target, source) {
      if (target.parent !== source.parent) {
        this._cloneAndAddRuleToParent(source, target.parent);
      }
      target.extends = target.extends || [];
      target.extends.push(source);
      // TODO: this misses `%foo, .bar` as an unetended selector but
      // this seems rare and could possibly be unsupported.
      source.selector = source.selector.replace(this.rx.STRIP, '');
      source.selector = (source.selector && source.selector + ',\n') +
        target.selector;
      if (source.extends) {
        source.extends.forEach(function(e) {
          this._extendRule(target, e);
        }, this);
      }
    },

    _cloneAndAddRuleToParent: function(rule, parent) {
      rule = Object.create(rule);
      rule.parent = parent;
      if (rule.extends) {
        rule.extends = rule.extends.slice();
      }
      parent.rules.push(rule);
    },

    rx: {
      EXTEND: /@extends\(([^)]*)\)\s*?;/gim,
      STRIP: /%[^,]*$/
    }

  };

})();
(function() {

    var prepElement = Polymer.Base._prepElement;
    var nativeShadow = Polymer.Settings.useNativeShadow;

    var styleUtil = Polymer.StyleUtil;
    var styleTransformer = Polymer.StyleTransformer;
    var styleExtends = Polymer.StyleExtends;

    Polymer.Base._addFeature({

      _prepElement: function(element) {
        if (this._encapsulateStyle) {
          styleTransformer.element(element, this.is,
            this._scopeCssViaAttr);
        }
        prepElement.call(this, element);
      },

      _prepStyles: function() {
        // under shady dom we always output a shimmed style (which may be 
        // empty) so that other dynamic stylesheets can always be placed 
        // after the element's main stylesheet. 
        // This helps ensure element styles are always in registration order.
        if (!nativeShadow) {
          this._scopeStyle = styleUtil.applyStylePlaceHolder(this.is);
        }
      },

      _prepShimStyles: function() {
        if (this._template) {
          if (this._encapsulateStyle === undefined) {
            this._encapsulateStyle = !nativeShadow;
          }
          this._styles = this._collectStyles();
          // calculate shimmed styles (we must always do this as it
          // stores shimmed style data in the css rules for later use)
          var cssText = styleTransformer.elementStyles(this);
          // prepare to shim style properties.
          this._prepStyleProperties();
          // do we really need to output static shimmed styles?
          // only if no custom properties are used since otherwise
          // styles are applied via property shimming.
          if (!this._needsStyleProperties() && this._styles.length) {
            styleUtil.applyCss(cssText, this.is,
              nativeShadow ? this._template.content : null, this._scopeStyle);
          }
        } else {
          this._styles = [];
        }
      },

      // search for extra style modules via `styleModules`
      // TODO(sorvell): consider dropping support for `styleModules`
      _collectStyles: function() {
        var styles = [];
        var cssText = '', m$ = this.styleModules;
        if (m$) {
          for (var i=0, l=m$.length, m; (i<l) && (m=m$[i]); i++) {
            cssText += styleUtil.cssFromModule(m);
          }
        }
        cssText += styleUtil.cssFromModule(this.is);
        // check if we have a disconnected template and add styles from that
        // if so; if our template has no parent or is not in our dom-module...
        var p = this._template && this._template.parentNode;
        if (this._template && (!p || p.id.toLowerCase() !== this.is)) {
          cssText += styleUtil.cssFromElement(this._template);
        }
        if (cssText) {
          var style = document.createElement('style');
          style.textContent = cssText;
          // extends!!
          if (styleExtends.hasExtends(style.textContent)) {
            // TODO(sorvell): variable is not used, should it update `style.textContent`?
            cssText = styleExtends.transform(style);
          }
          styles.push(style);
        }
        return styles;
      },

      // instance-y
      // add scoping class whenever an element is added to localDOM
      _elementAdd: function(node) {
        if (this._encapsulateStyle) {
          // If __styleScoped is set, this is a one-time optimization to
          // avoid scoping pre-scoped document fragments
          if (node.__styleScoped) {
            node.__styleScoped = false;
          } else {
            styleTransformer.dom(node, this.is, this._scopeCssViaAttr);
          }
        }
      },

      // remove scoping class whenever an element is removed from localDOM
      _elementRemove: function(node) {
        if (this._encapsulateStyle) {
          styleTransformer.dom(node, this.is, this._scopeCssViaAttr, true);
        }
      },

      /**
       * Apply style scoping to the specified `container` and all its
       * descendants. If `shouldObserve` is true, changes to the container are
       * monitored via mutation observer and scoping is applied.
       *
       * This method is useful for ensuring proper local DOM CSS scoping
       * for elements created in this local DOM scope, but out of the
       * control of this element (i.e., by a 3rd-party library)
       * when running in non-native Shadow DOM environments.
       *
       * @method scopeSubtree
       * @param {Element} container Element to scope.
       * @param {boolean} shouldObserve When true, monitors the container
       *   for changes and re-applies scoping for any future changes.
       */
      scopeSubtree: function(container, shouldObserve) {
        if (nativeShadow) {
          return;
        }
        var self = this;
        var scopify = function(node) {
          if (node.nodeType === Node.ELEMENT_NODE) {
            var className = node.getAttribute('class');
            node.setAttribute('class', self._scopeElementClass(node, className));
            var n$ = node.querySelectorAll('*');
            for (var i=0, n; (i<n$.length) && (n=n$[i]); i++) {
              className = n.getAttribute('class');
              n.setAttribute('class', self._scopeElementClass(n, className));
            }
          }
        };
        scopify(container);
        if (shouldObserve) {
          var mo = new MutationObserver(function(mxns) {
            for (var i=0, m; (i<mxns.length) && (m=mxns[i]); i++) {
              if (m.addedNodes) {
                for (var j=0; j < m.addedNodes.length; j++) {
                  scopify(m.addedNodes[j]);
                }
              }
            }
          });
          mo.observe(container, {childList: true, subtree: true});
          return mo;
        }
      }

    });

  })();
Polymer.StyleProperties = (function() {
    'use strict';

    var nativeShadow = Polymer.Settings.useNativeShadow;
    var matchesSelector = Polymer.DomApi.matchesSelector;
    var styleUtil = Polymer.StyleUtil;
    var styleTransformer = Polymer.StyleTransformer;

    return {

      // decorates styles with rule info and returns an array of used style
      // property names
      decorateStyles: function(styles) {
        var self = this, props = {}, keyframes = [];
        styleUtil.forRulesInStyles(styles, function(rule) {
          self.decorateRule(rule);
          self.collectPropertiesInCssText(rule.propertyInfo.cssText, props);
        }, function onKeyframesRule(rule) {
          keyframes.push(rule);
        });
        // Cache all found keyframes rules for later reference:
        styles._keyframes = keyframes;
        // return this list of property names *consumes* in these styles.
        var names = [];
        for (var i in props) {
          names.push(i);
        }
        return names;
      },

      // decorate a single rule with property info
      decorateRule: function(rule) {
        if (rule.propertyInfo) {
          return rule.propertyInfo;
        }
        var info = {}, properties = {};
        var hasProperties = this.collectProperties(rule, properties);
        if (hasProperties) {
          info.properties = properties;
          // TODO(sorvell): workaround parser seeing mixins as additional rules
          rule.rules = null;
        }
        info.cssText = this.collectCssText(rule);
        rule.propertyInfo = info;
        return info;
      },

      // collects the custom properties from a rule's cssText
      collectProperties: function(rule, properties) {
        var info = rule.propertyInfo;
        if (info) {
          if (info.properties) {
            Polymer.Base.mixin(properties, info.properties);
            return true;
          }
        } else {
          var m, rx = this.rx.VAR_ASSIGN;
          var cssText = rule.parsedCssText;
          var any;
          while ((m = rx.exec(cssText))) {
            // note: group 2 is var, 3 is mixin
            properties[m[1]] = (m[2] || m[3]).trim();
            any = true;
          }
          return any;
        }
      },

      // returns cssText of properties that consume variables/mixins
      collectCssText: function(rule) {
        return this.collectConsumingCssText(rule.parsedCssText);
      },

      // NOTE: we support consumption inside mixin assignment
      // but not production, so strip out {...}
      collectConsumingCssText: function(cssText) {
        return cssText.replace(this.rx.BRACKETED, '')
          .replace(this.rx.VAR_ASSIGN, '');
      },

      collectPropertiesInCssText: function(cssText, props) {
        var m;
        while ((m = this.rx.VAR_CAPTURE.exec(cssText))) {
          props[m[1]] = true;
          var def = m[2];
          if (def && def.match(this.rx.IS_VAR)) {
            props[def] = true;
          }
        }
      },

      // turns custom properties into realized values.
      reify: function(props) {
        // big perf optimization here: reify only *own* properties
        // since this object has __proto__ of the element's scope properties
        var names = Object.getOwnPropertyNames(props);
        for (var i=0, n; i < names.length; i++) {
          n = names[i];
          props[n] = this.valueForProperty(props[n], props);
        }
      },

      // given a property value, returns the reified value
      // a property value may be:
      // (1) a literal value like: red or 5px;
      // (2) a variable value like: var(--a), var(--a, red), or var(--a, --b);
      // (3) a literal mixin value like { properties }. Each of these properties
      // can have values that are: (a) literal, (b) variables, (c) @apply mixins.
      valueForProperty: function(property, props) {
        // case (1) default
        // case (3) defines a mixin and we have to reify the internals
        if (property) {
          if (property.indexOf(';') >=0) {
            property = this.valueForProperties(property, props);
          } else {
            // case (2) variable
            var self = this;
            var fn = function(all, prefix, value, fallback) {
              var propertyValue = (self.valueForProperty(props[value], props) ||
                (props[fallback] ?
                self.valueForProperty(props[fallback], props) :
                fallback));
              return prefix + (propertyValue || '');
            };
            property = property.replace(this.rx.VAR_MATCH, fn);
          }
        }
        return property && property.trim() || '';
      },

      // note: we do not yet support mixin within mixin
      valueForProperties: function(property, props) {
        var parts = property.split(';');
        for (var i=0, p, m; i<parts.length; i++) {
          if ((p = parts[i])) {
            m = p.match(this.rx.MIXIN_MATCH);
            if (m) {
              p = this.valueForProperty(props[m[1]], props);
            } else {
              var colon = p.indexOf(':');
              if (colon !== -1) {
                var pp = p.substring(colon);
                pp = pp.trim();
                pp = this.valueForProperty(pp, props) || pp;
                p = p.substring(0, colon) + pp;
              }
            }
            parts[i] = (p && p.lastIndexOf(';') === p.length - 1) ?
              // strip trailing ;
              p.slice(0, -1) :
              p || '';
          }
        }
        return parts.join(';');
      },

      applyProperties: function(rule, props) {
        var output = '';
        // dynamically added sheets may not be decorated so ensure they are.
        if (!rule.propertyInfo) {
          this.decorateRule(rule);
        }
        if (rule.propertyInfo.cssText) {
          output = this.valueForProperties(rule.propertyInfo.cssText, props);
        }
        rule.cssText = output;
      },

      // Apply keyframe transformations to the cssText of a given rule. The
      // keyframeTransforms object is a map of keyframe names to transformer
      // functions which take in cssText and spit out transformed cssText.
      applyKeyframeTransforms: function(rule, keyframeTransforms) {
        var input = rule.cssText;
        var output = rule.cssText;
        if (rule.hasAnimations == null) {
          // Cache whether or not the rule has any animations to begin with:
          rule.hasAnimations = this.rx.ANIMATION_MATCH.test(input);
        }
        // If there are no animations referenced, we can skip transforms:
        if (rule.hasAnimations) {
          var transform;
          // If we haven't transformed this rule before, we iterate over all
          // transforms:
          if (rule.keyframeNamesToTransform == null) {
            rule.keyframeNamesToTransform = [];
            for (var keyframe in keyframeTransforms) {
              transform = keyframeTransforms[keyframe];
              output = transform(input);
              // If the transform actually changed the CSS text, we cache the
              // transform name for future use:
              if (input !== output) {
                input = output;
                rule.keyframeNamesToTransform.push(keyframe);
              }
            }
          } else {
            // If we already have a list of keyframe names that apply to this
            // rule, we apply only those keyframe name transforms:
            for (var i = 0; i < rule.keyframeNamesToTransform.length; ++i) {
              transform = keyframeTransforms[rule.keyframeNamesToTransform[i]];
              input = transform(input);
            }
            output = input;
          }
        }
        rule.cssText = output;
      },

      // Test if the rules in these styles matches the given `element` and if so,
      // collect any custom properties into `props`.
      propertyDataFromStyles: function(styles, element) {
        var props = {}, self = this;
        // generates a unique key for these matches
        var o = [], i = 0;
        styleUtil.forRulesInStyles(styles, function(rule) {
          // TODO(sorvell): we could trim the set of rules at declaration
          // time to only include ones that have properties
          if (!rule.propertyInfo) {
            self.decorateRule(rule);
          }
          // match element against transformedSelector: selector may contain
          // unwanted uniquification and parsedSelector does not directly match
          // for :host selectors.
          if (element && rule.propertyInfo.properties &&
              matchesSelector.call(element, rule.transformedSelector
                || rule.parsedSelector)) {
            self.collectProperties(rule, props);
            // produce numeric key for these matches for lookup
            addToBitMask(i, o);
          }
          i++;
        });
        return {properties: props, key: o};
      },

      // Test if a rule matches scope criteria (* or :root) and if so,
      // collect any custom properties into `props`.
      scopePropertiesFromStyles: function(styles) {
        if (!styles._scopeStyleProperties) {
          styles._scopeStyleProperties =
            this.selectedPropertiesFromStyles(styles, this.SCOPE_SELECTORS);
        }
        return styles._scopeStyleProperties;
      },

      // Test if a rule matches host criteria (:host) and if so,
      // collect any custom properties into `props`.
      //
      // TODO(sorvell): this should change to collecting properties from any
      // :host(...) and then matching these against self.
      hostPropertiesFromStyles: function(styles) {
        if (!styles._hostStyleProperties) {
          styles._hostStyleProperties =
            this.selectedPropertiesFromStyles(styles, this.HOST_SELECTORS);
        }
        return styles._hostStyleProperties;
      },

      selectedPropertiesFromStyles: function(styles, selectors) {
        var props = {}, self = this;
        styleUtil.forRulesInStyles(styles, function(rule) {
          if (!rule.propertyInfo) {
            self.decorateRule(rule);
          }
          for (var i=0; i < selectors.length; i++) {
            if (rule.parsedSelector === selectors[i]) {
              self.collectProperties(rule, props);
              return;
            }
          }
        });
        return props;
      },

      transformStyles: function(element, properties, scopeSelector) {
        var self = this;
        var hostSelector = styleTransformer
          ._calcHostScope(element.is, element.extends);
        var rxHostSelector = element.extends ?
          '\\' + hostSelector.slice(0, -1) + '\\]' :
          hostSelector;
        var hostRx = new RegExp(this.rx.HOST_PREFIX + rxHostSelector +
          this.rx.HOST_SUFFIX);
        var keyframeTransforms =
          this._elementKeyframeTransforms(element, scopeSelector);
        return styleTransformer.elementStyles(element, function(rule) {
          self.applyProperties(rule, properties);
          if (!nativeShadow &&
              !Polymer.StyleUtil.isKeyframesSelector(rule) &&
              rule.cssText) {
            // NOTE: keyframe transforms only scope munge animation names, so it
            // is not necessary to apply them in ShadowDOM.
            self.applyKeyframeTransforms(rule, keyframeTransforms);
            self._scopeSelector(rule, hostRx, hostSelector,
              element._scopeCssViaAttr, scopeSelector);
          }
        });
      },

      _elementKeyframeTransforms: function(element, scopeSelector) {
        var keyframesRules = element._styles._keyframes;
        var keyframeTransforms = {};
        if (!nativeShadow && keyframesRules) {
          // For non-ShadowDOM, we transform all known keyframes rules in
          // advance for the current scope. This allows us to catch keyframes
          // rules that appear anywhere in the stylesheet:
          for (var i = 0, keyframesRule = keyframesRules[i];
               i < keyframesRules.length;
               keyframesRule = keyframesRules[++i]) {
            this._scopeKeyframes(keyframesRule, scopeSelector);
            keyframeTransforms[keyframesRule.keyframesName] =
                this._keyframesRuleTransformer(keyframesRule);
          }
        }
        return keyframeTransforms;
      },

      // Generate a factory for transforming a chunk of CSS text to handle a
      // particular scoped keyframes rule.
      _keyframesRuleTransformer: function(keyframesRule) {
        return function(cssText) {
          return cssText.replace(
              keyframesRule.keyframesNameRx,
              keyframesRule.transformedKeyframesName);
        };
      },

      // Transforms `@keyframes` names to be unique for the current host.
      // Example: @keyframes foo-anim -> @keyframes foo-anim-x-foo-0
      _scopeKeyframes: function(rule, scopeId) {
        rule.keyframesNameRx = new RegExp(rule.keyframesName, 'g');
        rule.transformedKeyframesName = rule.keyframesName + '-' + scopeId;
        rule.transformedSelector = rule.transformedSelector || rule.selector;
        rule.selector = rule.transformedSelector.replace(
            rule.keyframesName, rule.transformedKeyframesName);
      },

      // Strategy: x scope shim a selector e.g. to scope `.x-foo-42` (via classes):
      // non-host selector: .a.x-foo -> .x-foo-42 .a.x-foo
      // host selector: x-foo.wide -> .x-foo-42.wide
      // note: we use only the scope class (.x-foo-42) and not the hostSelector
      // (x-foo) to scope :host rules; this helps make property host rules
      // have low specificity. They are overrideable by class selectors but,
      // unfortunately, not by type selectors (e.g. overriding via 
      // `.special` is ok, but not by `x-foo`).
      _scopeSelector: function(rule, hostRx, hostSelector, viaAttr, scopeId) {
        rule.transformedSelector = rule.transformedSelector || rule.selector;
        var selector = rule.transformedSelector;
        var scope = viaAttr ? '[' + styleTransformer.SCOPE_NAME + '~=' +
          scopeId + ']' :
          '.' + scopeId;
        var parts = selector.split(',');
        for (var i=0, l=parts.length, p; (i<l) && (p=parts[i]); i++) {
          parts[i] = p.match(hostRx) ?
            p.replace(hostSelector, scope) :
            scope + ' ' + p;
        }
        rule.selector = parts.join(',');
      },

      applyElementScopeSelector: function(element, selector, old, viaAttr) {
        var c = viaAttr ? element.getAttribute(styleTransformer.SCOPE_NAME) :
          (element.getAttribute('class') || '');
        var v = old ? c.replace(old, selector) :
          (c ? c + ' ' : '') + this.XSCOPE_NAME + ' ' + selector;
        if (c !== v) {
          if (viaAttr) {
            element.setAttribute(styleTransformer.SCOPE_NAME, v);
          } else {
            element.setAttribute('class', v);
          }
        }
      },

      applyElementStyle: function(element, properties, selector, style) {
        // calculate cssText to apply
        var cssText = style ? style.textContent || '' :
          this.transformStyles(element, properties, selector);
        // if shady and we have a cached style that is not style, decrement
        var s = element._customStyle;
        if (s && !nativeShadow && (s !== style)) {
          s._useCount--;
          if (s._useCount <= 0 && s.parentNode) {
            s.parentNode.removeChild(s);
          }
        }
        // apply styling always under native or if we generated style
        // or the cached style is not in document(!)
        if (nativeShadow || (!style || !style.parentNode)) {
          // update existing style only under native
          if (nativeShadow && element._customStyle) {
            element._customStyle.textContent = cssText;
            style = element._customStyle;
          // otherwise, if we have css to apply, do so
          } else if (cssText) {
            // apply css after the scope style of the element to help with
            // style precedence rules.
            style = styleUtil.applyCss(cssText, selector,
              nativeShadow ? element.root : null, element._scopeStyle);
          }
        }
        // ensure this style is our custom style and increment its use count.
        if (style) {
          style._useCount = style._useCount || 0;
          // increment use count if we changed styles
          if (element._customStyle != style) {
            style._useCount++;
          }
          element._customStyle = style;
        }
        return style;
      },

      // customStyle properties are applied if they are truthy or 0. Otherwise,
      // they are skipped; this allows properties previously set in customStyle
      // to be easily reset to inherited values.
      mixinCustomStyle: function(props, customStyle) {
        var v;
        for (var i in customStyle) {
          v = customStyle[i];
          if (v || v === 0) {
            props[i] = v;
          }
        }
      },

      rx: {
        VAR_ASSIGN: /(?:^|[;\s{]\s*)(--[\w-]*?)\s*:\s*(?:([^;{]*)|{([^}]*)})(?:(?=[;\s}])|$)/gi,
        MIXIN_MATCH: /(?:^|\W+)@apply[\s]*\(([^)]*)\)/i,
        // note, this supports:
        // var(--a)
        // var(--a, --b)
        // var(--a, fallback-literal)
        // var(--a, fallback-literal(with-one-nested-parentheses))
        VAR_MATCH: /(^|\W+)var\([\s]*([^,)]*)[\s]*,?[\s]*((?:[^,()]*)|(?:[^;()]*\([^;)]*\)))[\s]*?\)/gi,
        VAR_CAPTURE: /\([\s]*(--[^,\s)]*)(?:,[\s]*(--[^,\s)]*))?(?:\)|,)/gi,
        ANIMATION_MATCH: /(animation\s*:)|(animation-name\s*:)/,
        IS_VAR: /^--/,
        BRACKETED: /\{[^}]*\}/g,
        HOST_PREFIX: '(?:^|[^.#[:])',
        HOST_SUFFIX: '($|[.:[\\s>+~])'
      },

      HOST_SELECTORS: [':host'],
      SCOPE_SELECTORS: [':root'],
      XSCOPE_NAME: 'x-scope'

    };

    function addToBitMask(n, bits) {
      var o = parseInt(n / 32);
      var v = 1 << (n % 32);
      bits[o] = (bits[o] || 0) | v;
    }

  })();
(function() {

  Polymer.StyleCache = function() {
    this.cache = {};
  };

  Polymer.StyleCache.prototype = {
    
    MAX: 100,

    store: function(is, data, keyValues, keyStyles) {
      data.keyValues = keyValues;
      data.styles = keyStyles;
      var s$ = this.cache[is] = this.cache[is] || [];
      s$.push(data);
      if (s$.length > this.MAX) {
        s$.shift();
      }
    },

    retrieve: function(is, keyValues, keyStyles) {
      var cache = this.cache[is];
      if (cache) {
        // look through cache backwards as most recent push is last.
        for (var i=cache.length-1, data; i >= 0; i--) {
          data = cache[i];
          if (keyStyles === data.styles &&
              this._objectsEqual(keyValues, data.keyValues)) {
            return data;
          }
        }
      }
    },

    clear: function() {
      this.cache = {};
    },

    // note, this is intentially limited to support just the cases we need
    // right now. The objects we're checking here are either objects that must 
    // always have the same keys OR arrays.
    _objectsEqual: function(target, source) {
      var t, s;
      for (var i in target) {
        t = target[i], s = source[i];
        if (!(typeof t === 'object' && t ? this._objectsStrictlyEqual(t, s) : 
            t === s)) {
          return false;
        }
      }
      if (Array.isArray(target)) {
        return target.length === source.length;
      }
      return true;
    },

    _objectsStrictlyEqual: function(target, source) {
      return this._objectsEqual(target, source) && 
        this._objectsEqual(source, target);
    }

  };

})();
Polymer.StyleDefaults = (function() {

    var styleProperties = Polymer.StyleProperties;
    var StyleCache = Polymer.StyleCache;

    var api = {

      _styles: [],
      _properties: null,
      customStyle: {},
      _styleCache: new StyleCache(),

      addStyle: function(style) {
        this._styles.push(style);
        this._properties = null;
      },

      // NOTE: this object can be used as a styling scope so it has an api
      // similar to that of an element wrt style properties
      get _styleProperties() {
        if (!this._properties) {
          // force rules to reparse since they may be out of date
          styleProperties.decorateStyles(this._styles);
          // NOTE: reset cache for own properties; it may have been set when
          // an element in an import applied styles (e.g. custom-style)
          this._styles._scopeStyleProperties = null;
          this._properties = styleProperties
            .scopePropertiesFromStyles(this._styles);
          // mixin customStyle
          styleProperties.mixinCustomStyle(this._properties, this.customStyle);
          styleProperties.reify(this._properties);
        }
        return this._properties;
      },

      _needsStyleProperties: function() {},

      _computeStyleProperties: function() {
        return this._styleProperties;
      },

      /**
       * Re-evaluates and applies custom CSS properties to all elements in the
       * document based on dynamic changes, such as adding or removing classes.
       *
       * For performance reasons, Polymer's custom CSS property shim relies
       * on this explicit signal from the user to indicate when changes have
       * been made that affect the values of custom properties.
       *
       * @method updateStyles
       * @param {Object=} properties Properties object which is mixed into
       * the document root `customStyle` property. This argument provides a
       * shortcut for setting `customStyle` and then calling `updateStyles`.
      */
      updateStyles: function(properties) {
        // force properties update.
        this._properties = null;
        if (properties) {
          Polymer.Base.mixin(this.customStyle, properties);
        }
        // invalidate the cache
        this._styleCache.clear();
        // update any custom-styles we are tracking
        for (var i=0, s; i < this._styles.length; i++) {
          s = this._styles[i];
          s = s.__importElement || s;
          s._apply();
        }
      }

    };

    // exports
    return api;

  })();
(function() {
    'use strict';

    var serializeValueToAttribute = Polymer.Base.serializeValueToAttribute;

    var propertyUtils = Polymer.StyleProperties;
    var styleTransformer = Polymer.StyleTransformer;
    var styleDefaults = Polymer.StyleDefaults;

    var nativeShadow = Polymer.Settings.useNativeShadow;

    Polymer.Base._addFeature({

      _prepStyleProperties: function() {
        // note: an element should produce an x-scope stylesheet
        // if it has any _stylePropertyNames
        this._ownStylePropertyNames = this._styles && this._styles.length ?
          propertyUtils.decorateStyles(this._styles) :
          null;
      },

      /**
       * An element's style properties can be directly modified by
       * setting key-value pairs in `customStyle` on the element
       * (analogous to setting `style`) and then calling `updateStyles()`.
       *
       */
      customStyle: null,

      /**
     * Returns the computed style value for the given property.
     * @param {String} property
     * @return {String} the computed value
     */
      getComputedStyleValue: function(property) {
        return this._styleProperties && this._styleProperties[property] ||
          getComputedStyle(this).getPropertyValue(property);
      },

      // here we have an instance time spot to put custom property data
      _setupStyleProperties: function() {
        this.customStyle = {};
        this._styleCache = null;
        this._styleProperties = null;
        this._scopeSelector = null;
        this._ownStyleProperties = null;
        this._customStyle = null;
      },

      _needsStyleProperties: function() {
        return Boolean(this._ownStylePropertyNames &&
          this._ownStylePropertyNames.length);
      },

      _beforeAttached: function() {
        // note: do this once automatically,
        // then requires calling `updateStyles`
        if (!this._scopeSelector && this._needsStyleProperties()) {
          this._updateStyleProperties();
        }
      },

      _findStyleHost: function() {
        var e = this, root;
        while ((root = Polymer.dom(e).getOwnerRoot())) {
          if (Polymer.isInstance(root.host)) {
            return root.host;
          }
          e = root.host;
        }
        return styleDefaults;
      },

      _updateStyleProperties: function() {
        var info, scope = this._findStyleHost();
        // install cache in host if it doesn't exist.
        if (!scope._styleCache) {
          scope._styleCache = new Polymer.StyleCache();
        }
        var scopeData = propertyUtils
          .propertyDataFromStyles(scope._styles, this);
        // look in scope cache
        scopeData.key.customStyle = this.customStyle;
        info = scope._styleCache.retrieve(this.is, scopeData.key, this._styles);
        // compute style properties (fast path, if cache hit)
        var scopeCached = Boolean(info);
        if (scopeCached) {
          // when scope cached, we can safely take style propertis out of the
          // scope cache because they are only for this scope.
          this._styleProperties = info._styleProperties;
        } else {
          this._computeStyleProperties(scopeData.properties);
        }
        this._computeOwnStyleProperties();
        // cache miss, do work!
        if (!scopeCached) {
          // and look in 2ndary global cache
          info = styleCache.retrieve(this.is,
            this._ownStyleProperties, this._styles);
        }
        var globalCached = Boolean(info) && !scopeCached;
        // now we have properties and a cached style if one
        // is available.
        var style = this._applyStyleProperties(info);
        // no cache so store in cache
        //console.warn(this.is, scopeCached, globalCached, info && info._scopeSelector);
        if (!scopeCached) {
          // create an info object for caching
          // TODO(sorvell): clone style node when using native Shadow DOM
          // so a style used in a root does not itself get stored in the cache
          // This can lead to incorrect sharing, but should be fixed
          // in `Polymer.StyleProperties.applyElementStyle`
          style = style && nativeShadow ? style.cloneNode(true) : style;
          info = {
            style: style,
            _scopeSelector: this._scopeSelector,
            _styleProperties: this._styleProperties
          };
          scopeData.key.customStyle = {};
          this.mixin(scopeData.key.customStyle, this.customStyle);
          scope._styleCache.store(this.is, info, scopeData.key, this._styles);
          if (!globalCached) {
            // save in global cache
            styleCache.store(this.is, Object.create(info), this._ownStyleProperties,
            this._styles);
          }
        }
      },

      _computeStyleProperties: function(scopeProps) {
        // get scope and make sure it has properties
        var scope = this._findStyleHost();
        // force scope to compute properties if they don't exist or if forcing
        // and it doesn't need properties
        if (!scope._styleProperties) {
          scope._computeStyleProperties();
        }
        // start with scope style properties
        var props = Object.create(scope._styleProperties);
        // mixin own host properties (lower specifity than scope props)
        this.mixin(props, propertyUtils.hostPropertiesFromStyles(this._styles));
        // mixin properties matching this element in scope
        scopeProps = scopeProps ||
          propertyUtils.propertyDataFromStyles(scope._styles, this).properties;
        this.mixin(props, scopeProps);
        // finally mixin properties inherent to this element
        this.mixin(props,
          propertyUtils.scopePropertiesFromStyles(this._styles));
        propertyUtils.mixinCustomStyle(props, this.customStyle);
        // reify properties (note: only does own properties)
        propertyUtils.reify(props);
        this._styleProperties = props;
      },

      _computeOwnStyleProperties: function() {
        var props = {};
        for (var i=0, n; i < this._ownStylePropertyNames.length; i++) {
          n = this._ownStylePropertyNames[i];
          props[n] = this._styleProperties[n];
        }
        this._ownStyleProperties = props;
      },

      _scopeCount: 0,

      _applyStyleProperties: function(info) {
        // update scope selector (needed for style transformation)
        var oldScopeSelector = this._scopeSelector;
        // note, the scope selector is incremented per class counter
        this._scopeSelector = info ? info._scopeSelector :
          this.is + '-' + this.__proto__._scopeCount++;
        var style = propertyUtils.applyElementStyle(this,
          this._styleProperties, this._scopeSelector, info && info.style);
        // apply scope selector
        if (!nativeShadow) {
          propertyUtils.applyElementScopeSelector(this, this._scopeSelector,
            oldScopeSelector, this._scopeCssViaAttr);
        }
        return style;
      },

      serializeValueToAttribute: function(value, attribute, node) {
        // override to ensure whenever classes are set, we need to shim them.
        node = node || this;
        if (attribute === 'class' && !nativeShadow) {
          // host needed to scope styling.
          // Under Shady DOM, domHost is safe to use here because we know it
          // is a Polymer element
          var host = node === this ? (this.domHost || this.dataHost) : this;
          if (host) {
            value = host._scopeElementClass(node, value);
          }
        }
        // note: using Polymer.dom here ensures that any attribute sets
        // will provoke distribution if necessary; do this iff necessary
        node = (this.shadyRoot && this.shadyRoot._hasDistributed) ?
          Polymer.dom(node) : node;
        serializeValueToAttribute.call(this, value, attribute, node);
      },

      _scopeElementClass: function(element, selector) {
        if (!nativeShadow && !this._scopeCssViaAttr) {
          selector = (selector ? selector + ' ' : '') + SCOPE_NAME + ' ' + this.is +
            (element._scopeSelector ? ' ' +  XSCOPE_NAME + ' ' +
            element._scopeSelector : '');
        }
        return selector;
      },

      /**
       * Re-evaluates and applies custom CSS properties based on dynamic
       * changes to this element's scope, such as adding or removing classes
       * in this element's local DOM.
       *
       * For performance reasons, Polymer's custom CSS property shim relies
       * on this explicit signal from the user to indicate when changes have
       * been made that affect the values of custom properties.
       *
       * @method updateStyles
       * @param {Object=} properties Properties object which is mixed into
       * the element's `customStyle` property. This argument provides a shortcut
       * for setting `customStyle` and then calling `updateStyles`.
      */
      updateStyles: function(properties) {
        if (this.isAttached) {
          if (properties) {
            this.mixin(this.customStyle, properties);
          }
          // skip applying properties to self if not used
          if (this._needsStyleProperties()) {
            this._updateStyleProperties();
          // when an element doesn't use style properties, its own properties
          // should be invalidated so elements down the tree update ok.
          } else {
            this._styleProperties = null;
          }
          if (this._styleCache) {
            this._styleCache.clear();
          }
          // always apply properties to root
          this._updateRootStyles();
        }
      },

      _updateRootStyles: function(root) {
        root = root || this.root;
        var c$ = Polymer.dom(root)._query(function(e) {
          return e.shadyRoot || e.shadowRoot;
        });
        for (var i=0, l= c$.length, c; (i<l) && (c=c$[i]); i++) {
          if (c.updateStyles) {
            c.updateStyles();
          }
        }
      }

    });

    /**
     * Force all custom elements using cross scope custom properties,
     * to update styling.
     */
    Polymer.updateStyles = function(properties) {
      // update default/custom styles
      styleDefaults.updateStyles(properties);
      // search the document for elements to update
      Polymer.Base._updateRootStyles(document);
    };

    var styleCache = new Polymer.StyleCache();
    Polymer.customStyleCache = styleCache;

    var SCOPE_NAME = styleTransformer.SCOPE_NAME;
    var XSCOPE_NAME = propertyUtils.XSCOPE_NAME;

  })();
Polymer.Base._addFeature({

    _registerFeatures: function() {
      // identity
      this._prepIs();
      // factory
      this._prepConstructor();
      // styles
      this._prepStyles();
    },

    _finishRegisterFeatures: function() {
      // template
      this._prepTemplate();
      // style shimming
      this._prepShimStyles();
      // template markup
      this._prepAnnotations();
      // accessors
      this._prepEffects();
      // shared behaviors
      this._prepBehaviors();
      // fast access to property info
      this._prepPropertyInfo();
      // accessors part 2
      this._prepBindings();
      // dom encapsulation
      this._prepShady();
    },

    _prepBehavior: function(b) {
      this._addPropertyEffects(b.properties);
      this._addComplexObserverEffects(b.observers);
      this._addHostAttributes(b.hostAttributes);
    },

    _initFeatures: function() {
      // setup gestures
      this._setupGestures();
      // manage configuration
      this._setupConfigure();
      // setup style properties
      this._setupStyleProperties();
      // setup debouncers
      this._setupDebouncers();
      // setup shady
      this._setupShady();
      this._registerHost();
      if (this._template) {
        // manage local dom
        this._poolContent();
        // host stack
        this._beginHosting();
        // instantiate template
        this._stampTemplate();
        // host stack
        this._endHosting();
        // concretize template references
        this._marshalAnnotationReferences();
      }
      // concretize effects on instance
      this._marshalInstanceEffects();
      // acquire instance behaviors
      this._marshalBehaviors();
      /*
      TODO(sorvell): It's *slightly() more efficient to marshal attributes prior 
      to installing hostAttributes, but then hostAttributes must be separately
      funneled to configure, which is cumbersome.
      Since this delta seems hard to measure we will not bother atm.
      */
      // install host attributes
      this._marshalHostAttributes();
      // acquire initial instance attribute values
      this._marshalAttributes();
      // top-down initial distribution, configuration, & ready callback
      this._tryReady();
    },

    _marshalBehavior: function(b) {
      // establish listeners on instance
      if (b.listeners) {
        this._listenListeners(b.listeners);
      }
    }

  });
/*
Note: <body is="body-bind"> is an experiment taken from
https://github.com/PolymerLabs/polymer-experiments/tree/master/body-bind.
It allows bindings in <body>, and other Polymer features which are lazily
upgraded. This approach does not block rendering!.
*/

(function() {

  var origTryReady = Polymer.Base._tryReady;

  Polymer.Base._tryReady = function() {
    // Configure properties bound from host lazily at startup
    // This is opt-in because it is expensive; it either needs to be in
    // a permanent top-level host with `lazyChildren` property set, or else
    // each instance needs to set the `lazy-bind` attribute
    if (this.is && this.hasAttribute('lazy-bind') ||
        (this.dataHost && this.dataHost.lazyChildren)) {
      for (var p in this._propertyEffects) {
        if (this.hasOwnProperty(p)) {
          var v = this[p];
          delete this[p];
          this._config[p] = v;
        }
      }
    }
    origTryReady.apply(this, arguments);
  };

  Polymer.LightDomBindingBehavior = {

    lazyChildren: true,

    _initFeatures: function() {
      // By default, LightDomBindingBehavior becomes the permanent top-level
      // host, so that any lazy-loaded children are automatically hosted by
      // this element, and by virtue of `dataHost.lazyChildren: true` will
      // lazily configure any properties bound from the host.
      this._beginHosting();
      // Instance time binding of light children
      this.root = this;
      this._template = this;
      this._content = this;
      this._notes = null;
      this._prepAnnotations();
      this._prepEffects();
      this._prepBindings();
      this._setupConfigure();
      this._marshalAnnotationReferences();
      this._marshalInstanceEffects();
      this._tryReady();
    },
  };

}());

// Similar to `<template is="dom-bind">`, but uses the body's light DOM
// as the template.  If more advanced features such as event listeners,
// computed functions, etc. are needed, just make an `extends: 'body'`
// element that uses the `Polymer.LightDomBindingBehavior`, and use
// normal Polymer idioms.

Polymer({

  extends: 'body',

  is: 'body-bind',

  behaviors: [Polymer.LightDomBindingBehavior]

});
(function() {

  var propertyUtils = Polymer.StyleProperties;
  var styleUtil = Polymer.StyleUtil;
  var cssParse = Polymer.CssParse;
  var styleDefaults = Polymer.StyleDefaults;
  var styleTransformer = Polymer.StyleTransformer;

  Polymer({

    is: 'custom-style',
    extends: 'style',
    _template: null,

    properties: {
      // include is a property so that it deserializes
      /**
       * Specify `include` to identify a `dom-module` containing style data which
       * should be used within the `custom-style`. By using `include` style data
       * may be shared between multiple different `custom-style` elements.
       *
       * To include multiple `dom-modules`, use `include="module1 module2"`.
       */
      include: String
    },

    ready: function() {
      // NOTE: we cannot just check attached because custom elements in
      // HTMLImports do not get attached.
      this._tryApply();
    },

    attached: function() {
      this._tryApply();
    },

    _tryApply: function() {
      if (!this._appliesToDocument) {
        // only apply variables iff this style is not inside a dom-module
        if (this.parentNode &&
          (this.parentNode.localName !== 'dom-module')) {
          this._appliesToDocument = true;
          // used applied element from HTMLImports polyfill or this
          var e = this.__appliedElement || this;
          styleDefaults.addStyle(e);
          // we may not have any textContent yet due to parser yielding
          // if so, wait until we do...
          if (e.textContent || this.include) {
            this._apply(true);
          } else {
            var self = this;
            var observer = new MutationObserver(function() {
              observer.disconnect();
              self._apply(true);
            });
            observer.observe(e, {childList: true});
          }
        }
      }
    },

    // polyfill this style with root scoping and
    // apply custom properties!
    _apply: function(deferProperties) {
      // used applied element from HTMLImports polyfill or this
      var e = this.__appliedElement || this;
      if (this.include) {
        e.textContent = styleUtil.cssFromModules(this.include, true) +
          e.textContent;
      }
      if (e.textContent) {
        styleUtil.forEachRule(styleUtil.rulesForStyle(e), function(rule) {
          styleTransformer.documentRule(rule);
        });
        // Allow all custom-styles defined in this turn to register
        // before applying any properties. This helps ensure that all properties
        // are defined before any are consumed.
        // Premature application of properties can occur in 2 cases:
        // (1) A property `--foo` is consumed in a custom-style
        // before another custom-style produces `--foo`.
        // In general, we require custom properties to be defined before being
        // used in elements so supporting this for custom-style
        // is dubious but is slightly more like native properties where this
        // is supported.
        // (2) A set of in order styles (A, B) are re-ordered due to a parser
        // yield that makes A wait for textContent. This reorders its
        // `_apply` after B.
        // This case should only occur with native webcomponents.
        var self = this;
        var fn = function fn() {
          self._applyCustomProperties(e);
        }
        if (this._pendingApplyProperties) {
          cancelAnimationFrame(this._pendingApplyProperties);
          this._pendingApplyProperties = null;
        }
        if (deferProperties) {
          this._pendingApplyProperties = requestAnimationFrame(fn);
        } else {
          fn();
        }
      }
    },

    _applyCustomProperties: function(element) {
      this._computeStyleProperties();
      var props = this._styleProperties;
      var rules = styleUtil.rulesForStyle(element);
      element.textContent = styleUtil.toCssText(rules, function(rule) {
        var css = rule.cssText = rule.parsedCssText;
        if (rule.propertyInfo && rule.propertyInfo.cssText) {
          // remove property assignments
          // so next function isn't confused
          // NOTE: we have 3 categories of css:
          // (1) normal properties,
          // (2) custom property assignments (--foo: red;),
          // (3) custom property usage: border: var(--foo); @apply(--foo);
          // In elements, 1 and 3 are separated for efficiency; here they
          // are not and this makes this case unique.
          css = cssParse.removeCustomPropAssignment(css);
          // replace with reified properties, scenario is same as mixin
          rule.cssText = propertyUtils.valueForProperties(css, props);
        }
      });
    }

  });

})();
/**
   * The `Polymer.Templatizer` behavior adds methods to generate instances of
   * templates that are each managed by an anonymous `Polymer.Base` instance.
   *
   * Example:
   *
   *     // Get a template from somewhere, e.g. light DOM
   *     var template = Polymer.dom(this).querySelector('template');
   *     // Prepare the template
   *     this.templatize(template);
   *     // Instance the template with an initial data model
   *     var instance = this.stamp({myProp: 'initial'});
   *     // Insert the instance's DOM somewhere, e.g. light DOM
   *     Polymer.dom(this).appendChild(instance.root);
   *     // Changing a property on the instance will propagate to bindings
   *     // in the template
   *     instance.myProp = 'new value';
   *
   * Users of `Templatizer` may need to implement the following abstract
   * API's to determine how properties and paths from the host should be
   * forwarded into to instances:
   *
   *     _forwardParentProp: function(prop, value)
   *     _forwardParentPath: function(path, value)
   *
   * Likewise, users may implement these additional abstract API's to determine
   * how instance-specific properties that change on the instance should be
   * forwarded out to the host, if necessary.
   *
   *     _forwardInstanceProp: function(inst, prop, value)
   *     _forwardInstancePath: function(inst, path, value)
   *
   * In order to determine which properties are instance-specific and require
   * custom forwarding via `_forwardInstanceProp`/`_forwardInstancePath`,
   * define an `_instanceProps` map containing keys for each instance prop,
   * for example:
   *
   *     _instanceProps: {
   *       item: true,
   *       index: true
   *     }
   *
   * Any properties used in the template that are not defined in _instanceProp
   * will be forwarded out to the host automatically.
   *
   * Users should also implement the following abstract function to show or
   * hide any DOM generated using `stamp`:
   *
   *     _showHideChildren: function(shouldHide)
   *
   * @polymerBehavior
   */
  Polymer.Templatizer = {

    properties: {
      __hideTemplateChildren__: {
        observer: '_showHideChildren'
      }
    },

    // Extension point for overrides
    _instanceProps: Polymer.nob,

    _parentPropPrefix: '_parent_',

    /**
     * Prepares a template containing Polymer bindings by generating
     * a constructor for an anonymous `Polymer.Base` subclass to serve as the
     * binding context for the provided template.
     *
     * Use `this.stamp` to create instances of the template context containing
     * a `root` fragment that may be stamped into the DOM.
     *
     * @method templatize
     * @param {HTMLTemplateElement} template The template to process.
     */
    templatize: function(template) {
      this._templatized = template;
      // TODO(sjmiles): supply _alternate_ content reference missing from root
      // templates (not nested). `_content` exists to provide content sharing
      // for nested templates.
      if (!template._content) {
        template._content = template.content;
      }
      // fast path if template's anonymous class has been memoized
      if (template._content._ctor) {
        this.ctor = template._content._ctor;
        //console.log('Templatizer.templatize: using memoized archetype');
        // forward parent properties to archetype
        this._prepParentProperties(this.ctor.prototype, template);
        return;
      }
      // `archetype` is the prototype of the anonymous
      // class created by the templatizer
      var archetype = Object.create(Polymer.Base);
      // normally Annotations.parseAnnotations(template) but
      // archetypes do special caching
      this._customPrepAnnotations(archetype, template);

      // forward parent properties to archetype
      this._prepParentProperties(archetype, template);

      // setup accessors
      archetype._prepEffects();
      this._customPrepEffects(archetype);
      archetype._prepBehaviors();
      archetype._prepPropertyInfo();
      archetype._prepBindings();

      // boilerplate code
      archetype._notifyPathUp = this._notifyPathUpImpl;
      archetype._scopeElementClass = this._scopeElementClassImpl;
      archetype.listen = this._listenImpl;
      archetype._showHideChildren = this._showHideChildrenImpl;
      archetype.__setPropertyOrig = this.__setProperty;
      archetype.__setProperty = this.__setPropertyImpl;
      // boilerplate code
      var _constructor = this._constructorImpl;
      var ctor = function TemplateInstance(model, host) {
        _constructor.call(this, model, host);
      };
      // standard references
      ctor.prototype = archetype;
      archetype.constructor = ctor;
      // TODO(sjmiles): constructor cache?
      template._content._ctor = ctor;
      // TODO(sjmiles): choose less general name
      this.ctor = ctor;
    },

    _getRootDataHost: function() {
      return (this.dataHost && this.dataHost._rootDataHost) || this.dataHost;
    },

    _showHideChildrenImpl: function(hide) {
      var c = this._children;
      for (var i=0; i<c.length; i++) {
        var n = c[i];
        // Ignore non-changes
        if (Boolean(hide) != Boolean(n.__hideTemplateChildren__)) {
          if (n.nodeType === Node.TEXT_NODE) {
            if (hide) {
              n.__polymerTextContent__ = n.textContent;
              n.textContent = '';
            } else {
              n.textContent = n.__polymerTextContent__;
            }
          } else if (n.style) {
            if (hide) {
              n.__polymerDisplay__ = n.style.display;
              n.style.display = 'none';
            } else {
              n.style.display = n.__polymerDisplay__;
            }
          }
        }
        n.__hideTemplateChildren__ = hide;
      }
    },

    __setPropertyImpl: function(property, value, fromAbove, node) {
      if (node && node.__hideTemplateChildren__ && property == 'textContent') {
        property = '__polymerTextContent__';
      }
      this.__setPropertyOrig(property, value, fromAbove, node);
    },

    _debounceTemplate: function(fn) {
      Polymer.dom.addDebouncer(this.debounce('_debounceTemplate', fn));
    },

    _flushTemplates: function() {
      Polymer.dom.flush();
    },

    _customPrepEffects: function(archetype) {
      var parentProps = archetype._parentProps;
      for (var prop in parentProps) {
        archetype._addPropertyEffect(prop, 'function',
          this._createHostPropEffector(prop));
      }
      for (prop in this._instanceProps) {
        archetype._addPropertyEffect(prop, 'function',
          this._createInstancePropEffector(prop));
      }
    },

    _customPrepAnnotations: function(archetype, template) {
      archetype._template = template;
      var c = template._content;
      if (!c._notes) {
        var rootDataHost = archetype._rootDataHost;
        if (rootDataHost) {
          Polymer.Annotations.prepElement = function() {
            rootDataHost._prepElement();
          }
        }
        c._notes = Polymer.Annotations.parseAnnotations(template);
        Polymer.Annotations.prepElement = null;
        this._processAnnotations(c._notes);
      }
      archetype._notes = c._notes;
      archetype._parentProps = c._parentProps;
    },

    // Sets up accessors on the template to call abstract _forwardParentProp
    // API that should be implemented by Templatizer users to get parent
    // properties to their template instances.  These accessors are memoized
    // on the archetype and copied to instances.
    _prepParentProperties: function(archetype, template) {
      var parentProps = this._parentProps = archetype._parentProps;
      if (this._forwardParentProp && parentProps) {
        // Prototype setup (memoized on archetype)
        var proto = archetype._parentPropProto;
        var prop;
        if (!proto) {
          for (prop in this._instanceProps) {
            delete parentProps[prop];
          }
          proto = archetype._parentPropProto = Object.create(null);
          if (template != this) {
            // Assumption: if `this` isn't the template being templatized,
            // assume that the template is not a Poylmer.Base, so prep it
            // for binding
            Polymer.Bind.prepareModel(proto);
            Polymer.Base.prepareModelNotifyPath(proto);
          }
          // Create accessors for each parent prop that forward the property
          // to template instances through abstract _forwardParentProp API
          // that should be implemented by Templatizer users
          for (prop in parentProps) {
            var parentProp = this._parentPropPrefix + prop;
            // TODO(sorvell): remove reference Bind library functions here.
            // Needed for effect optimization.
            var effects = [{
              kind: 'function',
              effect: this._createForwardPropEffector(prop),
              fn: Polymer.Bind._functionEffect
            }, {
              kind: 'notify',
              fn: Polymer.Bind._notifyEffect,
              effect: {event:
                Polymer.CaseMap.camelToDashCase(parentProp) + '-changed'}
            }];
            Polymer.Bind._createAccessors(proto, parentProp, effects);
          }
        }
        // capture this reference for use below
        var self = this;
        // Instance setup
        if (template != this) {
          Polymer.Bind.prepareInstance(template);
          template._forwardParentProp = function(source, value) {
            self._forwardParentProp(source, value);
          }
        }
        this._extendTemplate(template, proto);
        template._pathEffector = function(path, value, fromAbove) {
          return self._pathEffectorImpl(path, value, fromAbove);
        }
      }
    },

    _createForwardPropEffector: function(prop) {
      return function(source, value) {
        this._forwardParentProp(prop, value);
      };
    },

    _createHostPropEffector: function(prop) {
      var prefix = this._parentPropPrefix;
      return function(source, value) {
        this.dataHost._templatized[prefix + prop] = value;
      };
    },

    _createInstancePropEffector: function(prop) {
      return function(source, value, old, fromAbove) {
        if (!fromAbove) {
          this.dataHost._forwardInstanceProp(this, prop, value);
        }
      };
    },

    // Similar to Polymer.Base.extend, but retains any previously set instance
    // values (_propertySetter back on instance once accessor is installed)
    _extendTemplate: function(template, proto) {
      var n$ = Object.getOwnPropertyNames(proto);
      if (proto._propertySetter) {
        // _propertySetter API may need to be copied onto the template,
        // and it needs to come first to allow the property swizzle below
        template._propertySetter = proto._propertySetter;
      }
      for (var i=0, n; (i<n$.length) && (n=n$[i]); i++) {
        var val = template[n];
        var pd = Object.getOwnPropertyDescriptor(proto, n);
        Object.defineProperty(template, n, pd);
        if (val !== undefined) {
          template._propertySetter(n, val);
        }
      }
    },

    // Extension points for Templatizer sub-classes
    /* eslint-disable no-unused-vars */
    _showHideChildren: function(hidden) { },
    _forwardInstancePath: function(inst, path, value) { },
    _forwardInstanceProp: function(inst, prop, value) { },
    // Defined-check rather than thunk used to avoid unnecessary work for these:
    // _forwardParentPath: function(path, value) { },
    // _forwardParentProp: function(prop, value) { },
    /* eslint-enable no-unused-vars */

    _notifyPathUpImpl: function(path, value) {
      var dataHost = this.dataHost;
      var dot = path.indexOf('.');
      var root = dot < 0 ? path : path.slice(0, dot);
      // Call extension point for Templatizer sub-classes
      dataHost._forwardInstancePath.call(dataHost, this, path, value);
      if (root in dataHost._parentProps) {
        dataHost._templatized._notifyPath(dataHost._parentPropPrefix + path, value);
      }
    },

    // Overrides Base notify-path module
    _pathEffectorImpl: function(path, value, fromAbove) {
      if (this._forwardParentPath) {
        if (path.indexOf(this._parentPropPrefix) === 0) {
          var subPath = path.substring(this._parentPropPrefix.length);
          var model = this._modelForPath(subPath);
          if (model in this._parentProps) {
            this._forwardParentPath(subPath, value);
          }
        }
      }
      Polymer.Base._pathEffector.call(this._templatized, path, value, fromAbove);
    },

    _constructorImpl: function(model, host) {
      this._rootDataHost = host._getRootDataHost();
      this._setupConfigure(model);
      this._registerHost(host);
      this._beginHosting();
      this.root = this.instanceTemplate(this._template);
      this.root.__noContent = !this._notes._hasContent;
      this.root.__styleScoped = true;
      this._endHosting();
      this._marshalAnnotatedNodes();
      this._marshalInstanceEffects();
      this._marshalAnnotatedListeners();
      // each row is a document fragment which is lost when we appendChild,
      // so we have to track each child individually
      var children = [];
      for (var n = this.root.firstChild; n; n=n.nextSibling) {
        children.push(n);
        n._templateInstance = this;
      }
      // Since archetype overrides Base/HTMLElement, Safari complains
      // when accessing `children`
      this._children = children;
      // Ensure newly stamped nodes reflect host's hidden state
      if (host.__hideTemplateChildren__) {
        this._showHideChildren(true);
      }
      // ready self and children
      this._tryReady();
    },

    // Decorate events with model (template instance)
    _listenImpl: function(node, eventName, methodName) {
      var model = this;
      var host = this._rootDataHost;
      var handler = host._createEventHandler(node, eventName, methodName);
      var decorated = function(e) {
        e.model = model;
        handler(e);
      };
      host._listen(node, eventName, decorated);
    },

    _scopeElementClassImpl: function(node, value) {
      var host = this._rootDataHost;
      if (host) {
        return host._scopeElementClass(node, value);
      }
      return value;
    },

    /**
     * Creates an instance of the template previously processed via
     * a call to `templatize`.
     *
     * The object returned is an anonymous subclass of Polymer.Base that
     * has accessors generated to manage data in the template.  The DOM for
     * the instance is contained in a DocumentFragment called `root` on
     * the instance returned and must be manually inserted into the DOM
     * by the user.
     *
     * Note that a call to `templatize` must be called once before using
     * `stamp`.
     *
     * @method stamp
     * @param {Object=} model An object containing key/values to serve as the
     *   initial data configuration for the instance.  Note that properties
     *   from the host used in the template are automatically copied into
     *   the model.
     * @return {Polymer.Base} The Polymer.Base instance to manage the template
     *   instance.
     */
    stamp: function(model) {
      model = model || {};
      if (this._parentProps) {
        var templatized = this._templatized;
        for (var prop in this._parentProps) {
          if (model[prop] === undefined) {
            model[prop] = templatized[this._parentPropPrefix + prop];
          }
        }
      }
      return new this.ctor(model, this);
    },

    /**
     * Returns the template "model" associated with a given element, which
     * serves as the binding scope for the template instance the element is
     * contained in. A template model is an instance of `Polymer.Base`, and
     * should be used to manipulate data associated with this template instance.
     *
     * Example:
     *
     *   var model = modelForElement(el);
     *   if (model.index < 10) {
     *     model.set('item.checked', true);
     *   }
     *
     * @method modelForElement
     * @param {HTMLElement} el Element for which to return a template model.
     * @return {Object<Polymer.Base>} Model representing the binding scope for
     *   the element.
     */
    modelForElement: function(el) {
      var model;
      while (el) {
        // An element with a _templateInstance marks the top boundary
        // of a scope; walk up until we find one, and then ensure that
        // its dataHost matches `this`, meaning this dom-repeat stamped it
        if ((model = el._templateInstance)) {
          // Found an element stamped by another template; keep walking up
          // from its dataHost
          if (model.dataHost != this) {
            el = model.dataHost;
          } else {
            return model;
          }
        } else {
          // Still in a template scope, keep going up until
          // a _templateInstance is found
          el = el.parentNode;
        }
      }
    }

  };
/**
   * Creates a pseudo-custom-element that maps property values to bindings
   * in DOM.
   * 
   * `stamp` method creates an instance of the pseudo-element. The instance
   * references a document-fragment containing the stamped and bound dom
   * via it's `root` property. 
   *  
   */
  Polymer({

    is: 'dom-template',
    extends: 'template',
    _template: null,

    behaviors: [
      Polymer.Templatizer
    ],

    ready: function() {
      this.templatize(this);
    }

  });
Polymer._collections = new WeakMap();

  Polymer.Collection = function(userArray) {
    Polymer._collections.set(userArray, this);
    this.userArray = userArray;
    this.store = userArray.slice();
    this.initMap();
  };

  Polymer.Collection.prototype = {

    constructor: Polymer.Collection,

    initMap: function() {
      var omap = this.omap = new WeakMap();
      var pmap = this.pmap = {};
      var s = this.store;
      for (var i=0; i<s.length; i++) {
        var item = s[i];
        if (item && typeof item == 'object') {
          omap.set(item, i);
        } else {
          pmap[item] = i;
        }
      }
    },

    add: function(item) {
      var key = this.store.push(item) - 1;
      if (item && typeof item == 'object') {
        this.omap.set(item, key);
      } else {
        this.pmap[item] = key;
      }
      return '#' + key;
    },

    removeKey: function(key) {
      if ((key = this._parseKey(key))) {
        this._removeFromMap(this.store[key]);
        delete this.store[key];
      }
    },

    _removeFromMap: function(item) {
      if (item && typeof item == 'object') {
        this.omap.delete(item);
      } else {
        delete this.pmap[item];
      }
    },

    remove: function(item) {
      var key = this.getKey(item);
      this.removeKey(key);
      return key;
    },

    getKey: function(item) {
      var key;
      if (item && typeof item == 'object') {
        key = this.omap.get(item);
      } else {
        key = this.pmap[item];
      }
      if (key != undefined) {
        return '#' + key;
      }
    },

    getKeys: function() {
      return Object.keys(this.store).map(function(key) {
        return '#' + key;
      });
    },

    _parseKey: function(key) {
      if (key && key[0] == '#') {
        return key.slice(1);
      }
    },

    setItem: function(key, item) {
      if ((key = this._parseKey(key))) {
        var old = this.store[key];
        if (old) {
          this._removeFromMap(old);
        }
        if (item && typeof item == 'object') {
          this.omap.set(item, key);
        } else {
          this.pmap[item] = key;
        }
        this.store[key] = item;
      }
    },

    getItem: function(key) {
      if ((key = this._parseKey(key))) {
        return this.store[key];
      }
    },

    getItems: function() {
      var items = [], store = this.store;
      for (var key in store) {
        items.push(store[key]);
      }
      return items;
    },

    // Accepts an array of standard splice records (index, addedCount, removed
    // array), and performs two key actions:
    // 1. Applies the splice to the collection: adds newly added items to the
    //    store which generates a unique key for it, and removes removed items
    //    (and their key) from the store
    // 2. Generates a "keySplices" record (in contrast to the input
    //    "indexSplices"), which contains an array of added and removed keys
    //    corresponding to the added/removed items
    _applySplices: function(splices) {
      // Dedupe added and removed keys to a final added/removed map
      var keyMap = {}, key;
      for (var i=0, s; (i<splices.length) && (s=splices[i]); i++) {
        s.addedKeys = [];
        for (var j=0; j<s.removed.length; j++) {
          key = this.getKey(s.removed[j]);
          keyMap[key] = keyMap[key] ? null : -1;
        }
        for (j=0; j<s.addedCount; j++) {
          var item = this.userArray[s.index + j];
          key = this.getKey(item);
          key = (key === undefined) ? this.add(item) : key;
          keyMap[key] = keyMap[key] ? null : 1;
          // Add an "addedKeys" array to indexSplices to capture keys associated
          // with added items, since references to added items can be lost by
          // further changes to the array by the time the splice is consumed
          s.addedKeys.push(key);
        }
      }
      // Convert added/removed key map to added/removed arrays
      var removed = [];
      var added = [];
      for (key in keyMap) {
        if (keyMap[key] < 0) {
          this.removeKey(key);
          removed.push(key);
        }
        if (keyMap[key] > 0) {
          added.push(key);
        }
      }
      return [{
        removed: removed,
        added: added
      }];
    }

  };

  Polymer.Collection.get = function(userArray) {
    return Polymer._collections.get(userArray) ||
      new Polymer.Collection(userArray);
  };

  Polymer.Collection.applySplices = function(userArray, splices) {
    // Only apply splices & generate keySplices if the array already has a
    // backing Collection, meaning there is an element monitoring its keys;
    // Splices that happen before the collection has been created must be
    // discarded to avoid double-entries
    var coll = Polymer._collections.get(userArray);
    return coll ? coll._applySplices(splices) : null;
  };
Polymer({

    is: 'dom-repeat',
    extends: 'template',
    _template: null,

    /**
     * Fired whenever DOM is added or removed by this template (by
     * default, rendering occurs lazily).  To force immediate rendering, call
     * `render`.
     *
     * @event dom-change
     */

    properties: {

      /**
       * An array containing items determining how many instances of the template
       * to stamp and that that each template instance should bind to.
       */
      items: {
        type: Array
      },

      /**
       * The name of the variable to add to the binding scope for the array
       * element associated with a given template instance.
       */
      as: {
        type: String,
        value: 'item'
      },

      /**
       * The name of the variable to add to the binding scope with the index
       * for the inst.  If `sort` is provided, the index will reflect the
       * sorted order (rather than the original array order).
       */
      indexAs: {
        type: String,
        value: 'index'
      },

      /**
       * A function that should determine the sort order of the items.  This
       * property should either be provided as a string, indicating a method
       * name on the element's host, or else be an actual function.  The
       * function should match the sort function passed to `Array.sort`.
       * Using a sort function has no effect on the underlying `items` array.
       */
      sort: {
        type: Function,
        observer: '_sortChanged'
      },

      /**
       * A function that can be used to filter items out of the view.  This
       * property should either be provided as a string, indicating a method
       * name on the element's host, or else be an actual function.  The
       * function should match the sort function passed to `Array.filter`.
       * Using a filter function has no effect on the underlying `items` array.
       */
      filter: {
        type: Function,
        observer: '_filterChanged'
      },

      /**
       * When using a `filter` or `sort` function, the `observe` property
       * should be set to a space-separated list of the names of item
       * sub-fields that should trigger a re-sort or re-filter when changed.
       * These should generally be fields of `item` that the sort or filter
       * function depends on.
       */
      observe: {
        type: String,
        observer: '_observeChanged'
      },

      /**
       * When using a `filter` or `sort` function, the `delay` property
       * determines a debounce time after a change to observed item
       * properties that must pass before the filter or sort is re-run.
       * This is useful in rate-limiting shuffing of the view when
       * item changes may be frequent.
       */
      delay: Number,

      /**
       * Count of currently rendered items after `filter` (if any) has been applied.
       * If "chunking mode" is enabled, `renderedItemCount` is updated each time a
       * set of template instances is rendered.
       *
       */
      renderedItemCount: {
        type: Number,
        notify: true,
        readOnly: true
      },

      /**
       * Defines an initial count of template instances to render after setting
       * the `items` array, before the next paint, and puts the `dom-repeat`
       * into "chunking mode".  The remaining items will be created and rendered
       * incrementally at each animation frame therof until all instances have
       * been rendered.
       */
      initialCount: {
        type: Number,
        observer: '_initializeChunking'
      },

      /**
       * When `initialCount` is used, this property defines a frame rate to
       * target by throttling the number of instances rendered each frame to
       * not exceed the budget for the target frame rate.  Setting this to a
       * higher number will allow lower latency and higher throughput for
       * things like event handlers, but will result in a longer time for the
       * remaining items to complete rendering.
       */
      targetFramerate: {
        type: Number,
        value: 20
      },

      _targetFrameTime: {
        type: Number,
        computed: '_computeFrameTime(targetFramerate)'
      }

    },

    behaviors: [
      Polymer.Templatizer
    ],

    observers: [
      '_itemsChanged(items.*)'
    ],

    created: function() {
      this._instances = [];
      this._pool = [];
      this._limit = Infinity;
      var self = this;
      this._boundRenderChunk = function() {
        self._renderChunk();
      };
    },

    detached: function() {
      this.__isDetached = true;
      for (var i=0; i<this._instances.length; i++) {
        this._detachInstance(i);
      }
    },

    attached: function() {
      // only perform attachment if the element was previously detached.
      if (this.__isDetached) {
        this.__isDetached = false;
        var parent = Polymer.dom(Polymer.dom(this).parentNode);
        for (var i=0; i<this._instances.length; i++) {
          this._attachInstance(i, parent);
        }
      }
    },

    ready: function() {
      // Template instance props that should be excluded from forwarding
      this._instanceProps = {
        __key__: true
      };
      this._instanceProps[this.as] = true;
      this._instanceProps[this.indexAs] = true;
      // Templatizing (generating the instance constructor) needs to wait
      // until ready, since won't have its template content handed back to
      // it until then
      if (!this.ctor) {
        this.templatize(this);
      }
    },

    _sortChanged: function(sort) {
      var dataHost = this._getRootDataHost();
      this._sortFn = sort && (typeof sort == 'function' ? sort :
        function() { return dataHost[sort].apply(dataHost, arguments); });
      this._needFullRefresh = true;
      if (this.items) {
        this._debounceTemplate(this._render);
      }
    },

    _filterChanged: function(filter) {
      var dataHost = this._getRootDataHost();
      this._filterFn = filter && (typeof filter == 'function' ? filter :
        function() { return dataHost[filter].apply(dataHost, arguments); });
      this._needFullRefresh = true;
      if (this.items) {
        this._debounceTemplate(this._render);
      }
    },

    _computeFrameTime: function(rate) {
      return Math.ceil(1000/rate);
    },

    _initializeChunking: function() {
      if (this.initialCount) {
        this._limit = this.initialCount;
        this._chunkCount = this.initialCount;
        this._lastChunkTime = performance.now();
      }
    },

    _tryRenderChunk: function() {
      // Debounced so that multiple calls through `_render` between animation
      // frames only queue one new rAF (e.g. array mutation & chunked render)
      if (this.items && this._limit < this.items.length) {
        this.debounce('renderChunk', this._requestRenderChunk);
      }
    },

    _requestRenderChunk: function() {
      requestAnimationFrame(this._boundRenderChunk);
    },

    _renderChunk: function() {
      // Simple auto chunkSize throttling algorithm based on feedback loop:
      // measure actual time between frames and scale chunk count by ratio
      // of target/actual frame time
      var currChunkTime = performance.now();
      var ratio = this._targetFrameTime / (currChunkTime - this._lastChunkTime);
      this._chunkCount = Math.round(this._chunkCount * ratio) || 1;
      this._limit += this._chunkCount;
      this._lastChunkTime = currChunkTime;
      this._debounceTemplate(this._render);
    },

    _observeChanged: function() {
      this._observePaths = this.observe &&
        this.observe.replace('.*', '.').split(' ');
    },

    _itemsChanged: function(change) {
      if (change.path == 'items') {
        if (Array.isArray(this.items)) {
          this.collection = Polymer.Collection.get(this.items);
        } else if (!this.items) {
          this.collection = null;
        } else {
          this._error(this._logf('dom-repeat', 'expected array for `items`,' +
            ' found', this.items));
        }
        this._keySplices = [];
        this._indexSplices = [];
        this._needFullRefresh = true;
        this._initializeChunking();
        this._debounceTemplate(this._render);
      } else if (change.path == 'items.splices') {
        this._keySplices = this._keySplices.concat(change.value.keySplices);
        this._indexSplices = this._indexSplices.concat(change.value.indexSplices);
        this._debounceTemplate(this._render);
      } else { // items.*
        // slice off 'items.' ('items.'.length == 6)
        var subpath = change.path.slice(6);
        this._forwardItemPath(subpath, change.value);
        this._checkObservedPaths(subpath);
      }
    },

    _checkObservedPaths: function(path) {
      if (this._observePaths) {
        path = path.substring(path.indexOf('.') + 1);
        var paths = this._observePaths;
        for (var i=0; i<paths.length; i++) {
          if (path.indexOf(paths[i]) === 0) {
            // TODO(kschaaf): interim solution: ideally this is just an incremental
            // insertion sort of the changed item
            this._needFullRefresh = true;
            if (this.delay) {
              this.debounce('render', this._render, this.delay);
            } else {
              this._debounceTemplate(this._render);
            }
            return;
          }
        }
      }
    },

    /**
     * Forces the element to render its content. Normally rendering is
     * asynchronous to a provoking change. This is done for efficiency so
     * that multiple changes trigger only a single render. The render method
     * should be called if, for example, template rendering is required to
     * validate application state.
     */
    render: function() {
      // Queue this repeater, then flush all in order
      this._needFullRefresh = true;
      this._debounceTemplate(this._render);
      this._flushTemplates();
    },

    _render: function() {
      // Choose rendering path: full vs. incremental using splices
      if (this._needFullRefresh) {
        // Full refresh when items, sort, or filter change, or when render() called
        this._applyFullRefresh();
        this._needFullRefresh = false;
      } else if (this._keySplices.length) {
        // Incremental refresh when splices were queued
        if (this._sortFn) {
          this._applySplicesUserSort(this._keySplices);
        } else {
          if (this._filterFn) {
            // TODK(kschaaf): Filtering using array sort takes slow path
            this._applyFullRefresh();
          } else {
            this._applySplicesArrayOrder(this._indexSplices);
          }
        }
      } else {
        // Otherwise only limit changed; no change to instances, just need to
        // upgrade more placeholders to instances
      }
      this._keySplices = [];
      this._indexSplices = [];
      // Update final _keyToInstIdx and instance indices, and
      // upgrade/downgrade placeholders
      var keyToIdx = this._keyToInstIdx = {};
      for (var i=this._instances.length-1; i>=0; i--) {
        var inst = this._instances[i];
        if (inst.isPlaceholder && i<this._limit) {
          inst = this._insertInstance(i, inst.__key__);
        } else if (!inst.isPlaceholder && i>=this._limit) {
          inst = this._downgradeInstance(i, inst.__key__);
        }
        keyToIdx[inst.__key__] = i;
        if (!inst.isPlaceholder) {
          inst.__setProperty(this.indexAs, i, true);
        }
      }
      // Reset the pool
      // TODO(kschaaf): Reuse pool across turns and nested templates
      // Requires updating parentProps and dealing with the fact that path
      // notifications won't reach instances sitting in the pool, which
      // could result in out-of-sync instances since simply re-setting
      // `item` may not be sufficient if the pooled instance happens to be
      // the same item.
      this._pool.length = 0;
      // Set rendered item count
      this._setRenderedItemCount(this._instances.length);
      // Notify users
      this.fire('dom-change');
      // Check to see if we need to render more items
      this._tryRenderChunk();
    },

    // Render method 1: full refesh
    // ----
    // Full list of keys is pulled from the collection, then sorted, filtered,
    // and iterated to create (or reuse) existing instances
    _applyFullRefresh: function() {
      var c = this.collection;
      // Start with unordered keys for user sort,
      // or get them in array order for array order
      var keys;
      if (this._sortFn) {
        keys = c ? c.getKeys() : [];
      } else {
        keys = [];
        var items = this.items;
        if (items) {
          for (var i=0; i<items.length; i++) {
            keys.push(c.getKey(items[i]));
          }
        }
      }
      // capture reference for use in filter/sort fn's
      var self = this;
      // Apply user filter to keys
      if (this._filterFn) {
        keys = keys.filter(function(a) {
          return self._filterFn(c.getItem(a));
        });
      }
      // Apply user sort to keys
      if (this._sortFn) {
        keys.sort(function(a, b) {
          return self._sortFn(c.getItem(a), c.getItem(b));
        });
      }
      // Generate instances and assign items and keys
      for (i=0; i<keys.length; i++) {
        var key = keys[i];
        var inst = this._instances[i];
        if (inst) {
          inst.__key__ = key;
          if (!inst.isPlaceholder && i < this._limit) {
            inst.__setProperty(this.as, c.getItem(key), true);
          }
        } else if (i < this._limit) {
          this._insertInstance(i, key);
        } else {
          this._insertPlaceholder(i, key);
        }
      }
      // Remove any extra instances from previous state
      for (var j=this._instances.length-1; j>=i; j--) {
        this._detachAndRemoveInstance(j);
      }
    },

    _numericSort: function(a, b) {
      return a - b;
    },

    // Render method 2: incremental update using splices with user sort applied
    // ----
    // Removed/added keys are deduped, all removed rows are detached and pooled
    // first, and added rows are insertion-sorted into place using user sort
    _applySplicesUserSort: function(splices) {
      var c = this.collection;
      var keyMap = {};
      var key;
      // Dedupe added and removed keys to a final added/removed map
      for (var i=0, s; (i<splices.length) && (s=splices[i]); i++) {
        for (var j=0; j<s.removed.length; j++) {
          key = s.removed[j];
          keyMap[key] = keyMap[key] ? null : -1;
        }
        for (j=0; j<s.added.length; j++) {
          key = s.added[j];
          keyMap[key] = keyMap[key] ? null : 1;
        }
      }
      // Convert added/removed key map to added/removed arrays
      var removedIdxs = [];
      var addedKeys = [];
      for (key in keyMap) {
        if (keyMap[key] === -1) {
          removedIdxs.push(this._keyToInstIdx[key]);
        }
        if (keyMap[key] === 1) {
          addedKeys.push(key);
        }
      }
      // Remove & pool removed instances
      if (removedIdxs.length) {
        // Sort removed instances idx's then remove backwards,
        // so we don't invalidate instance index
        // use numeric sort, default .sort is alphabetic
        removedIdxs.sort(this._numericSort);
        for (i=removedIdxs.length-1; i>=0 ; i--) {
          var idx = removedIdxs[i];
          // Removed idx may be undefined if item was previously filtered out
          if (idx !== undefined) {
            this._detachAndRemoveInstance(idx);
          }
        }
      }
      // capture reference for use in filter/sort fn's
      var self = this;
      // Add instances for added keys
      if (addedKeys.length) {
        // Filter added keys
        if (this._filterFn) {
          addedKeys = addedKeys.filter(function(a) {
            return self._filterFn(c.getItem(a));
          });
        }
        // Sort added keys
        addedKeys.sort(function(a, b) {
          return self._sortFn(c.getItem(a), c.getItem(b));
        });
        // Insertion-sort new instances into place (from pool or newly created)
        var start = 0;
        for (i=0; i<addedKeys.length; i++) {
          start = this._insertRowUserSort(start, addedKeys[i]);
        }
      }
    },

    _insertRowUserSort: function(start, key) {
      var c = this.collection;
      var item = c.getItem(key);
      var end = this._instances.length - 1;
      var idx = -1;
      // Binary search for insertion point
      while (start <= end) {
        var mid = (start + end) >> 1;
        var midKey = this._instances[mid].__key__;
        var cmp = this._sortFn(c.getItem(midKey), item);
        if (cmp < 0) {
          start = mid + 1;
        } else if (cmp > 0) {
          end = mid - 1;
        } else {
          idx = mid;
          break;
        }
      }
      if (idx < 0) {
        idx = end + 1;
      }
      // Insert instance at insertion point
      this._insertPlaceholder(idx, key);
      return idx;
    },

    // Render method 3: incremental update using splices with array order
    // ----
    // Splices are processed in order; removed rows are pooled, and added
    // rows are as placeholders, and placeholders are updated to
    // actual rows at the end to take full advantage of removed rows
    _applySplicesArrayOrder: function(splices) {
      for (var i=0, s; (i<splices.length) && (s=splices[i]); i++) {
        // Detach & pool removed instances
        for (var j=0; j<s.removed.length; j++) {
          this._detachAndRemoveInstance(s.index);
        }
        for (j=0; j<s.addedKeys.length; j++) {
          this._insertPlaceholder(s.index+j, s.addedKeys[j]);
        }
      }
    },

    _detachInstance: function(idx) {
      var inst = this._instances[idx];
      if (!inst.isPlaceholder) {
        for (var i=0; i<inst._children.length; i++) {
          var el = inst._children[i];
          Polymer.dom(inst.root).appendChild(el);
        }
        return inst;
      }
    },

    _attachInstance: function(idx, parent) {
      var inst = this._instances[idx];
      if (!inst.isPlaceholder) {
        parent.insertBefore(inst.root, this);
      }
    },

    _detachAndRemoveInstance: function(idx) {
      var inst = this._detachInstance(idx);
      if (inst) {
        this._pool.push(inst);
      }
      this._instances.splice(idx, 1);
    },

    _insertPlaceholder: function(idx, key) {
      this._instances.splice(idx, 0, {
        isPlaceholder: true,
        __key__: key
      });
    },

    _stampInstance: function(idx, key) {
      var model = {
        __key__: key
      };
      model[this.as] = this.collection.getItem(key);
      model[this.indexAs] = idx;
      return this.stamp(model);
    },

    _insertInstance: function(idx, key) {
      var inst = this._pool.pop();
      if (inst) {
        // TODO(kschaaf): If the pool is shared across turns, parentProps
        // need to be re-set to reused instances in addition to item/key
        inst.__setProperty(this.as, this.collection.getItem(key), true);
        inst.__setProperty('__key__', key, true);
      } else {
        inst = this._stampInstance(idx, key);
      }
      var beforeRow = this._instances[idx + 1];
      var beforeNode = beforeRow && !beforeRow.isPlaceholder ? beforeRow._children[0] : this;
      var parentNode = Polymer.dom(this).parentNode;
      Polymer.dom(parentNode).insertBefore(inst.root, beforeNode);
      this._instances[idx] = inst;
      return inst;
    },

    _downgradeInstance: function(idx, key) {
      var inst = this._detachInstance(idx);
      if (inst) {
        this._pool.push(inst);
      }
      inst = {
        isPlaceholder: true,
        __key__: key
      };
      this._instances[idx] = inst;
      return inst;
    },

    // Implements extension point from Templatizer mixin
    _showHideChildren: function(hidden) {
      for (var i=0; i<this._instances.length; i++) {
        this._instances[i]._showHideChildren(hidden);
      }
    },

    // Called as a side effect of a template item change, responsible
    // for notifying items.<key-for-inst> change up to host
    _forwardInstanceProp: function(inst, prop, value) {
      if (prop == this.as) {
        var idx;
        if (this._sortFn || this._filterFn) {
          // Known slow lookup: when sorted/filtered, there is no way to
          // efficiently memoize the array index and keep it in sync with array
          // mutations, so we need to look the item up in the array
          // This can happen e.g. when array of strings is repeated into inputs
          idx = this.items.indexOf(this.collection.getItem(inst.__key__));
        } else {
          // When there is no sort/filter, the view index is the array index
          idx = inst[this.indexAs];
        }
        this.set('items.' + idx, value);
      }
    },

    // Implements extension point from Templatizer
    // Called as a side effect of a template instance path change, responsible
    // for notifying items.<key-for-inst>.<path> change up to host
    _forwardInstancePath: function(inst, path, value) {
      if (path.indexOf(this.as + '.') === 0) {
        this._notifyPath('items.' + inst.__key__ + '.' +
          path.slice(this.as.length + 1), value);
      }
    },

    // Implements extension point from Templatizer mixin
    // Called as side-effect of a host property change, responsible for
    // notifying parent path change on each inst
    _forwardParentProp: function(prop, value) {
      var i$ = this._instances;
      for (var i=0, inst; (i<i$.length) && (inst=i$[i]); i++) {
        if (!inst.isPlaceholder) {
          inst.__setProperty(prop, value, true);
        }
      }
    },

    // Implements extension point from Templatizer
    // Called as side-effect of a host path change, responsible for
    // notifying parent path change on each inst
    _forwardParentPath: function(path, value) {
      var i$ = this._instances;
      for (var i=0, inst; (i<i$.length) && (inst=i$[i]); i++) {
        if (!inst.isPlaceholder) {
          inst._notifyPath(path, value, true);
        }
      }
    },

    // Called as a side effect of a host items.<key>.<path> path change,
    // responsible for notifying item.<path> changes to inst for key
    _forwardItemPath: function(path, value) {
      if (this._keyToInstIdx) {
        var dot = path.indexOf('.');
        var key = path.substring(0, dot < 0 ? path.length : dot);
        var idx = this._keyToInstIdx[key];
        var inst = this._instances[idx];
        if (inst && !inst.isPlaceholder) {
          if (dot >= 0) {
            path = this.as + '.' + path.substring(dot+1);
            inst._notifyPath(path, value, true);
          } else {
            inst.__setProperty(this.as, value, true);
          }
        }
      }
    },

    /**
     * Returns the item associated with a given element stamped by
     * this `dom-repeat`.
     *
     * Note, to modify sub-properties of the item,
     * `modelForElement(el).set('item.<sub-prop>', value)`
     * should be used.
     *
     * @method itemForElement
     * @param {HTMLElement} el Element for which to return the item.
     * @return {any} Item associated with the element.
     */
    itemForElement: function(el) {
      var instance = this.modelForElement(el);
      return instance && instance[this.as];
    },

    /**
     * Returns the `Polymer.Collection` key associated with a given
     * element stamped by this `dom-repeat`.
     *
     * @method keyForElement
     * @param {HTMLElement} el Element for which to return the key.
     * @return {any} Key associated with the element.
     */
    keyForElement: function(el) {
      var instance = this.modelForElement(el);
      return instance && instance.__key__;
    },

    /**
     * Returns the inst index for a given element stamped by this `dom-repeat`.
     * If `sort` is provided, the index will reflect the sorted order (rather
     * than the original array order).
     *
     * @method indexForElement
     * @param {HTMLElement} el Element for which to return the index.
     * @return {any} Row index associated with the element (note this may
     *   not correspond to the array index if a user `sort` is applied).
     */
    indexForElement: function(el) {
      var instance = this.modelForElement(el);
      return instance && instance[this.indexAs];
    }

  });
Polymer({
    is: 'array-selector',
    _template: null,

    properties: {

      /**
       * An array containing items from which selection will be made.
       */
      items: {
        type: Array,
        observer: 'clearSelection'
      },

      /**
       * When `true`, multiple items may be selected at once (in this case,
       * `selected` is an array of currently selected items).  When `false`,
       * only one item may be selected at a time.
       */
      multi: {
        type: Boolean,
        value: false,
        observer: 'clearSelection'
      },

      /**
       * When `multi` is true, this is an array that contains any selected.
       * When `multi` is false, this is the currently selected item, or `null`
       * if no item is selected.
       */
      selected: {
        type: Object,
        notify: true
      },

      /**
       * When `multi` is false, this is the currently selected item, or `null`
       * if no item is selected.
       */
      selectedItem: {
        type: Object,
        notify: true
      },

      /**
       * When `true`, calling `select` on an item that is already selected
       * will deselect the item.
       */
      toggle: {
        type: Boolean,
        value: false
      }
    },

    /**
     * Clears the selection state.
     *
     * @method clearSelection
     */
    clearSelection: function() {
      // Unbind previous selection
      if (Array.isArray(this.selected)) {
        for (var i=0; i<this.selected.length; i++) {
          this.unlinkPaths('selected.' + i);
        }
      } else {
        this.unlinkPaths('selected');
        this.unlinkPaths('selectedItem');
      }
      // Initialize selection
      if (this.multi) {
        if (!this.selected || this.selected.length) {
          this.selected = [];
          this._selectedColl = Polymer.Collection.get(this.selected);
        }
      } else {
        this.selected = null;
        this._selectedColl = null;
      }
      this.selectedItem = null;
    },

    /**
     * Returns whether the item is currently selected.
     *
     * @method isSelected
     * @param {*} item Item from `items` array to test
     * @return {boolean} Whether the item is selected
     */
    isSelected: function(item) {
      if (this.multi) {
        return this._selectedColl.getKey(item) !== undefined;
      } else {
        return this.selected == item;
      }
    },

    /**
     * Deselects the given item if it is already selected.
     *
     * @method isSelected
     * @param {*} item Item from `items` array to deselect
     */
    deselect: function(item) {
      if (this.multi) {
        if (this.isSelected(item)) {
          var skey = this._selectedColl.getKey(item);
          this.arrayDelete('selected', item);
          this.unlinkPaths('selected.' + skey);
        }
      } else {
        this.selected = null;
        this.selectedItem = null;
        this.unlinkPaths('selected');
        this.unlinkPaths('selectedItem');
      }
    },

    /**
     * Selects the given item.  When `toggle` is true, this will automatically
     * deselect the item if already selected.
     *
     * @method isSelected
     * @param {*} item Item from `items` array to select
     */
    select: function(item) {
      var icol = Polymer.Collection.get(this.items);
      var key = icol.getKey(item);
      if (this.multi) {
        if (this.isSelected(item)) {
          if (this.toggle) {
            this.deselect(item);
          }
        } else {
          this.push('selected', item);
          var skey = this._selectedColl.getKey(item);
          this.linkPaths('selected.' + skey, 'items.' + key);
        }
      } else {
        if (this.toggle && item == this.selected) {
          this.deselect();
        } else {
          this.selected = item;
          this.selectedItem = item;
          this.linkPaths('selected', 'items.' + key);
          this.linkPaths('selectedItem', 'items.' + key);
        }
      }
    }

  });
/**
   * Stamps the template iff the `if` property is truthy.
   *
   * When `if` becomes falsey, the stamped content is hidden but not
   * removed from dom. When `if` subsequently becomes truthy again, the content
   * is simply re-shown. This approach is used due to its favorable performance
   * characteristics: the expense of creating template content is paid only
   * once and lazily.
   *
   * Set the `restamp` property to true to force the stamped content to be
   * created / destroyed when the `if` condition changes.
   */
  Polymer({

    is: 'dom-if',
    extends: 'template',
    _template: null,

    /**
     * Fired whenever DOM is added or removed/hidden by this template (by
     * default, rendering occurs lazily).  To force immediate rendering, call
     * `render`.
     *
     * @event dom-change
     */

    properties: {

      /**
       * A boolean indicating whether this template should stamp.
       */
      'if': {
        type: Boolean,
        value: false,
        observer: '_queueRender'
      },

      /**
       * When true, elements will be removed from DOM and discarded when `if`
       * becomes false and re-created and added back to the DOM when `if`
       * becomes true.  By default, stamped elements will be hidden but left
       * in the DOM when `if` becomes false, which is generally results
       * in better performance.
       */
      restamp: {
        type: Boolean,
        value: false,
        observer: '_queueRender'
      }

    },

    behaviors: [
      Polymer.Templatizer
    ],

    _queueRender: function() {
      this._debounceTemplate(this._render);
    },

    detached: function() {
      if (!this.parentNode ||
          (this.parentNode.nodeType == Node.DOCUMENT_FRAGMENT_NODE &&
           (!Polymer.Settings.hasShadow ||
            !(this.parentNode instanceof ShadowRoot)))) {
        this._teardownInstance();
      }
    },

    attached: function() {
      if (this.if && this.ctor) {
        // NOTE: ideally should not be async, but node can be attached
        // when shady dom is in the act of distributing/composing so push it out
        this.async(this._ensureInstance);
      }
    },

    /**
     * Forces the element to render its content. Normally rendering is
     * asynchronous to a provoking change. This is done for efficiency so
     * that multiple changes trigger only a single render. The render method
     * should be called if, for example, template rendering is required to
     * validate application state.
     */
    render: function() {
      this._flushTemplates();
    },

    _render: function() {
      if (this.if) {
        if (!this.ctor) {
          this.templatize(this);
        }
        this._ensureInstance();
        this._showHideChildren();
      } else if (this.restamp) {
        this._teardownInstance();
      }
      if (!this.restamp && this._instance) {
        this._showHideChildren();
      }
      if (this.if != this._lastIf) {
        this.fire('dom-change');
        this._lastIf = this.if;
      }
    },

    _ensureInstance: function() {
      var parentNode = Polymer.dom(this).parentNode;
      // Guard against element being detached while render was queued
      if (parentNode) {
        var parent = Polymer.dom(parentNode);
        if (!this._instance) {
          this._instance = this.stamp();
          var root = this._instance.root;
          parent.insertBefore(root, this);
        } else {
          var c$ = this._instance._children;
          if (c$ && c$.length) {
            // Detect case where dom-if was re-attached in new position
            var lastChild = Polymer.dom(this).previousSibling;
            if (lastChild !== c$[c$.length-1]) {
              for (var i=0, n; (i<c$.length) && (n=c$[i]); i++) {
                parent.insertBefore(n, this);
              }
            }
          }
        }
      }
    },

    _teardownInstance: function() {
      if (this._instance) {
        var c$ = this._instance._children;
        if (c$ && c$.length) {
          // use first child parent, for case when dom-if may have been detached
          var parent = Polymer.dom(Polymer.dom(c$[0]).parentNode);
          for (var i=0, n; (i<c$.length) && (n=c$[i]); i++) {
            parent.removeChild(n);
          }
        }
        this._instance = null;
      }
    },

    _showHideChildren: function() {
      var hidden = this.__hideTemplateChildren__ || !this.if;
      if (this._instance) {
        this._instance._showHideChildren(hidden);
      }
    },

    // Implements extension point from Templatizer mixin
    // Called as side-effect of a host property change, responsible for
    // notifying parent.<prop> path change on instance
    _forwardParentProp: function(prop, value) {
      if (this._instance) {
        this._instance[prop] = value;
      }
    },

    // Implements extension point from Templatizer
    // Called as side-effect of a host path change, responsible for
    // notifying parent.<path> path change on each row
    _forwardParentPath: function(path, value) {
      if (this._instance) {
        this._instance._notifyPath(path, value, true);
      }
    }

  });
Polymer({

    /**
     * Fired whenever DOM is stamped by this template (rendering
     * will be deferred until all HTML imports have resolved).
     *
     * @event dom-change
     */

    is: 'dom-bind',

    extends: 'template',
    _template: null,

    created: function() {
      // Ensure dom-bind doesn't stamp until all possible dependencies
      // have resolved
      var self = this;
      Polymer.RenderStatus.whenReady(function() {
        if (document.readyState == 'loading') {
          document.addEventListener('DOMContentLoaded', function() {
            self._markImportsReady(); 
          });
        } else {  
          self._markImportsReady();
        }
      });
    },

    _ensureReady: function() {
      if (!this._readied) {
        this._readySelf();
      }
    },

    _markImportsReady: function() {
      this._importsReady = true;
      this._ensureReady();
    },

    _registerFeatures: function() {
      this._prepConstructor();
    },

    _insertChildren: function() {
      var parentDom = Polymer.dom(Polymer.dom(this).parentNode);
      parentDom.insertBefore(this.root, this);
    },

    _removeChildren: function() {
      if (this._children) {
        for (var i=0; i<this._children.length; i++) {
          this.root.appendChild(this._children[i]);
        }
      }
    },

    _initFeatures: function() {
      // defer _initFeatures and stamping until after attached, to support
      // document.createElement('template', 'dom-bind') use case,
      // where template content is filled in after creation
    },

    // avoid scoping elements as we expect dom-bind output to be in the main
    // document
    _scopeElementClass: function(element, selector) {
      if (this.dataHost) {
        return this.dataHost._scopeElementClass(element, selector);
      } else {
        return selector;
      }
    },

    _prepConfigure: function() {
      var config = {};
      for (var prop in this._propertyEffects) {
        config[prop] = this[prop];
      }
      // Pass values set before attached as initialConfig to _setupConfigure
      var setupConfigure = this._setupConfigure;
      this._setupConfigure = function() {
        setupConfigure.call(this, config);
      };
    },

    attached: function() {
      if (this._importsReady) {
        this.render();
      }
    },

    detached: function() {
      this._removeChildren();
    },

    /**
     * Forces the element to render its content. This is typically only
     * necessary to call if HTMLImports with the async attribute are used.
     */
    render: function() {
      this._ensureReady();
      if (!this._children) {
        this._template = this;
        this._prepAnnotations();
        this._prepEffects();
        this._prepBehaviors();
        this._prepConfigure();
        this._prepBindings();
        this._prepPropertyInfo();
        Polymer.Base._initFeatures.call(this);
        this._children = Polymer.TreeApi.arrayCopyChildNodes(this.root);
      }
      this._insertChildren();
      this.fire('dom-change');
    }

  });
(function() {

    // monostate data
    var metaDatas = {};
    var metaArrays = {};
    var singleton = null;

    Polymer.IronMeta = Polymer({

      is: 'iron-meta',

      properties: {

        /**
         * The type of meta-data.  All meta-data of the same type is stored
         * together.
         */
        type: {
          type: String,
          value: 'default',
          observer: '_typeChanged'
        },

        /**
         * The key used to store `value` under the `type` namespace.
         */
        key: {
          type: String,
          observer: '_keyChanged'
        },

        /**
         * The meta-data to store or retrieve.
         */
        value: {
          type: Object,
          notify: true,
          observer: '_valueChanged'
        },

        /**
         * If true, `value` is set to the iron-meta instance itself.
         */
         self: {
          type: Boolean,
          observer: '_selfChanged'
        },

        /**
         * Array of all meta-data values for the given type.
         */
        list: {
          type: Array,
          notify: true
        }

      },

      hostAttributes: {
        hidden: true
      },

      /**
       * Only runs if someone invokes the factory/constructor directly
       * e.g. `new Polymer.IronMeta()`
       *
       * @param {{type: (string|undefined), key: (string|undefined), value}=} config
       */
      factoryImpl: function(config) {
        if (config) {
          for (var n in config) {
            switch(n) {
              case 'type':
              case 'key':
              case 'value':
                this[n] = config[n];
                break;
            }
          }
        }
      },

      created: function() {
        // TODO(sjmiles): good for debugging?
        this._metaDatas = metaDatas;
        this._metaArrays = metaArrays;
      },

      _keyChanged: function(key, old) {
        this._resetRegistration(old);
      },

      _valueChanged: function(value) {
        this._resetRegistration(this.key);
      },

      _selfChanged: function(self) {
        if (self) {
          this.value = this;
        }
      },

      _typeChanged: function(type) {
        this._unregisterKey(this.key);
        if (!metaDatas[type]) {
          metaDatas[type] = {};
        }
        this._metaData = metaDatas[type];
        if (!metaArrays[type]) {
          metaArrays[type] = [];
        }
        this.list = metaArrays[type];
        this._registerKeyValue(this.key, this.value);
      },

      /**
       * Retrieves meta data value by key.
       *
       * @method byKey
       * @param {string} key The key of the meta-data to be returned.
       * @return {*}
       */
      byKey: function(key) {
        return this._metaData && this._metaData[key];
      },

      _resetRegistration: function(oldKey) {
        this._unregisterKey(oldKey);
        this._registerKeyValue(this.key, this.value);
      },

      _unregisterKey: function(key) {
        this._unregister(key, this._metaData, this.list);
      },

      _registerKeyValue: function(key, value) {
        this._register(key, value, this._metaData, this.list);
      },

      _register: function(key, value, data, list) {
        if (key && data && value !== undefined) {
          data[key] = value;
          list.push(value);
        }
      },

      _unregister: function(key, data, list) {
        if (key && data) {
          if (key in data) {
            var value = data[key];
            delete data[key];
            this.arrayDelete(list, value);
          }
        }
      }

    });

    Polymer.IronMeta.getIronMeta = function getIronMeta() {
       if (singleton === null) {
         singleton = new Polymer.IronMeta();
       }
       return singleton;
     };

    /**
    `iron-meta-query` can be used to access infomation stored in `iron-meta`.

    Examples:

    If I create an instance like this:

        <iron-meta key="info" value="foo/bar"></iron-meta>

    Note that value="foo/bar" is the metadata I've defined. I could define more
    attributes or use child nodes to define additional metadata.

    Now I can access that element (and it's metadata) from any `iron-meta-query` instance:

         var value = new Polymer.IronMetaQuery({key: 'info'}).value;

    @group Polymer Iron Elements
    @element iron-meta-query
    */
    Polymer.IronMetaQuery = Polymer({

      is: 'iron-meta-query',

      properties: {

        /**
         * The type of meta-data.  All meta-data of the same type is stored
         * together.
         */
        type: {
          type: String,
          value: 'default',
          observer: '_typeChanged'
        },

        /**
         * Specifies a key to use for retrieving `value` from the `type`
         * namespace.
         */
        key: {
          type: String,
          observer: '_keyChanged'
        },

        /**
         * The meta-data to store or retrieve.
         */
        value: {
          type: Object,
          notify: true,
          readOnly: true
        },

        /**
         * Array of all meta-data values for the given type.
         */
        list: {
          type: Array,
          notify: true
        }

      },

      /**
       * Actually a factory method, not a true constructor. Only runs if
       * someone invokes it directly (via `new Polymer.IronMeta()`);
       *
       * @param {{type: (string|undefined), key: (string|undefined)}=} config
       */
      factoryImpl: function(config) {
        if (config) {
          for (var n in config) {
            switch(n) {
              case 'type':
              case 'key':
                this[n] = config[n];
                break;
            }
          }
        }
      },

      created: function() {
        // TODO(sjmiles): good for debugging?
        this._metaDatas = metaDatas;
        this._metaArrays = metaArrays;
      },

      _keyChanged: function(key) {
        this._setValue(this._metaData && this._metaData[key]);
      },

      _typeChanged: function(type) {
        this._metaData = metaDatas[type];
        this.list = metaArrays[type];
        if (this.key) {
          this._keyChanged(this.key);
        }
      },

      /**
       * Retrieves meta data value by key.
       * @param {string} key The key of the meta-data to be returned.
       * @return {*}
       */
      byKey: function(key) {
        return this._metaData && this._metaData[key];
      }

    });

  })();
Polymer({

      is: 'iron-icon',

      properties: {

        /**
         * The name of the icon to use. The name should be of the form:
         * `iconset_name:icon_name`.
         */
        icon: {
          type: String
        },

        /**
         * The name of the theme to used, if one is specified by the
         * iconset.
         */
        theme: {
          type: String
        },

        /**
         * If using iron-icon without an iconset, you can set the src to be
         * the URL of an individual icon image file. Note that this will take
         * precedence over a given icon attribute.
         */
        src: {
          type: String
        },

        /**
         * @type {!Polymer.IronMeta}
         */
        _meta: {
          value: Polymer.Base.create('iron-meta', {type: 'iconset'})
        }

      },

      observers: [
        '_updateIcon(_meta, isAttached)',
        '_updateIcon(theme, isAttached)',
        '_srcChanged(src, isAttached)',
        '_iconChanged(icon, isAttached)'
      ],

      _DEFAULT_ICONSET: 'icons',

      _iconChanged: function(icon) {
        var parts = (icon || '').split(':');
        this._iconName = parts.pop();
        this._iconsetName = parts.pop() || this._DEFAULT_ICONSET;
        this._updateIcon();
      },

      _srcChanged: function(src) {
        this._updateIcon();
      },

      _usesIconset: function() {
        return this.icon || !this.src;
      },

      /** @suppress {visibility} */
      _updateIcon: function() {
        if (this._usesIconset()) {
          if (this._img && this._img.parentNode) {
            Polymer.dom(this.root).removeChild(this._img);
          }
          if (this._iconName === "") {
            if (this._iconset) {
              this._iconset.removeIcon(this);
            }
          } else if (this._iconsetName && this._meta) {
            this._iconset = /** @type {?Polymer.Iconset} */ (
              this._meta.byKey(this._iconsetName));
            if (this._iconset) {
              this._iconset.applyIcon(this, this._iconName, this.theme);
              this.unlisten(window, 'iron-iconset-added', '_updateIcon');
            } else {
              this.listen(window, 'iron-iconset-added', '_updateIcon');
            }
          }
        } else {
          if (this._iconset) {
            this._iconset.removeIcon(this);
          }
          if (!this._img) {
            this._img = document.createElement('img');
            this._img.style.width = '100%';
            this._img.style.height = '100%';
            this._img.draggable = false;
          }
          this._img.src = this.src;
          Polymer.dom(this.root).appendChild(this._img);
        }
      }

    });
/**
   * The `iron-iconset-svg` element allows users to define their own icon sets
   * that contain svg icons. The svg icon elements should be children of the
   * `iron-iconset-svg` element. Multiple icons should be given distinct id's.
   *
   * Using svg elements to create icons has a few advantages over traditional
   * bitmap graphics like jpg or png. Icons that use svg are vector based so
   * they are resolution independent and should look good on any device. They
   * are stylable via css. Icons can be themed, colorized, and even animated.
   *
   * Example:
   *
   *     <iron-iconset-svg name="my-svg-icons" size="24">
   *       <svg>
   *         <defs>
   *           <g id="shape">
   *             <rect x="12" y="0" width="12" height="24" />
   *             <circle cx="12" cy="12" r="12" />
   *           </g>
   *         </defs>
   *       </svg>
   *     </iron-iconset-svg>
   *
   * This will automatically register the icon set "my-svg-icons" to the iconset
   * database.  To use these icons from within another element, make a
   * `iron-iconset` element and call the `byId` method
   * to retrieve a given iconset. To apply a particular icon inside an
   * element use the `applyIcon` method. For example:
   *
   *     iconset.applyIcon(iconNode, 'car');
   *
   * @element iron-iconset-svg
   * @demo demo/index.html
   * @implements {Polymer.Iconset}
   */
  Polymer({
    is: 'iron-iconset-svg',

    properties: {

      /**
       * The name of the iconset.
       */
      name: {
        type: String,
        observer: '_nameChanged'
      },

      /**
       * The size of an individual icon. Note that icons must be square.
       */
      size: {
        type: Number,
        value: 24
      },

      /**
       * Set to true to enable mirroring of icons where specified when they are
       * stamped. Icons that should be mirrored should be decorated with a
       * `mirror-in-rtl` attribute.
       *
       * NOTE: For performance reasons, direction will be resolved once per
       * document per iconset, so moving icons in and out of RTL subtrees will
       * not cause their mirrored state to change.
       */
      rtlMirroring: {
        type: Boolean,
        value: false
      }
    },

    attached: function() {
      this.style.display = 'none';
    },

    /**
     * Construct an array of all icon names in this iconset.
     *
     * @return {!Array} Array of icon names.
     */
    getIconNames: function() {
      this._icons = this._createIconMap();
      return Object.keys(this._icons).map(function(n) {
        return this.name + ':' + n;
      }, this);
    },

    /**
     * Applies an icon to the given element.
     *
     * An svg icon is prepended to the element's shadowRoot if it exists,
     * otherwise to the element itself.
     *
     * If RTL mirroring is enabled, and the icon is marked to be mirrored in
     * RTL, the element will be tested (once and only once ever for each
     * iconset) to determine the direction of the subtree the element is in.
     * This direction will apply to all future icon applications, although only
     * icons marked to be mirrored will be affected.
     *
     * @method applyIcon
     * @param {Element} element Element to which the icon is applied.
     * @param {string} iconName Name of the icon to apply.
     * @return {?Element} The svg element which renders the icon.
     */
    applyIcon: function(element, iconName) {
      // insert svg element into shadow root, if it exists
      element = element.root || element;
      // Remove old svg element
      this.removeIcon(element);
      // install new svg element
      var svg = this._cloneIcon(iconName,
          this.rtlMirroring && this._targetIsRTL(element));
      if (svg) {
        var pde = Polymer.dom(element);
        pde.insertBefore(svg, pde.childNodes[0]);
        return element._svgIcon = svg;
      }
      return null;
    },

    /**
     * Remove an icon from the given element by undoing the changes effected
     * by `applyIcon`.
     *
     * @param {Element} element The element from which the icon is removed.
     */
    removeIcon: function(element) {
      // Remove old svg element
      element = element.root || element;
      if (element._svgIcon) {
        Polymer.dom(element).removeChild(element._svgIcon);
        element._svgIcon = null;
      }
    },

    /**
     * Measures and memoizes the direction of the element. Note that this
     * measurement is only done once and the result is memoized for future
     * invocations.
     */
    _targetIsRTL: function(target) {
      if (this.__targetIsRTL == null) {
        if (target && target.nodeType !== Node.ELEMENT_NODE) {
          target = target.host;
        }

        this.__targetIsRTL = target &&
            window.getComputedStyle(target)['direction'] === 'rtl';
      }

      return this.__targetIsRTL;
    },

    /**
     *
     * When name is changed, register iconset metadata
     *
     */
    _nameChanged: function() {
      new Polymer.IronMeta({type: 'iconset', key: this.name, value: this});
      this.async(function() {
        this.fire('iron-iconset-added', this, {node: window});
      });
    },

    /**
     * Create a map of child SVG elements by id.
     *
     * @return {!Object} Map of id's to SVG elements.
     */
    _createIconMap: function() {
      // Objects chained to Object.prototype (`{}`) have members. Specifically,
      // on FF there is a `watch` method that confuses the icon map, so we
      // need to use a null-based object here.
      var icons = Object.create(null);
      Polymer.dom(this).querySelectorAll('[id]')
        .forEach(function(icon) {
          icons[icon.id] = icon;
        });
      return icons;
    },

    /**
     * Produce installable clone of the SVG element matching `id` in this
     * iconset, or `undefined` if there is no matching element.
     *
     * @return {Element} Returns an installable clone of the SVG element
     * matching `id`.
     */
    _cloneIcon: function(id, mirrorAllowed) {
      // create the icon map on-demand, since the iconset itself has no discrete
      // signal to know when it's children are fully parsed
      this._icons = this._icons || this._createIconMap();
      return this._prepareSvgClone(this._icons[id], this.size, mirrorAllowed);
    },

    /**
     * @param {Element} sourceSvg
     * @param {number} size
     * @param {Boolean} mirrorAllowed
     * @return {Element}
     */
    _prepareSvgClone: function(sourceSvg, size, mirrorAllowed) {
      if (sourceSvg) {
        var content = sourceSvg.cloneNode(true),
            svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg'),
            viewBox = content.getAttribute('viewBox') || '0 0 ' + size + ' ' + size,
            cssText = 'pointer-events: none; display: block; width: 100%; height: 100%;';

        if (mirrorAllowed && content.hasAttribute('mirror-in-rtl')) {
          cssText += '-webkit-transform:scale(-1,1);transform:scale(-1,1);';
        }

        svg.setAttribute('viewBox', viewBox);
        svg.setAttribute('preserveAspectRatio', 'xMidYMid meet');
        // TODO(dfreedm): `pointer-events: none` works around https://crbug.com/370136
        // TODO(sjmiles): inline style may not be ideal, but avoids requiring a shadow-root
        svg.style.cssText = cssText;
        svg.appendChild(content).removeAttribute('id');
        return svg;
      }
      return null;
    }

  });
(function() {
    'use strict';

    /**
     * Chrome uses an older version of DOM Level 3 Keyboard Events
     *
     * Most keys are labeled as text, but some are Unicode codepoints.
     * Values taken from: http://www.w3.org/TR/2007/WD-DOM-Level-3-Events-20071221/keyset.html#KeySet-Set
     */
    var KEY_IDENTIFIER = {
      'U+0008': 'backspace',
      'U+0009': 'tab',
      'U+001B': 'esc',
      'U+0020': 'space',
      'U+007F': 'del'
    };

    /**
     * Special table for KeyboardEvent.keyCode.
     * KeyboardEvent.keyIdentifier is better, and KeyBoardEvent.key is even better
     * than that.
     *
     * Values from: https://developer.mozilla.org/en-US/docs/Web/API/KeyboardEvent.keyCode#Value_of_keyCode
     */
    var KEY_CODE = {
      8: 'backspace',
      9: 'tab',
      13: 'enter',
      27: 'esc',
      33: 'pageup',
      34: 'pagedown',
      35: 'end',
      36: 'home',
      32: 'space',
      37: 'left',
      38: 'up',
      39: 'right',
      40: 'down',
      46: 'del',
      106: '*'
    };

    /**
     * MODIFIER_KEYS maps the short name for modifier keys used in a key
     * combo string to the property name that references those same keys
     * in a KeyboardEvent instance.
     */
    var MODIFIER_KEYS = {
      'shift': 'shiftKey',
      'ctrl': 'ctrlKey',
      'alt': 'altKey',
      'meta': 'metaKey'
    };

    /**
     * KeyboardEvent.key is mostly represented by printable character made by
     * the keyboard, with unprintable keys labeled nicely.
     *
     * However, on OS X, Alt+char can make a Unicode character that follows an
     * Apple-specific mapping. In this case, we fall back to .keyCode.
     */
    var KEY_CHAR = /[a-z0-9*]/;

    /**
     * Matches a keyIdentifier string.
     */
    var IDENT_CHAR = /U\+/;

    /**
     * Matches arrow keys in Gecko 27.0+
     */
    var ARROW_KEY = /^arrow/;

    /**
     * Matches space keys everywhere (notably including IE10's exceptional name
     * `spacebar`).
     */
    var SPACE_KEY = /^space(bar)?/;

    /**
     * Matches ESC key.
     *
     * Value from: http://w3c.github.io/uievents-key/#key-Escape
     */
    var ESC_KEY = /^escape$/;

    /**
     * Transforms the key.
     * @param {string} key The KeyBoardEvent.key
     * @param {Boolean} [noSpecialChars] Limits the transformation to
     * alpha-numeric characters.
     */
    function transformKey(key, noSpecialChars) {
      var validKey = '';
      if (key) {
        var lKey = key.toLowerCase();
        if (lKey === ' ' || SPACE_KEY.test(lKey)) {
          validKey = 'space';
        } else if (ESC_KEY.test(lKey)) {
          validKey = 'esc';
        } else if (lKey.length == 1) {
          if (!noSpecialChars || KEY_CHAR.test(lKey)) {
            validKey = lKey;
          }
        } else if (ARROW_KEY.test(lKey)) {
          validKey = lKey.replace('arrow', '');
        } else if (lKey == 'multiply') {
          // numpad '*' can map to Multiply on IE/Windows
          validKey = '*';
        } else {
          validKey = lKey;
        }
      }
      return validKey;
    }

    function transformKeyIdentifier(keyIdent) {
      var validKey = '';
      if (keyIdent) {
        if (keyIdent in KEY_IDENTIFIER) {
          validKey = KEY_IDENTIFIER[keyIdent];
        } else if (IDENT_CHAR.test(keyIdent)) {
          keyIdent = parseInt(keyIdent.replace('U+', '0x'), 16);
          validKey = String.fromCharCode(keyIdent).toLowerCase();
        } else {
          validKey = keyIdent.toLowerCase();
        }
      }
      return validKey;
    }

    function transformKeyCode(keyCode) {
      var validKey = '';
      if (Number(keyCode)) {
        if (keyCode >= 65 && keyCode <= 90) {
          // ascii a-z
          // lowercase is 32 offset from uppercase
          validKey = String.fromCharCode(32 + keyCode);
        } else if (keyCode >= 112 && keyCode <= 123) {
          // function keys f1-f12
          validKey = 'f' + (keyCode - 112);
        } else if (keyCode >= 48 && keyCode <= 57) {
          // top 0-9 keys
          validKey = String(keyCode - 48);
        } else if (keyCode >= 96 && keyCode <= 105) {
          // num pad 0-9
          validKey = String(keyCode - 96);
        } else {
          validKey = KEY_CODE[keyCode];
        }
      }
      return validKey;
    }

    /**
      * Calculates the normalized key for a KeyboardEvent.
      * @param {KeyboardEvent} keyEvent
      * @param {Boolean} [noSpecialChars] Set to true to limit keyEvent.key
      * transformation to alpha-numeric chars. This is useful with key
      * combinations like shift + 2, which on FF for MacOS produces
      * keyEvent.key = @
      * To get 2 returned, set noSpecialChars = true
      * To get @ returned, set noSpecialChars = false
     */
    function normalizedKeyForEvent(keyEvent, noSpecialChars) {
      // Fall back from .key, to .detail.key for artifical keyboard events,
      // and then to deprecated .keyIdentifier and .keyCode.
      if (keyEvent.key) {
        return transformKey(keyEvent.key, noSpecialChars);
      }
      if (keyEvent.detail && keyEvent.detail.key) {
        return transformKey(keyEvent.detail.key, noSpecialChars);
      }
      return transformKeyIdentifier(keyEvent.keyIdentifier) ||
        transformKeyCode(keyEvent.keyCode) || '';
    }

    function keyComboMatchesEvent(keyCombo, event) {
      // For combos with modifiers we support only alpha-numeric keys
      var keyEvent = normalizedKeyForEvent(event, keyCombo.hasModifiers);
      return keyEvent === keyCombo.key &&
        (!keyCombo.hasModifiers || (
          !!event.shiftKey === !!keyCombo.shiftKey &&
          !!event.ctrlKey === !!keyCombo.ctrlKey &&
          !!event.altKey === !!keyCombo.altKey &&
          !!event.metaKey === !!keyCombo.metaKey)
        );
    }

    function parseKeyComboString(keyComboString) {
      if (keyComboString.length === 1) {
        return {
          combo: keyComboString,
          key: keyComboString,
          event: 'keydown'
        };
      }
      return keyComboString.split('+').reduce(function(parsedKeyCombo, keyComboPart) {
        var eventParts = keyComboPart.split(':');
        var keyName = eventParts[0];
        var event = eventParts[1];

        if (keyName in MODIFIER_KEYS) {
          parsedKeyCombo[MODIFIER_KEYS[keyName]] = true;
          parsedKeyCombo.hasModifiers = true;
        } else {
          parsedKeyCombo.key = keyName;
          parsedKeyCombo.event = event || 'keydown';
        }

        return parsedKeyCombo;
      }, {
        combo: keyComboString.split(':').shift()
      });
    }

    function parseEventString(eventString) {
      return eventString.trim().split(' ').map(function(keyComboString) {
        return parseKeyComboString(keyComboString);
      });
    }

    /**
     * `Polymer.IronA11yKeysBehavior` provides a normalized interface for processing
     * keyboard commands that pertain to [WAI-ARIA best practices](http://www.w3.org/TR/wai-aria-practices/#kbd_general_binding).
     * The element takes care of browser differences with respect to Keyboard events
     * and uses an expressive syntax to filter key presses.
     *
     * Use the `keyBindings` prototype property to express what combination of keys
     * will trigger the callback. A key binding has the format
     * `"KEY+MODIFIER:EVENT": "callback"` (`"KEY": "callback"` or
     * `"KEY:EVENT": "callback"` are valid as well). Some examples:
     *
     *      keyBindings: {
     *        'space': '_onKeydown', // same as 'space:keydown'
     *        'shift+tab': '_onKeydown',
     *        'enter:keypress': '_onKeypress',
     *        'esc:keyup': '_onKeyup'
     *      }
     *
     * The callback will receive with an event containing the following information in `event.detail`:
     *
     *      _onKeydown: function(event) {
     *        console.log(event.detail.combo); // KEY+MODIFIER, e.g. "shift+tab"
     *        console.log(event.detail.key); // KEY only, e.g. "tab"
     *        console.log(event.detail.event); // EVENT, e.g. "keydown"
     *        console.log(event.detail.keyboardEvent); // the original KeyboardEvent
     *      }
     *
     * Use the `keyEventTarget` attribute to set up event handlers on a specific
     * node.
     *
     * See the [demo source code](https://github.com/PolymerElements/iron-a11y-keys-behavior/blob/master/demo/x-key-aware.html)
     * for an example.
     *
     * @demo demo/index.html
     * @polymerBehavior
     */
    Polymer.IronA11yKeysBehavior = {
      properties: {
        /**
         * The EventTarget that will be firing relevant KeyboardEvents. Set it to
         * `null` to disable the listeners.
         * @type {?EventTarget}
         */
        keyEventTarget: {
          type: Object,
          value: function() {
            return this;
          }
        },

        /**
         * If true, this property will cause the implementing element to
         * automatically stop propagation on any handled KeyboardEvents.
         */
        stopKeyboardEventPropagation: {
          type: Boolean,
          value: false
        },

        _boundKeyHandlers: {
          type: Array,
          value: function() {
            return [];
          }
        },

        // We use this due to a limitation in IE10 where instances will have
        // own properties of everything on the "prototype".
        _imperativeKeyBindings: {
          type: Object,
          value: function() {
            return {};
          }
        }
      },

      observers: [
        '_resetKeyEventListeners(keyEventTarget, _boundKeyHandlers)'
      ],


      /**
       * To be used to express what combination of keys  will trigger the relative
       * callback. e.g. `keyBindings: { 'esc': '_onEscPressed'}`
       * @type {!Object}
       */
      keyBindings: {},

      registered: function() {
        this._prepKeyBindings();
      },

      attached: function() {
        this._listenKeyEventListeners();
      },

      detached: function() {
        this._unlistenKeyEventListeners();
      },

      /**
       * Can be used to imperatively add a key binding to the implementing
       * element. This is the imperative equivalent of declaring a keybinding
       * in the `keyBindings` prototype property.
       */
      addOwnKeyBinding: function(eventString, handlerName) {
        this._imperativeKeyBindings[eventString] = handlerName;
        this._prepKeyBindings();
        this._resetKeyEventListeners();
      },

      /**
       * When called, will remove all imperatively-added key bindings.
       */
      removeOwnKeyBindings: function() {
        this._imperativeKeyBindings = {};
        this._prepKeyBindings();
        this._resetKeyEventListeners();
      },

      /**
       * Returns true if a keyboard event matches `eventString`.
       *
       * @param {KeyboardEvent} event
       * @param {string} eventString
       * @return {boolean}
       */
      keyboardEventMatchesKeys: function(event, eventString) {
        var keyCombos = parseEventString(eventString);
        for (var i = 0; i < keyCombos.length; ++i) {
          if (keyComboMatchesEvent(keyCombos[i], event)) {
            return true;
          }
        }
        return false;
      },

      _collectKeyBindings: function() {
        var keyBindings = this.behaviors.map(function(behavior) {
          return behavior.keyBindings;
        });

        if (keyBindings.indexOf(this.keyBindings) === -1) {
          keyBindings.push(this.keyBindings);
        }

        return keyBindings;
      },

      _prepKeyBindings: function() {
        this._keyBindings = {};

        this._collectKeyBindings().forEach(function(keyBindings) {
          for (var eventString in keyBindings) {
            this._addKeyBinding(eventString, keyBindings[eventString]);
          }
        }, this);

        for (var eventString in this._imperativeKeyBindings) {
          this._addKeyBinding(eventString, this._imperativeKeyBindings[eventString]);
        }

        // Give precedence to combos with modifiers to be checked first.
        for (var eventName in this._keyBindings) {
          this._keyBindings[eventName].sort(function (kb1, kb2) {
            var b1 = kb1[0].hasModifiers;
            var b2 = kb2[0].hasModifiers;
            return (b1 === b2) ? 0 : b1 ? -1 : 1;
          })
        }
      },

      _addKeyBinding: function(eventString, handlerName) {
        parseEventString(eventString).forEach(function(keyCombo) {
          this._keyBindings[keyCombo.event] =
            this._keyBindings[keyCombo.event] || [];

          this._keyBindings[keyCombo.event].push([
            keyCombo,
            handlerName
          ]);
        }, this);
      },

      _resetKeyEventListeners: function() {
        this._unlistenKeyEventListeners();

        if (this.isAttached) {
          this._listenKeyEventListeners();
        }
      },

      _listenKeyEventListeners: function() {
        if (!this.keyEventTarget) {
          return;
        }
        Object.keys(this._keyBindings).forEach(function(eventName) {
          var keyBindings = this._keyBindings[eventName];
          var boundKeyHandler = this._onKeyBindingEvent.bind(this, keyBindings);

          this._boundKeyHandlers.push([this.keyEventTarget, eventName, boundKeyHandler]);

          this.keyEventTarget.addEventListener(eventName, boundKeyHandler);
        }, this);
      },

      _unlistenKeyEventListeners: function() {
        var keyHandlerTuple;
        var keyEventTarget;
        var eventName;
        var boundKeyHandler;

        while (this._boundKeyHandlers.length) {
          // My kingdom for block-scope binding and destructuring assignment..
          keyHandlerTuple = this._boundKeyHandlers.pop();
          keyEventTarget = keyHandlerTuple[0];
          eventName = keyHandlerTuple[1];
          boundKeyHandler = keyHandlerTuple[2];

          keyEventTarget.removeEventListener(eventName, boundKeyHandler);
        }
      },

      _onKeyBindingEvent: function(keyBindings, event) {
        if (this.stopKeyboardEventPropagation) {
          event.stopPropagation();
        }

        // if event has been already prevented, don't do anything
        if (event.defaultPrevented) {
          return;
        }

        for (var i = 0; i < keyBindings.length; i++) {
          var keyCombo = keyBindings[i][0];
          var handlerName = keyBindings[i][1];
          if (keyComboMatchesEvent(keyCombo, event)) {
            this._triggerKeyHandler(keyCombo, handlerName, event);
            // exit the loop if eventDefault was prevented
            if (event.defaultPrevented) {
              return;
            }
          }
        }
      },

      _triggerKeyHandler: function(keyCombo, handlerName, keyboardEvent) {
        var detail = Object.create(keyCombo);
        detail.keyboardEvent = keyboardEvent;
        var event = new CustomEvent(keyCombo.event, {
          detail: detail,
          cancelable: true
        });
        this[handlerName].call(this, event);
        if (event.defaultPrevented) {
          keyboardEvent.preventDefault();
        }
      }
    };
  })();
/**
   * @demo demo/index.html
   * @polymerBehavior
   */
  Polymer.IronControlState = {

    properties: {

      /**
       * If true, the element currently has focus.
       */
      focused: {
        type: Boolean,
        value: false,
        notify: true,
        readOnly: true,
        reflectToAttribute: true
      },

      /**
       * If true, the user cannot interact with this element.
       */
      disabled: {
        type: Boolean,
        value: false,
        notify: true,
        observer: '_disabledChanged',
        reflectToAttribute: true
      },

      _oldTabIndex: {
        type: Number
      },

      _boundFocusBlurHandler: {
        type: Function,
        value: function() {
          return this._focusBlurHandler.bind(this);
        }
      }

    },

    observers: [
      '_changedControlState(focused, disabled)'
    ],

    ready: function() {
      this.addEventListener('focus', this._boundFocusBlurHandler, true);
      this.addEventListener('blur', this._boundFocusBlurHandler, true);
    },

    _focusBlurHandler: function(event) {
      // NOTE(cdata):  if we are in ShadowDOM land, `event.target` will
      // eventually become `this` due to retargeting; if we are not in
      // ShadowDOM land, `event.target` will eventually become `this` due
      // to the second conditional which fires a synthetic event (that is also
      // handled). In either case, we can disregard `event.path`.

      if (event.target === this) {
        this._setFocused(event.type === 'focus');
      } else if (!this.shadowRoot) {
        var target = /** @type {Node} */(Polymer.dom(event).localTarget);
        if (!this.isLightDescendant(target)) {
          this.fire(event.type, {sourceEvent: event}, {
            node: this,
            bubbles: event.bubbles,
            cancelable: event.cancelable
          });
        }
      }
    },

    _disabledChanged: function(disabled, old) {
      this.setAttribute('aria-disabled', disabled ? 'true' : 'false');
      this.style.pointerEvents = disabled ? 'none' : '';
      if (disabled) {
        this._oldTabIndex = this.tabIndex;
        this._setFocused(false);
        this.tabIndex = -1;
        this.blur();
      } else if (this._oldTabIndex !== undefined) {
        this.tabIndex = this._oldTabIndex;
      }
    },

    _changedControlState: function() {
      // _controlStateChanged is abstract, follow-on behaviors may implement it
      if (this._controlStateChanged) {
        this._controlStateChanged();
      }
    }

  };
/**
   * @demo demo/index.html
   * @polymerBehavior Polymer.IronButtonState
   */
  Polymer.IronButtonStateImpl = {

    properties: {

      /**
       * If true, the user is currently holding down the button.
       */
      pressed: {
        type: Boolean,
        readOnly: true,
        value: false,
        reflectToAttribute: true,
        observer: '_pressedChanged'
      },

      /**
       * If true, the button toggles the active state with each tap or press
       * of the spacebar.
       */
      toggles: {
        type: Boolean,
        value: false,
        reflectToAttribute: true
      },

      /**
       * If true, the button is a toggle and is currently in the active state.
       */
      active: {
        type: Boolean,
        value: false,
        notify: true,
        reflectToAttribute: true
      },

      /**
       * True if the element is currently being pressed by a "pointer," which
       * is loosely defined as mouse or touch input (but specifically excluding
       * keyboard input).
       */
      pointerDown: {
        type: Boolean,
        readOnly: true,
        value: false
      },

      /**
       * True if the input device that caused the element to receive focus
       * was a keyboard.
       */
      receivedFocusFromKeyboard: {
        type: Boolean,
        readOnly: true
      },

      /**
       * The aria attribute to be set if the button is a toggle and in the
       * active state.
       */
      ariaActiveAttribute: {
        type: String,
        value: 'aria-pressed',
        observer: '_ariaActiveAttributeChanged'
      }
    },

    listeners: {
      down: '_downHandler',
      up: '_upHandler',
      tap: '_tapHandler'
    },

    observers: [
      '_detectKeyboardFocus(focused)',
      '_activeChanged(active, ariaActiveAttribute)'
    ],

    keyBindings: {
      'enter:keydown': '_asyncClick',
      'space:keydown': '_spaceKeyDownHandler',
      'space:keyup': '_spaceKeyUpHandler',
    },

    _mouseEventRe: /^mouse/,

    _tapHandler: function() {
      if (this.toggles) {
       // a tap is needed to toggle the active state
        this._userActivate(!this.active);
      } else {
        this.active = false;
      }
    },

    _detectKeyboardFocus: function(focused) {
      this._setReceivedFocusFromKeyboard(!this.pointerDown && focused);
    },

    // to emulate native checkbox, (de-)activations from a user interaction fire
    // 'change' events
    _userActivate: function(active) {
      if (this.active !== active) {
        this.active = active;
        this.fire('change');
      }
    },

    _downHandler: function(event) {
      this._setPointerDown(true);
      this._setPressed(true);
      this._setReceivedFocusFromKeyboard(false);
    },

    _upHandler: function() {
      this._setPointerDown(false);
      this._setPressed(false);
    },

    /**
     * @param {!KeyboardEvent} event .
     */
    _spaceKeyDownHandler: function(event) {
      var keyboardEvent = event.detail.keyboardEvent;
      var target = Polymer.dom(keyboardEvent).localTarget;

      // Ignore the event if this is coming from a focused light child, since that
      // element will deal with it.
      if (this.isLightDescendant(/** @type {Node} */(target)))
        return;

      keyboardEvent.preventDefault();
      keyboardEvent.stopImmediatePropagation();
      this._setPressed(true);
    },

    /**
     * @param {!KeyboardEvent} event .
     */
    _spaceKeyUpHandler: function(event) {
      var keyboardEvent = event.detail.keyboardEvent;
      var target = Polymer.dom(keyboardEvent).localTarget;

      // Ignore the event if this is coming from a focused light child, since that
      // element will deal with it.
      if (this.isLightDescendant(/** @type {Node} */(target)))
        return;

      if (this.pressed) {
        this._asyncClick();
      }
      this._setPressed(false);
    },

    // trigger click asynchronously, the asynchrony is useful to allow one
    // event handler to unwind before triggering another event
    _asyncClick: function() {
      this.async(function() {
        this.click();
      }, 1);
    },

    // any of these changes are considered a change to button state

    _pressedChanged: function(pressed) {
      this._changedButtonState();
    },

    _ariaActiveAttributeChanged: function(value, oldValue) {
      if (oldValue && oldValue != value && this.hasAttribute(oldValue)) {
        this.removeAttribute(oldValue);
      }
    },

    _activeChanged: function(active, ariaActiveAttribute) {
      if (this.toggles) {
        this.setAttribute(this.ariaActiveAttribute,
                          active ? 'true' : 'false');
      } else {
        this.removeAttribute(this.ariaActiveAttribute);
      }
      this._changedButtonState();
    },

    _controlStateChanged: function() {
      if (this.disabled) {
        this._setPressed(false);
      } else {
        this._changedButtonState();
      }
    },

    // provide hook for follow-on behaviors to react to button-state

    _changedButtonState: function() {
      if (this._buttonStateChanged) {
        this._buttonStateChanged(); // abstract
      }
    }

  };

  /** @polymerBehavior */
  Polymer.IronButtonState = [
    Polymer.IronA11yKeysBehavior,
    Polymer.IronButtonStateImpl
  ];
(function() {
    var Utility = {
      distance: function(x1, y1, x2, y2) {
        var xDelta = (x1 - x2);
        var yDelta = (y1 - y2);

        return Math.sqrt(xDelta * xDelta + yDelta * yDelta);
      },

      now: window.performance && window.performance.now ?
          window.performance.now.bind(window.performance) : Date.now
    };

    /**
     * @param {HTMLElement} element
     * @constructor
     */
    function ElementMetrics(element) {
      this.element = element;
      this.width = this.boundingRect.width;
      this.height = this.boundingRect.height;

      this.size = Math.max(this.width, this.height);
    }

    ElementMetrics.prototype = {
      get boundingRect () {
        return this.element.getBoundingClientRect();
      },

      furthestCornerDistanceFrom: function(x, y) {
        var topLeft = Utility.distance(x, y, 0, 0);
        var topRight = Utility.distance(x, y, this.width, 0);
        var bottomLeft = Utility.distance(x, y, 0, this.height);
        var bottomRight = Utility.distance(x, y, this.width, this.height);

        return Math.max(topLeft, topRight, bottomLeft, bottomRight);
      }
    };

    /**
     * @param {HTMLElement} element
     * @constructor
     */
    function Ripple(element) {
      this.element = element;
      this.color = window.getComputedStyle(element).color;

      this.wave = document.createElement('div');
      this.waveContainer = document.createElement('div');
      this.wave.style.backgroundColor = this.color;
      this.wave.classList.add('wave');
      this.waveContainer.classList.add('wave-container');
      Polymer.dom(this.waveContainer).appendChild(this.wave);

      this.resetInteractionState();
    }

    Ripple.MAX_RADIUS = 300;

    Ripple.prototype = {
      get recenters() {
        return this.element.recenters;
      },

      get center() {
        return this.element.center;
      },

      get mouseDownElapsed() {
        var elapsed;

        if (!this.mouseDownStart) {
          return 0;
        }

        elapsed = Utility.now() - this.mouseDownStart;

        if (this.mouseUpStart) {
          elapsed -= this.mouseUpElapsed;
        }

        return elapsed;
      },

      get mouseUpElapsed() {
        return this.mouseUpStart ?
          Utility.now () - this.mouseUpStart : 0;
      },

      get mouseDownElapsedSeconds() {
        return this.mouseDownElapsed / 1000;
      },

      get mouseUpElapsedSeconds() {
        return this.mouseUpElapsed / 1000;
      },

      get mouseInteractionSeconds() {
        return this.mouseDownElapsedSeconds + this.mouseUpElapsedSeconds;
      },

      get initialOpacity() {
        return this.element.initialOpacity;
      },

      get opacityDecayVelocity() {
        return this.element.opacityDecayVelocity;
      },

      get radius() {
        var width2 = this.containerMetrics.width * this.containerMetrics.width;
        var height2 = this.containerMetrics.height * this.containerMetrics.height;
        var waveRadius = Math.min(
          Math.sqrt(width2 + height2),
          Ripple.MAX_RADIUS
        ) * 1.1 + 5;

        var duration = 1.1 - 0.2 * (waveRadius / Ripple.MAX_RADIUS);
        var timeNow = this.mouseInteractionSeconds / duration;
        var size = waveRadius * (1 - Math.pow(80, -timeNow));

        return Math.abs(size);
      },

      get opacity() {
        if (!this.mouseUpStart) {
          return this.initialOpacity;
        }

        return Math.max(
          0,
          this.initialOpacity - this.mouseUpElapsedSeconds * this.opacityDecayVelocity
        );
      },

      get outerOpacity() {
        // Linear increase in background opacity, capped at the opacity
        // of the wavefront (waveOpacity).
        var outerOpacity = this.mouseUpElapsedSeconds * 0.3;
        var waveOpacity = this.opacity;

        return Math.max(
          0,
          Math.min(outerOpacity, waveOpacity)
        );
      },

      get isOpacityFullyDecayed() {
        return this.opacity < 0.01 &&
          this.radius >= Math.min(this.maxRadius, Ripple.MAX_RADIUS);
      },

      get isRestingAtMaxRadius() {
        return this.opacity >= this.initialOpacity &&
          this.radius >= Math.min(this.maxRadius, Ripple.MAX_RADIUS);
      },

      get isAnimationComplete() {
        return this.mouseUpStart ?
          this.isOpacityFullyDecayed : this.isRestingAtMaxRadius;
      },

      get translationFraction() {
        return Math.min(
          1,
          this.radius / this.containerMetrics.size * 2 / Math.sqrt(2)
        );
      },

      get xNow() {
        if (this.xEnd) {
          return this.xStart + this.translationFraction * (this.xEnd - this.xStart);
        }

        return this.xStart;
      },

      get yNow() {
        if (this.yEnd) {
          return this.yStart + this.translationFraction * (this.yEnd - this.yStart);
        }

        return this.yStart;
      },

      get isMouseDown() {
        return this.mouseDownStart && !this.mouseUpStart;
      },

      resetInteractionState: function() {
        this.maxRadius = 0;
        this.mouseDownStart = 0;
        this.mouseUpStart = 0;

        this.xStart = 0;
        this.yStart = 0;
        this.xEnd = 0;
        this.yEnd = 0;
        this.slideDistance = 0;

        this.containerMetrics = new ElementMetrics(this.element);
      },

      draw: function() {
        var scale;
        var translateString;
        var dx;
        var dy;

        this.wave.style.opacity = this.opacity;

        scale = this.radius / (this.containerMetrics.size / 2);
        dx = this.xNow - (this.containerMetrics.width / 2);
        dy = this.yNow - (this.containerMetrics.height / 2);


        // 2d transform for safari because of border-radius and overflow:hidden clipping bug.
        // https://bugs.webkit.org/show_bug.cgi?id=98538
        this.waveContainer.style.webkitTransform = 'translate(' + dx + 'px, ' + dy + 'px)';
        this.waveContainer.style.transform = 'translate3d(' + dx + 'px, ' + dy + 'px, 0)';
        this.wave.style.webkitTransform = 'scale(' + scale + ',' + scale + ')';
        this.wave.style.transform = 'scale3d(' + scale + ',' + scale + ',1)';
      },

      /** @param {Event=} event */
      downAction: function(event) {
        var xCenter = this.containerMetrics.width / 2;
        var yCenter = this.containerMetrics.height / 2;

        this.resetInteractionState();
        this.mouseDownStart = Utility.now();

        if (this.center) {
          this.xStart = xCenter;
          this.yStart = yCenter;
          this.slideDistance = Utility.distance(
            this.xStart, this.yStart, this.xEnd, this.yEnd
          );
        } else {
          this.xStart = event ?
              event.detail.x - this.containerMetrics.boundingRect.left :
              this.containerMetrics.width / 2;
          this.yStart = event ?
              event.detail.y - this.containerMetrics.boundingRect.top :
              this.containerMetrics.height / 2;
        }

        if (this.recenters) {
          this.xEnd = xCenter;
          this.yEnd = yCenter;
          this.slideDistance = Utility.distance(
            this.xStart, this.yStart, this.xEnd, this.yEnd
          );
        }

        this.maxRadius = this.containerMetrics.furthestCornerDistanceFrom(
          this.xStart,
          this.yStart
        );

        this.waveContainer.style.top =
          (this.containerMetrics.height - this.containerMetrics.size) / 2 + 'px';
        this.waveContainer.style.left =
          (this.containerMetrics.width - this.containerMetrics.size) / 2 + 'px';

        this.waveContainer.style.width = this.containerMetrics.size + 'px';
        this.waveContainer.style.height = this.containerMetrics.size + 'px';
      },

      /** @param {Event=} event */
      upAction: function(event) {
        if (!this.isMouseDown) {
          return;
        }

        this.mouseUpStart = Utility.now();
      },

      remove: function() {
        Polymer.dom(this.waveContainer.parentNode).removeChild(
          this.waveContainer
        );
      }
    };

    Polymer({
      is: 'paper-ripple',

      behaviors: [
        Polymer.IronA11yKeysBehavior
      ],

      properties: {
        /**
         * The initial opacity set on the wave.
         *
         * @attribute initialOpacity
         * @type number
         * @default 0.25
         */
        initialOpacity: {
          type: Number,
          value: 0.25
        },

        /**
         * How fast (opacity per second) the wave fades out.
         *
         * @attribute opacityDecayVelocity
         * @type number
         * @default 0.8
         */
        opacityDecayVelocity: {
          type: Number,
          value: 0.8
        },

        /**
         * If true, ripples will exhibit a gravitational pull towards
         * the center of their container as they fade away.
         *
         * @attribute recenters
         * @type boolean
         * @default false
         */
        recenters: {
          type: Boolean,
          value: false
        },

        /**
         * If true, ripples will center inside its container
         *
         * @attribute recenters
         * @type boolean
         * @default false
         */
        center: {
          type: Boolean,
          value: false
        },

        /**
         * A list of the visual ripples.
         *
         * @attribute ripples
         * @type Array
         * @default []
         */
        ripples: {
          type: Array,
          value: function() {
            return [];
          }
        },

        /**
         * True when there are visible ripples animating within the
         * element.
         */
        animating: {
          type: Boolean,
          readOnly: true,
          reflectToAttribute: true,
          value: false
        },

        /**
         * If true, the ripple will remain in the "down" state until `holdDown`
         * is set to false again.
         */
        holdDown: {
          type: Boolean,
          value: false,
          observer: '_holdDownChanged'
        },

        /**
         * If true, the ripple will not generate a ripple effect
         * via pointer interaction.
         * Calling ripple's imperative api like `simulatedRipple` will
         * still generate the ripple effect.
         */
        noink: {
          type: Boolean,
          value: false
        },

        _animating: {
          type: Boolean
        },

        _boundAnimate: {
          type: Function,
          value: function() {
            return this.animate.bind(this);
          }
        }
      },

      get target () {
        return this.keyEventTarget;
      },

      keyBindings: {
        'enter:keydown': '_onEnterKeydown',
        'space:keydown': '_onSpaceKeydown',
        'space:keyup': '_onSpaceKeyup'
      },

      attached: function() {
        // Set up a11yKeysBehavior to listen to key events on the target,
        // so that space and enter activate the ripple even if the target doesn't
        // handle key events. The key handlers deal with `noink` themselves.
        if (this.parentNode.nodeType == 11) { // DOCUMENT_FRAGMENT_NODE
          this.keyEventTarget = Polymer.dom(this).getOwnerRoot().host;
        } else {
          this.keyEventTarget = this.parentNode;
        }
        var keyEventTarget = /** @type {!EventTarget} */ (this.keyEventTarget);
        this.listen(keyEventTarget, 'up', 'uiUpAction');
        this.listen(keyEventTarget, 'down', 'uiDownAction');
      },

      detached: function() {
        this.unlisten(this.keyEventTarget, 'up', 'uiUpAction');
        this.unlisten(this.keyEventTarget, 'down', 'uiDownAction');
        this.keyEventTarget = null;
      },

      get shouldKeepAnimating () {
        for (var index = 0; index < this.ripples.length; ++index) {
          if (!this.ripples[index].isAnimationComplete) {
            return true;
          }
        }

        return false;
      },

      simulatedRipple: function() {
        this.downAction(null);

        // Please see polymer/polymer#1305
        this.async(function() {
          this.upAction();
        }, 1);
      },

      /**
       * Provokes a ripple down effect via a UI event,
       * respecting the `noink` property.
       * @param {Event=} event
       */
      uiDownAction: function(event) {
        if (!this.noink) {
          this.downAction(event);
        }
      },

      /**
       * Provokes a ripple down effect via a UI event,
       * *not* respecting the `noink` property.
       * @param {Event=} event
       */
      downAction: function(event) {
        if (this.holdDown && this.ripples.length > 0) {
          return;
        }

        var ripple = this.addRipple();

        ripple.downAction(event);

        if (!this._animating) {
          this._animating = true;
          this.animate();
        }
      },

      /**
       * Provokes a ripple up effect via a UI event,
       * respecting the `noink` property.
       * @param {Event=} event
       */
      uiUpAction: function(event) {
        if (!this.noink) {
          this.upAction(event);
        }
      },

      /**
       * Provokes a ripple up effect via a UI event,
       * *not* respecting the `noink` property.
       * @param {Event=} event
       */
      upAction: function(event) {
        if (this.holdDown) {
          return;
        }

        this.ripples.forEach(function(ripple) {
          ripple.upAction(event);
        });

        this._animating = true;
        this.animate();
      },

      onAnimationComplete: function() {
        this._animating = false;
        this.$.background.style.backgroundColor = null;
        this.fire('transitionend');
      },

      addRipple: function() {
        var ripple = new Ripple(this);

        Polymer.dom(this.$.waves).appendChild(ripple.waveContainer);
        this.$.background.style.backgroundColor = ripple.color;
        this.ripples.push(ripple);

        this._setAnimating(true);

        return ripple;
      },

      removeRipple: function(ripple) {
        var rippleIndex = this.ripples.indexOf(ripple);

        if (rippleIndex < 0) {
          return;
        }

        this.ripples.splice(rippleIndex, 1);

        ripple.remove();

        if (!this.ripples.length) {
          this._setAnimating(false);
        }
      },

      /**
       * This conflicts with Element#antimate().
       * https://developer.mozilla.org/en-US/docs/Web/API/Element/animate
       * @suppress {checkTypes}
       */
      animate: function() {
        if (!this._animating) {
          return;
        }
        var index;
        var ripple;

        for (index = 0; index < this.ripples.length; ++index) {
          ripple = this.ripples[index];

          ripple.draw();

          this.$.background.style.opacity = ripple.outerOpacity;

          if (ripple.isOpacityFullyDecayed && !ripple.isRestingAtMaxRadius) {
            this.removeRipple(ripple);
          }
        }

        if (!this.shouldKeepAnimating && this.ripples.length === 0) {
          this.onAnimationComplete();
        } else {
          window.requestAnimationFrame(this._boundAnimate);
        }
      },

      _onEnterKeydown: function() {
        this.uiDownAction();
        this.async(this.uiUpAction, 1);
      },

      _onSpaceKeydown: function() {
        this.uiDownAction();
      },

      _onSpaceKeyup: function() {
        this.uiUpAction();
      },

      // note: holdDown does not respect noink since it can be a focus based
      // effect.
      _holdDownChanged: function(newVal, oldVal) {
        if (oldVal === undefined) {
          return;
        }
        if (newVal) {
          this.downAction();
        } else {
          this.upAction();
        }
      }

      /**
      Fired when the animation finishes.
      This is useful if you want to wait until
      the ripple animation finishes to perform some action.

      @event transitionend
      @param {{node: Object}} detail Contains the animated node.
      */
    });
  })();
/**
   * `Polymer.PaperRippleBehavior` dynamically implements a ripple
   * when the element has focus via pointer or keyboard.
   *
   * NOTE: This behavior is intended to be used in conjunction with and after
   * `Polymer.IronButtonState` and `Polymer.IronControlState`.
   *
   * @polymerBehavior Polymer.PaperRippleBehavior
   */
  Polymer.PaperRippleBehavior = {
    properties: {
      /**
       * If true, the element will not produce a ripple effect when interacted
       * with via the pointer.
       */
      noink: {
        type: Boolean,
        observer: '_noinkChanged'
      },

      /**
       * @type {Element|undefined}
       */
      _rippleContainer: {
        type: Object,
      }
    },

    /**
     * Ensures a `<paper-ripple>` element is available when the element is
     * focused.
     */
    _buttonStateChanged: function() {
      if (this.focused) {
        this.ensureRipple();
      }
    },

    /**
     * In addition to the functionality provided in `IronButtonState`, ensures
     * a ripple effect is created when the element is in a `pressed` state.
     */
    _downHandler: function(event) {
      Polymer.IronButtonStateImpl._downHandler.call(this, event);
      if (this.pressed) {
        this.ensureRipple(event);
      }
    },

    /**
     * Ensures this element contains a ripple effect. For startup efficiency
     * the ripple effect is dynamically on demand when needed.
     * @param {!Event=} optTriggeringEvent (optional) event that triggered the
     * ripple.
     */
    ensureRipple: function(optTriggeringEvent) {
      if (!this.hasRipple()) {
        this._ripple = this._createRipple();
        this._ripple.noink = this.noink;
        var rippleContainer = this._rippleContainer || this.root;
        if (rippleContainer) {
          Polymer.dom(rippleContainer).appendChild(this._ripple);
        }
        if (optTriggeringEvent) {
          // Check if the event happened inside of the ripple container
          // Fall back to host instead of the root because distributed text
          // nodes are not valid event targets
          var domContainer = Polymer.dom(this._rippleContainer || this);
          var target = Polymer.dom(optTriggeringEvent).rootTarget;
          if (domContainer.deepContains( /** @type {Node} */(target))) {
            this._ripple.uiDownAction(optTriggeringEvent);
          }
        }
      }
    },

    /**
     * Returns the `<paper-ripple>` element used by this element to create
     * ripple effects. The element's ripple is created on demand, when
     * necessary, and calling this method will force the
     * ripple to be created.
     */
    getRipple: function() {
      this.ensureRipple();
      return this._ripple;
    },

    /**
     * Returns true if this element currently contains a ripple effect.
     * @return {boolean}
     */
    hasRipple: function() {
      return Boolean(this._ripple);
    },

    /**
     * Create the element's ripple effect via creating a `<paper-ripple>`.
     * Override this method to customize the ripple element.
     * @return {!PaperRippleElement} Returns a `<paper-ripple>` element.
     */
    _createRipple: function() {
      return /** @type {!PaperRippleElement} */ (
          document.createElement('paper-ripple'));
    },

    _noinkChanged: function(noink) {
      if (this.hasRipple()) {
        this._ripple.noink = noink;
      }
    }
  };
/** @polymerBehavior Polymer.PaperButtonBehavior */
  Polymer.PaperButtonBehaviorImpl = {
    properties: {
      /**
       * The z-depth of this element, from 0-5. Setting to 0 will remove the
       * shadow, and each increasing number greater than 0 will be "deeper"
       * than the last.
       *
       * @attribute elevation
       * @type number
       * @default 1
       */
      elevation: {
        type: Number,
        reflectToAttribute: true,
        readOnly: true
      }
    },

    observers: [
      '_calculateElevation(focused, disabled, active, pressed, receivedFocusFromKeyboard)',
      '_computeKeyboardClass(receivedFocusFromKeyboard)'
    ],

    hostAttributes: {
      role: 'button',
      tabindex: '0',
      animated: true
    },

    _calculateElevation: function() {
      var e = 1;
      if (this.disabled) {
        e = 0;
      } else if (this.active || this.pressed) {
        e = 4;
      } else if (this.receivedFocusFromKeyboard) {
        e = 3;
      }
      this._setElevation(e);
    },

    _computeKeyboardClass: function(receivedFocusFromKeyboard) {
      this.toggleClass('keyboard-focus', receivedFocusFromKeyboard);
    },

    /**
     * In addition to `IronButtonState` behavior, when space key goes down,
     * create a ripple down effect.
     *
     * @param {!KeyboardEvent} event .
     */
    _spaceKeyDownHandler: function(event) {
      Polymer.IronButtonStateImpl._spaceKeyDownHandler.call(this, event);
      // Ensure that there is at most one ripple when the space key is held down.
      if (this.hasRipple() && this.getRipple().ripples.length < 1) {
        this._ripple.uiDownAction();
      }
    },

    /**
     * In addition to `IronButtonState` behavior, when space key goes up,
     * create a ripple up effect.
     *
     * @param {!KeyboardEvent} event .
     */
    _spaceKeyUpHandler: function(event) {
      Polymer.IronButtonStateImpl._spaceKeyUpHandler.call(this, event);
      if (this.hasRipple()) {
        this._ripple.uiUpAction();
      }
    }
  };

  /** @polymerBehavior */
  Polymer.PaperButtonBehavior = [
    Polymer.IronButtonState,
    Polymer.IronControlState,
    Polymer.PaperRippleBehavior,
    Polymer.PaperButtonBehaviorImpl
  ];
Polymer({
      is: 'paper-button',

      behaviors: [
        Polymer.PaperButtonBehavior
      ],

      properties: {
        /**
         * If true, the button should be styled with a shadow.
         */
        raised: {
          type: Boolean,
          reflectToAttribute: true,
          value: false,
          observer: '_calculateElevation'
        }
      },

      _calculateElevation: function() {
        if (!this.raised) {
          this._setElevation(0);
        } else {
          Polymer.PaperButtonBehaviorImpl._calculateElevation.apply(this);
        }
      }

      /**
      Fired when the animation finishes.
      This is useful if you want to wait until
      the ripple animation finishes to perform some action.

      @event transitionend
      Event param: {{node: Object}} detail Contains the animated node.
      */
    });
Polymer({

    is: 'iron-media-query',

    properties: {

      /**
       * The Boolean return value of the media query.
       */
      queryMatches: {
        type: Boolean,
        value: false,
        readOnly: true,
        notify: true
      },

      /**
       * The CSS media query to evaluate.
       */
      query: {
        type: String,
        observer: 'queryChanged'
      },

      /**
       * If true, the query attribute is assumed to be a complete media query
       * string rather than a single media feature.
       */
      full: {
        type: Boolean,
        value: false
      },

      /**
       * @type {function(MediaQueryList)}
       */
      _boundMQHandler: {
        value: function() {
          return this.queryHandler.bind(this);
        }
      },

      /**
       * @type {MediaQueryList}
       */
      _mq: {
        value: null
      }
    },

    attached: function() {
      this.style.display = 'none';
      this.queryChanged();
    },

    detached: function() {
      this._remove();
    },

    _add: function() {
      if (this._mq) {
        this._mq.addListener(this._boundMQHandler);
      }
    },

    _remove: function() {
      if (this._mq) {
        this._mq.removeListener(this._boundMQHandler);
      }
      this._mq = null;
    },

    queryChanged: function() {
      this._remove();
      var query = this.query;
      if (!query) {
        return;
      }
      if (!this.full && query[0] !== '(') {
        query = '(' + query + ')';
      }
      this._mq = window.matchMedia(query);
      this._add();
      this.queryHandler(this._mq);
    },

    queryHandler: function(mq) {
      this._setQueryMatches(mq.matches);
    }

  });
/**
   * @param {!Function} selectCallback
   * @constructor
   */
  Polymer.IronSelection = function(selectCallback) {
    this.selection = [];
    this.selectCallback = selectCallback;
  };

  Polymer.IronSelection.prototype = {

    /**
     * Retrieves the selected item(s).
     *
     * @method get
     * @returns Returns the selected item(s). If the multi property is true,
     * `get` will return an array, otherwise it will return
     * the selected item or undefined if there is no selection.
     */
    get: function() {
      return this.multi ? this.selection.slice() : this.selection[0];
    },

    /**
     * Clears all the selection except the ones indicated.
     *
     * @method clear
     * @param {Array} excludes items to be excluded.
     */
    clear: function(excludes) {
      this.selection.slice().forEach(function(item) {
        if (!excludes || excludes.indexOf(item) < 0) {
          this.setItemSelected(item, false);
        }
      }, this);
    },

    /**
     * Indicates if a given item is selected.
     *
     * @method isSelected
     * @param {*} item The item whose selection state should be checked.
     * @returns Returns true if `item` is selected.
     */
    isSelected: function(item) {
      return this.selection.indexOf(item) >= 0;
    },

    /**
     * Sets the selection state for a given item to either selected or deselected.
     *
     * @method setItemSelected
     * @param {*} item The item to select.
     * @param {boolean} isSelected True for selected, false for deselected.
     */
    setItemSelected: function(item, isSelected) {
      if (item != null) {
        if (isSelected !== this.isSelected(item)) {
          // proceed to update selection only if requested state differs from current
          if (isSelected) {
            this.selection.push(item);
          } else {
            var i = this.selection.indexOf(item);
            if (i >= 0) {
              this.selection.splice(i, 1);
            }
          }
          if (this.selectCallback) {
            this.selectCallback(item, isSelected);
          }
        }
      }
    },

    /**
     * Sets the selection state for a given item. If the `multi` property
     * is true, then the selected state of `item` will be toggled; otherwise
     * the `item` will be selected.
     *
     * @method select
     * @param {*} item The item to select.
     */
    select: function(item) {
      if (this.multi) {
        this.toggle(item);
      } else if (this.get() !== item) {
        this.setItemSelected(this.get(), false);
        this.setItemSelected(item, true);
      }
    },

    /**
     * Toggles the selection state for `item`.
     *
     * @method toggle
     * @param {*} item The item to toggle.
     */
    toggle: function(item) {
      this.setItemSelected(item, !this.isSelected(item));
    }

  };
/** @polymerBehavior */
  Polymer.IronSelectableBehavior = {

      /**
       * Fired when iron-selector is activated (selected or deselected).
       * It is fired before the selected items are changed.
       * Cancel the event to abort selection.
       *
       * @event iron-activate
       */

      /**
       * Fired when an item is selected
       *
       * @event iron-select
       */

      /**
       * Fired when an item is deselected
       *
       * @event iron-deselect
       */

      /**
       * Fired when the list of selectable items changes (e.g., items are
       * added or removed). The detail of the event is a mutation record that
       * describes what changed.
       *
       * @event iron-items-changed
       */

    properties: {

      /**
       * If you want to use an attribute value or property of an element for
       * `selected` instead of the index, set this to the name of the attribute
       * or property. Hyphenated values are converted to camel case when used to
       * look up the property of a selectable element. Camel cased values are
       * *not* converted to hyphenated values for attribute lookup. It's
       * recommended that you provide the hyphenated form of the name so that
       * selection works in both cases. (Use `attr-or-property-name` instead of
       * `attrOrPropertyName`.)
       */
      attrForSelected: {
        type: String,
        value: null
      },

      /**
       * Gets or sets the selected element. The default is to use the index of the item.
       * @type {string|number}
       */
      selected: {
        type: String,
        notify: true
      },

      /**
       * Returns the currently selected item.
       *
       * @type {?Object}
       */
      selectedItem: {
        type: Object,
        readOnly: true,
        notify: true
      },

      /**
       * The event that fires from items when they are selected. Selectable
       * will listen for this event from items and update the selection state.
       * Set to empty string to listen to no events.
       */
      activateEvent: {
        type: String,
        value: 'tap',
        observer: '_activateEventChanged'
      },

      /**
       * This is a CSS selector string.  If this is set, only items that match the CSS selector
       * are selectable.
       */
      selectable: String,

      /**
       * The class to set on elements when selected.
       */
      selectedClass: {
        type: String,
        value: 'iron-selected'
      },

      /**
       * The attribute to set on elements when selected.
       */
      selectedAttribute: {
        type: String,
        value: null
      },

      /**
       * Default fallback if the selection based on selected with `attrForSelected`
       * is not found.
       */
      fallbackSelection: {
        type: String,
        value: null
      },

      /**
       * The list of items from which a selection can be made.
       */
      items: {
        type: Array,
        readOnly: true,
        notify: true,
        value: function() {
          return [];
        }
      },

      /**
       * The set of excluded elements where the key is the `localName`
       * of the element that will be ignored from the item list.
       *
       * @default {template: 1}
       */
      _excludedLocalNames: {
        type: Object,
        value: function() {
          return {
            'template': 1
          };
        }
      }
    },

    observers: [
      '_updateAttrForSelected(attrForSelected)',
      '_updateSelected(selected)',
      '_checkFallback(fallbackSelection)'
    ],

    created: function() {
      this._bindFilterItem = this._filterItem.bind(this);
      this._selection = new Polymer.IronSelection(this._applySelection.bind(this));
    },

    attached: function() {
      this._observer = this._observeItems(this);
      this._updateItems();
      if (!this._shouldUpdateSelection) {
        this._updateSelected();
      }
      this._addListener(this.activateEvent);
    },

    detached: function() {
      if (this._observer) {
        Polymer.dom(this).unobserveNodes(this._observer);
      }
      this._removeListener(this.activateEvent);
    },

    /**
     * Returns the index of the given item.
     *
     * @method indexOf
     * @param {Object} item
     * @returns Returns the index of the item
     */
    indexOf: function(item) {
      return this.items.indexOf(item);
    },

    /**
     * Selects the given value.
     *
     * @method select
     * @param {string|number} value the value to select.
     */
    select: function(value) {
      this.selected = value;
    },

    /**
     * Selects the previous item.
     *
     * @method selectPrevious
     */
    selectPrevious: function() {
      var length = this.items.length;
      var index = (Number(this._valueToIndex(this.selected)) - 1 + length) % length;
      this.selected = this._indexToValue(index);
    },

    /**
     * Selects the next item.
     *
     * @method selectNext
     */
    selectNext: function() {
      var index = (Number(this._valueToIndex(this.selected)) + 1) % this.items.length;
      this.selected = this._indexToValue(index);
    },

    /**
     * Selects the item at the given index.
     *
     * @method selectIndex
     */
    selectIndex: function(index) {
      this.select(this._indexToValue(index));
    },

    /**
     * Force a synchronous update of the `items` property.
     *
     * NOTE: Consider listening for the `iron-items-changed` event to respond to
     * updates to the set of selectable items after updates to the DOM list and
     * selection state have been made.
     *
     * WARNING: If you are using this method, you should probably consider an
     * alternate approach. Synchronously querying for items is potentially
     * slow for many use cases. The `items` property will update asynchronously
     * on its own to reflect selectable items in the DOM.
     */
    forceSynchronousItemUpdate: function() {
      this._updateItems();
    },

    get _shouldUpdateSelection() {
      return this.selected != null;
    },

    _checkFallback: function() {
      if (this._shouldUpdateSelection) {
        this._updateSelected();
      }
    },

    _addListener: function(eventName) {
      this.listen(this, eventName, '_activateHandler');
    },

    _removeListener: function(eventName) {
      this.unlisten(this, eventName, '_activateHandler');
    },

    _activateEventChanged: function(eventName, old) {
      this._removeListener(old);
      this._addListener(eventName);
    },

    _updateItems: function() {
      var nodes = Polymer.dom(this).queryDistributedElements(this.selectable || '*');
      nodes = Array.prototype.filter.call(nodes, this._bindFilterItem);
      this._setItems(nodes);
    },

    _updateAttrForSelected: function() {
      if (this._shouldUpdateSelection) {
        this.selected = this._indexToValue(this.indexOf(this.selectedItem));
      }
    },

    _updateSelected: function() {
      this._selectSelected(this.selected);
    },

    _selectSelected: function(selected) {
      this._selection.select(this._valueToItem(this.selected));
      // Check for items, since this array is populated only when attached
      // Since Number(0) is falsy, explicitly check for undefined
      if (this.fallbackSelection && this.items.length && (this._selection.get() === undefined)) {
        this.selected = this.fallbackSelection;
      }
    },

    _filterItem: function(node) {
      return !this._excludedLocalNames[node.localName];
    },

    _valueToItem: function(value) {
      return (value == null) ? null : this.items[this._valueToIndex(value)];
    },

    _valueToIndex: function(value) {
      if (this.attrForSelected) {
        for (var i = 0, item; item = this.items[i]; i++) {
          if (this._valueForItem(item) == value) {
            return i;
          }
        }
      } else {
        return Number(value);
      }
    },

    _indexToValue: function(index) {
      if (this.attrForSelected) {
        var item = this.items[index];
        if (item) {
          return this._valueForItem(item);
        }
      } else {
        return index;
      }
    },

    _valueForItem: function(item) {
      var propValue = item[Polymer.CaseMap.dashToCamelCase(this.attrForSelected)];
      return propValue != undefined ? propValue : item.getAttribute(this.attrForSelected);
    },

    _applySelection: function(item, isSelected) {
      if (this.selectedClass) {
        this.toggleClass(this.selectedClass, isSelected, item);
      }
      if (this.selectedAttribute) {
        this.toggleAttribute(this.selectedAttribute, isSelected, item);
      }
      this._selectionChange();
      this.fire('iron-' + (isSelected ? 'select' : 'deselect'), {item: item});
    },

    _selectionChange: function() {
      this._setSelectedItem(this._selection.get());
    },

    // observe items change under the given node.
    _observeItems: function(node) {
      return Polymer.dom(node).observeNodes(function(mutation) {
        this._updateItems();

        if (this._shouldUpdateSelection) {
          this._updateSelected();
        }

        // Let other interested parties know about the change so that
        // we don't have to recreate mutation observers everywhere.
        this.fire('iron-items-changed', mutation, {
          bubbles: false,
          cancelable: false
        });
      });
    },

    _activateHandler: function(e) {
      var t = e.target;
      var items = this.items;
      while (t && t != this) {
        var i = items.indexOf(t);
        if (i >= 0) {
          var value = this._indexToValue(i);
          this._itemActivate(value, t);
          return;
        }
        t = t.parentNode;
      }
    },

    _itemActivate: function(value, item) {
      if (!this.fire('iron-activate',
          {selected: value, item: item}, {cancelable: true}).defaultPrevented) {
        this.select(value);
      }
    }

  };
/** @polymerBehavior Polymer.IronMultiSelectableBehavior */
  Polymer.IronMultiSelectableBehaviorImpl = {
    properties: {

      /**
       * If true, multiple selections are allowed.
       */
      multi: {
        type: Boolean,
        value: false,
        observer: 'multiChanged'
      },

      /**
       * Gets or sets the selected elements. This is used instead of `selected` when `multi`
       * is true.
       */
      selectedValues: {
        type: Array,
        notify: true
      },

      /**
       * Returns an array of currently selected items.
       */
      selectedItems: {
        type: Array,
        readOnly: true,
        notify: true
      },

    },

    observers: [
      '_updateSelected(selectedValues.splices)'
    ],

    /**
     * Selects the given value. If the `multi` property is true, then the selected state of the
     * `value` will be toggled; otherwise the `value` will be selected.
     *
     * @method select
     * @param {string|number} value the value to select.
     */
    select: function(value) {
      if (this.multi) {
        if (this.selectedValues) {
          this._toggleSelected(value);
        } else {
          this.selectedValues = [value];
        }
      } else {
        this.selected = value;
      }
    },

    multiChanged: function(multi) {
      this._selection.multi = multi;
    },

    get _shouldUpdateSelection() {
      return this.selected != null ||
        (this.selectedValues != null && this.selectedValues.length);
    },

    _updateAttrForSelected: function() {
      if (!this.multi) {
        Polymer.IronSelectableBehavior._updateAttrForSelected.apply(this);
      } else if (this._shouldUpdateSelection) {
        this.selectedValues = this.selectedItems.map(function(selectedItem) {
          return this._indexToValue(this.indexOf(selectedItem));
        }, this).filter(function(unfilteredValue) {
          return unfilteredValue != null;
        }, this);
      }
    },

    _updateSelected: function() {
      if (this.multi) {
        this._selectMulti(this.selectedValues);
      } else {
        this._selectSelected(this.selected);
      }
    },

    _selectMulti: function(values) {
      if (values) {
        var selectedItems = this._valuesToItems(values);
        // clear all but the current selected items
        this._selection.clear(selectedItems);
        // select only those not selected yet
        for (var i = 0; i < selectedItems.length; i++) {
          this._selection.setItemSelected(selectedItems[i], true);
        }
        // Check for items, since this array is populated only when attached
        if (this.fallbackSelection && this.items.length && !this._selection.get().length) {
          var fallback = this._valueToItem(this.fallbackSelection);
          if (fallback) {
            this.selectedValues = [this.fallbackSelection];
          }
        }
      } else {
        this._selection.clear();
      }
    },

    _selectionChange: function() {
      var s = this._selection.get();
      if (this.multi) {
        this._setSelectedItems(s);
      } else {
        this._setSelectedItems([s]);
        this._setSelectedItem(s);
      }
    },

    _toggleSelected: function(value) {
      var i = this.selectedValues.indexOf(value);
      var unselected = i < 0;
      if (unselected) {
        this.push('selectedValues',value);
      } else {
        this.splice('selectedValues',i,1);
      }
    },

    _valuesToItems: function(values) {
      return (values == null) ? null : values.map(function(value) {
        return this._valueToItem(value);
      }, this);
    }
  };

  /** @polymerBehavior */
  Polymer.IronMultiSelectableBehavior = [
    Polymer.IronSelectableBehavior,
    Polymer.IronMultiSelectableBehaviorImpl
  ];
/**
  `iron-selector` is an element which can be used to manage a list of elements
  that can be selected.  Tapping on the item will make the item selected.  The `selected` indicates
  which item is being selected.  The default is to use the index of the item.

  Example:

      <iron-selector selected="0">
        <div>Item 1</div>
        <div>Item 2</div>
        <div>Item 3</div>
      </iron-selector>

  If you want to use the attribute value of an element for `selected` instead of the index,
  set `attrForSelected` to the name of the attribute.  For example, if you want to select item by
  `name`, set `attrForSelected` to `name`.

  Example:

      <iron-selector attr-for-selected="name" selected="foo">
        <div name="foo">Foo</div>
        <div name="bar">Bar</div>
        <div name="zot">Zot</div>
      </iron-selector>

  You can specify a default fallback with `fallbackSelection` in case the `selected` attribute does
  not match the `attrForSelected` attribute of any elements.

  Example:

        <iron-selector attr-for-selected="name" selected="non-existing"
                       fallback-selection="default">
          <div name="foo">Foo</div>
          <div name="bar">Bar</div>
          <div name="default">Default</div>
        </iron-selector>

  Note: When the selector is multi, the selection will set to `fallbackSelection` iff
  the number of matching elements is zero.

  `iron-selector` is not styled. Use the `iron-selected` CSS class to style the selected element.

  Example:

      <style>
        .iron-selected {
          background: #eee;
        }
      </style>

      ...

      <iron-selector selected="0">
        <div>Item 1</div>
        <div>Item 2</div>
        <div>Item 3</div>
      </iron-selector>

  @demo demo/index.html
  */

  Polymer({

    is: 'iron-selector',

    behaviors: [
      Polymer.IronMultiSelectableBehavior
    ]

  });
/**
   * `IronResizableBehavior` is a behavior that can be used in Polymer elements to
   * coordinate the flow of resize events between "resizers" (elements that control the
   * size or hidden state of their children) and "resizables" (elements that need to be
   * notified when they are resized or un-hidden by their parents in order to take
   * action on their new measurements).
   *
   * Elements that perform measurement should add the `IronResizableBehavior` behavior to
   * their element definition and listen for the `iron-resize` event on themselves.
   * This event will be fired when they become showing after having been hidden,
   * when they are resized explicitly by another resizable, or when the window has been
   * resized.
   *
   * Note, the `iron-resize` event is non-bubbling.
   *
   * @polymerBehavior Polymer.IronResizableBehavior
   * @demo demo/index.html
   **/
  Polymer.IronResizableBehavior = {
    properties: {
      /**
       * The closest ancestor element that implements `IronResizableBehavior`.
       */
      _parentResizable: {
        type: Object,
        observer: '_parentResizableChanged'
      },

      /**
       * True if this element is currently notifying its descedant elements of
       * resize.
       */
      _notifyingDescendant: {
        type: Boolean,
        value: false
      }
    },

    listeners: {
      'iron-request-resize-notifications': '_onIronRequestResizeNotifications'
    },

    created: function() {
      // We don't really need property effects on these, and also we want them
      // to be created before the `_parentResizable` observer fires:
      this._interestedResizables = [];
      this._boundNotifyResize = this.notifyResize.bind(this);
    },

    attached: function() {
      this.fire('iron-request-resize-notifications', null, {
        node: this,
        bubbles: true,
        cancelable: true
      });

      if (!this._parentResizable) {
        window.addEventListener('resize', this._boundNotifyResize);
        this.notifyResize();
      }
    },

    detached: function() {
      if (this._parentResizable) {
        this._parentResizable.stopResizeNotificationsFor(this);
      } else {
        window.removeEventListener('resize', this._boundNotifyResize);
      }

      this._parentResizable = null;
    },

    /**
     * Can be called to manually notify a resizable and its descendant
     * resizables of a resize change.
     */
    notifyResize: function() {
      if (!this.isAttached) {
        return;
      }

      this._interestedResizables.forEach(function(resizable) {
        if (this.resizerShouldNotify(resizable)) {
          this._notifyDescendant(resizable);
        }
      }, this);

      this._fireResize();
    },

    /**
     * Used to assign the closest resizable ancestor to this resizable
     * if the ancestor detects a request for notifications.
     */
    assignParentResizable: function(parentResizable) {
      this._parentResizable = parentResizable;
    },

    /**
     * Used to remove a resizable descendant from the list of descendants
     * that should be notified of a resize change.
     */
    stopResizeNotificationsFor: function(target) {
      var index = this._interestedResizables.indexOf(target);

      if (index > -1) {
        this._interestedResizables.splice(index, 1);
        this.unlisten(target, 'iron-resize', '_onDescendantIronResize');
      }
    },

    /**
     * This method can be overridden to filter nested elements that should or
     * should not be notified by the current element. Return true if an element
     * should be notified, or false if it should not be notified.
     *
     * @param {HTMLElement} element A candidate descendant element that
     * implements `IronResizableBehavior`.
     * @return {boolean} True if the `element` should be notified of resize.
     */
    resizerShouldNotify: function(element) { return true; },

    _onDescendantIronResize: function(event) {
      if (this._notifyingDescendant) {
        event.stopPropagation();
        return;
      }

      // NOTE(cdata): In ShadowDOM, event retargetting makes echoing of the
      // otherwise non-bubbling event "just work." We do it manually here for
      // the case where Polymer is not using shadow roots for whatever reason:
      if (!Polymer.Settings.useShadow) {
        this._fireResize();
      }
    },

    _fireResize: function() {
      this.fire('iron-resize', null, {
        node: this,
        bubbles: false
      });
    },

    _onIronRequestResizeNotifications: function(event) {
      var target = event.path ? event.path[0] : event.target;

      if (target === this) {
        return;
      }

      if (this._interestedResizables.indexOf(target) === -1) {
        this._interestedResizables.push(target);
        this.listen(target, 'iron-resize', '_onDescendantIronResize');
      }

      target.assignParentResizable(this);
      this._notifyDescendant(target);

      event.stopPropagation();
    },

    _parentResizableChanged: function(parentResizable) {
      if (parentResizable) {
        window.removeEventListener('resize', this._boundNotifyResize);
      }
    },

    _notifyDescendant: function(descendant) {
      // NOTE(cdata): In IE10, attached is fired on children first, so it's
      // important not to notify them if the parent is not attached yet (or
      // else they will get redundantly notified when the parent attaches).
      if (!this.isAttached) {
        return;
      }

      this._notifyingDescendant = true;
      descendant.notifyResize();
      this._notifyingDescendant = false;
    }
  };
(function() {
      'use strict';

      // this would be the only `paper-drawer-panel` in
      // the whole app that can be in `dragging` state
      var sharedPanel = null;

      function classNames(obj) {
        var classes = [];
        for (var key in obj) {
          if (obj.hasOwnProperty(key) && obj[key]) {
            classes.push(key);
          }
        }

        return classes.join(' ');
      }

      Polymer({

        is: 'paper-drawer-panel',

        behaviors: [Polymer.IronResizableBehavior],

        /**
         * Fired when the narrow layout changes.
         *
         * @event paper-responsive-change {{narrow: boolean}} detail -
         *     narrow: true if the panel is in narrow layout.
         */

        /**
         * Fired when the a panel is selected.
         *
         * Listening for this event is an alternative to observing changes in the `selected` attribute.
         * This event is fired both when a panel is selected.
         *
         * @event iron-select {{item: Object}} detail -
         *     item: The panel that the event refers to.
         */

        /**
         * Fired when a panel is deselected.
         *
         * Listening for this event is an alternative to observing changes in the `selected` attribute.
         * This event is fired both when a panel is deselected.
         *
         * @event iron-deselect {{item: Object}} detail -
         *     item: The panel that the event refers to.
         */
        properties: {

          /**
           * The panel to be selected when `paper-drawer-panel` changes to narrow
           * layout.
           */
          defaultSelected: {
            type: String,
            value: 'main'
          },

          /**
           * If true, swipe from the edge is disabled.
           */
          disableEdgeSwipe: {
            type: Boolean,
            value: false
          },

          /**
           * If true, swipe to open/close the drawer is disabled.
           */
          disableSwipe: {
            type: Boolean,
            value: false
          },

          /**
           * Whether the user is dragging the drawer interactively.
           */
          dragging: {
            type: Boolean,
            value: false,
            readOnly: true,
            notify: true
          },

          /**
           * Width of the drawer panel.
           */
          drawerWidth: {
            type: String,
            value: '256px'
          },

          /**
           * How many pixels on the side of the screen are sensitive to edge
           * swipes and peek.
           */
          edgeSwipeSensitivity: {
            type: Number,
            value: 30
          },

          /**
           * If true, ignore `responsiveWidth` setting and force the narrow layout.
           */
          forceNarrow: {
            type: Boolean,
            value: false
          },

          /**
           * Whether the browser has support for the transform CSS property.
           */
          hasTransform: {
            type: Boolean,
            value: function() {
              return 'transform' in this.style;
            }
          },

          /**
           * Whether the browser has support for the will-change CSS property.
           */
          hasWillChange: {
            type: Boolean,
            value: function() {
              return 'willChange' in this.style;
            }
          },

          /**
           * Returns true if the panel is in narrow layout.  This is useful if you
           * need to show/hide elements based on the layout.
           */
          narrow: {
            reflectToAttribute: true,
            type: Boolean,
            value: false,
            readOnly: true,
            notify: true
          },

          /**
           * Whether the drawer is peeking out from the edge.
           */
          peeking: {
            type: Boolean,
            value: false,
            readOnly: true,
            notify: true
          },

          /**
           * Max-width when the panel changes to narrow layout.
           */
          responsiveWidth: {
            type: String,
            value: '768px'
          },

          /**
           * If true, position the drawer to the right.
           */
          rightDrawer: {
            type: Boolean,
            value: false
          },

          /**
           * The panel that is being selected. `drawer` for the drawer panel and
           * `main` for the main panel.
           *
           * @type {string|null}
           */
          selected: {
            reflectToAttribute: true,
            notify: true,
            type: String,
            value: null
          },

          /**
           * The attribute on elements that should toggle the drawer on tap, also elements will
           * automatically be hidden in wide layout.
           */
          drawerToggleAttribute: {
            type: String,
            value: 'paper-drawer-toggle'
          },

          /**
           * The CSS selector for the element that should receive focus when the drawer is open.
           * By default, when the drawer opens, it focuses the first tabbable element. That is,
           * the first element that can receive focus.
           *
           * To disable this behavior, you can set `drawerFocusSelector` to `null` or an empty string.
           *
           */
          drawerFocusSelector: {
            type: String,
            value:
                'a[href]:not([tabindex="-1"]),'+
                'area[href]:not([tabindex="-1"]),'+
                'input:not([disabled]):not([tabindex="-1"]),'+
                'select:not([disabled]):not([tabindex="-1"]),'+
                'textarea:not([disabled]):not([tabindex="-1"]),'+
                'button:not([disabled]):not([tabindex="-1"]),'+
                'iframe:not([tabindex="-1"]),'+
                '[tabindex]:not([tabindex="-1"]),'+
                '[contentEditable=true]:not([tabindex="-1"])'
          },

          /**
           * Whether the transition is enabled.
           */
          _transition: {
            type: Boolean,
            value: false
          },

        },

        listeners: {
          tap: '_onTap',
          track: '_onTrack',
          down: '_downHandler',
          up: '_upHandler',
          transitionend: '_onTransitionEnd'
        },

        observers: [
          '_forceNarrowChanged(forceNarrow, defaultSelected)',
          '_toggleFocusListener(selected)'
        ],

        ready: function() {
          // Avoid transition at the beginning e.g. page loads and enable
          // transitions only after the element is rendered and ready.
          this._transition = true;
          this._boundFocusListener = this._didFocus.bind(this);
        },

        /**
         * Toggles the panel open and closed.
         *
         * @method togglePanel
         */
        togglePanel: function() {
          if (this._isMainSelected()) {
            this.openDrawer();
          } else {
            this.closeDrawer();
          }
        },

        /**
         * Opens the drawer.
         *
         * @method openDrawer
         */
        openDrawer: function() {
          requestAnimationFrame(function() {
            this.toggleClass("transition-drawer", true, this.$.drawer);
            this.selected = 'drawer';
          }.bind(this));
          
        },

        /**
         * Closes the drawer.
         *
         * @method closeDrawer
         */
        closeDrawer: function() {
          requestAnimationFrame(function() {
            this.toggleClass("transition-drawer", true, this.$.drawer);
            this.selected = 'main';
          }.bind(this));
        },

        _onTransitionEnd: function (e) {
          var target = Polymer.dom(e).localTarget;
          if (target !== this) {
            // ignore events coming from the light dom
            return;
          }
          if (e.propertyName === 'left' || e.propertyName === 'right') {
            this.notifyResize();
          }
          if (e.propertyName === 'transform') {
            requestAnimationFrame(function() {
              this.toggleClass("transition-drawer", false, this.$.drawer);
            }.bind(this));
            if (this.selected === 'drawer') {
              var focusedChild = this._getAutoFocusedNode();
              focusedChild && focusedChild.focus();
            }
          }
        },

        _computeIronSelectorClass: function(narrow, transition, dragging, rightDrawer, peeking) {
          return classNames({
            dragging: dragging,
            'narrow-layout': narrow,
            'right-drawer': rightDrawer,
            'left-drawer': !rightDrawer,
            transition: transition,
            peeking: peeking
          });
        },

        _computeDrawerStyle: function(drawerWidth) {
          return 'width:' + drawerWidth + ';';
        },

        _computeMainStyle: function(narrow, rightDrawer, drawerWidth) {
          var style = '';

          style += 'left:' + ((narrow || rightDrawer) ? '0' : drawerWidth) + ';';

          if (rightDrawer) {
            style += 'right:' + (narrow ? '' : drawerWidth) + ';';
          }

          return style;
        },

        _computeMediaQuery: function(forceNarrow, responsiveWidth) {
          return forceNarrow ? '' : '(max-width: ' + responsiveWidth + ')';
        },

        _computeSwipeOverlayHidden: function(narrow, disableEdgeSwipe) {
          return !narrow || disableEdgeSwipe;
        },

        _onTrack: function(event) {
          if (sharedPanel && this !== sharedPanel) {
            return;
          }
          switch (event.detail.state) {
            case 'start':
              this._trackStart(event);
              break;
            case 'track':
              this._trackX(event);
              break;
            case 'end':
              this._trackEnd(event);
              break;
          }
        },

        _responsiveChange: function(narrow) {
          this._setNarrow(narrow);

          this.selected = this.narrow ? this.defaultSelected : null;

          this.setScrollDirection(this._swipeAllowed() ? 'y' : 'all');
          this.fire('paper-responsive-change', {narrow: this.narrow});
        },

        _onQueryMatchesChanged: function(event) {
          this._responsiveChange(event.detail.value);
        },

        _forceNarrowChanged: function() {
          // set the narrow mode only if we reached the `responsiveWidth`
          this._responsiveChange(this.forceNarrow || this.$.mq.queryMatches);
        },

        _swipeAllowed: function() {
          return this.narrow && !this.disableSwipe;
        },

        _isMainSelected: function() {
          return this.selected === 'main';
        },

        _startEdgePeek: function() {
          this.width = this.$.drawer.offsetWidth;
          this._moveDrawer(this._translateXForDeltaX(this.rightDrawer ?
              -this.edgeSwipeSensitivity : this.edgeSwipeSensitivity));
          this._setPeeking(true);
        },

        _stopEdgePeek: function() {
          if (this.peeking) {
            this._setPeeking(false);
            this._moveDrawer(null);
          }
        },

        _downHandler: function(event) {
          if (!this.dragging && this._isMainSelected() && this._isEdgeTouch(event) && !sharedPanel) {
            this._startEdgePeek();
            // cancel selection
            event.preventDefault();
            // grab this panel
            sharedPanel = this;
          }
        },

        _upHandler: function() {
          this._stopEdgePeek();
          // release the panel
          sharedPanel = null;
        },

        _onTap: function(event) {
          var targetElement = Polymer.dom(event).localTarget;
          var isTargetToggleElement = targetElement &&
            this.drawerToggleAttribute &&
            targetElement.hasAttribute(this.drawerToggleAttribute);

          if (isTargetToggleElement) {
            this.togglePanel();
          }
        },

        _isEdgeTouch: function(event) {
          var x = event.detail.x;

          return !this.disableEdgeSwipe && this._swipeAllowed() &&
            (this.rightDrawer ?
              x >= this.offsetWidth - this.edgeSwipeSensitivity :
              x <= this.edgeSwipeSensitivity);
        },

        _trackStart: function(event) {
          if (this._swipeAllowed()) {
            sharedPanel = this;
            this._setDragging(true);

            if (this._isMainSelected()) {
              this._setDragging(this.peeking || this._isEdgeTouch(event));
            }

            if (this.dragging) {
              this.width = this.$.drawer.offsetWidth;
              this._transition = false;
            }
          }
        },

        _translateXForDeltaX: function(deltaX) {
          var isMain = this._isMainSelected();

          if (this.rightDrawer) {
            return Math.max(0, isMain ? this.width + deltaX : deltaX);
          } else {
            return Math.min(0, isMain ? deltaX - this.width : deltaX);
          }
        },

        _trackX: function(event) {
          if (this.dragging) {
            var dx = event.detail.dx;

            if (this.peeking) {
              if (Math.abs(dx) <= this.edgeSwipeSensitivity) {
                // Ignore trackx until we move past the edge peek.
                return;
              }
              this._setPeeking(false);
            }

            this._moveDrawer(this._translateXForDeltaX(dx));
          }
        },

        _trackEnd: function(event) {
          if (this.dragging) {
            var xDirection = event.detail.dx > 0;

            this._setDragging(false);
            this._transition = true;
            sharedPanel = null;
            this._moveDrawer(null);

            if (this.rightDrawer) {
              this[xDirection ? 'closeDrawer' : 'openDrawer']();
            } else {
              this[xDirection ? 'openDrawer' : 'closeDrawer']();
            }
          }
        },

        _transformForTranslateX: function(translateX) {
          if (translateX === null) {
            return '';
          }
          return this.hasWillChange ? 'translateX(' + translateX + 'px)' :
              'translate3d(' + translateX + 'px, 0, 0)';
        },

        _moveDrawer: function(translateX) {
          this.transform(this._transformForTranslateX(translateX), this.$.drawer);
        },

        _getDrawerContent: function() {
          return Polymer.dom(this.$.drawerContent).getDistributedNodes()[0];
        },

        _getAutoFocusedNode: function() {
          var drawerContent = this._getDrawerContent();

          return this.drawerFocusSelector ?
              Polymer.dom(drawerContent).querySelector(this.drawerFocusSelector) || drawerContent : null;
        },

        _toggleFocusListener: function(selected) {
          if (selected === 'drawer') {
            this.addEventListener('focus', this._boundFocusListener, true);
          } else {
            this.removeEventListener('focus', this._boundFocusListener, true);
          }
        },

        _didFocus: function(event) {
          var autoFocusedNode = this._getAutoFocusedNode();
          if (!autoFocusedNode) {
            return;
          }

          var path = Polymer.dom(event).path;
          var focusedChild = path[0];
          var drawerContent = this._getDrawerContent();
          var focusedChildCameFromDrawer = path.indexOf(drawerContent) !== -1;

          if (!focusedChildCameFromDrawer) {
            event.stopPropagation();
            autoFocusedNode.focus();
          }
        },

        _isDrawerClosed: function(narrow, selected) {
          return !narrow || selected !== 'drawer';
        }
      });

    }());
(function() {
      'use strict';

      var SHADOW_WHEN_SCROLLING = 1;
      var SHADOW_ALWAYS = 2;
      var MODE_CONFIGS = {
        outerScroll: {
          'scroll': true
        },

        shadowMode: {
          'standard': SHADOW_ALWAYS,
          'waterfall': SHADOW_WHEN_SCROLLING,
          'waterfall-tall': SHADOW_WHEN_SCROLLING
        },

        tallMode: {
          'waterfall-tall': true
        }
      };

      Polymer({
        is: 'paper-header-panel',

        /**
         * Fired when the content has been scrolled.  `event.detail.target` returns
         * the scrollable element which you can use to access scroll info such as
         * `scrollTop`.
         *
         *     <paper-header-panel on-content-scroll="scrollHandler">
         *       ...
         *     </paper-header-panel>
         *
         *
         *     scrollHandler: function(event) {
         *       var scroller = event.detail.target;
         *       console.log(scroller.scrollTop);
         *     }
         *
         * @event content-scroll
         */

        properties: {
          /**
           * Controls header and scrolling behavior. Options are
           * `standard`, `seamed`, `waterfall`, `waterfall-tall`, `scroll` and
           * `cover`. Default is `standard`.
           *
           * `standard`: The header is a step above the panel. The header will consume the
           * panel at the point of entry, preventing it from passing through to the
           * opposite side.
           *
           * `seamed`: The header is presented as seamed with the panel.
           *
           * `waterfall`: Similar to standard mode, but header is initially presented as
           * seamed with panel, but then separates to form the step.
           *
           * `waterfall-tall`: The header is initially taller (`tall` class is added to
           * the header).  As the user scrolls, the header separates (forming an edge)
           * while condensing (`tall` class is removed from the header).
           *
           * `scroll`: The header keeps its seam with the panel, and is pushed off screen.
           *
           * `cover`: The panel covers the whole `paper-header-panel` including the
           * header. This allows user to style the panel in such a way that the panel is
           * partially covering the header.
           *
           *     <paper-header-panel mode="cover">
           *       <paper-toolbar class="tall">
           *         <paper-icon-button icon="menu"></paper-icon-button>
           *       </paper-toolbar>
           *       <div class="content"></div>
           *     </paper-header-panel>
           */
          mode: {
            type: String,
            value: 'standard',
            observer: '_modeChanged',
            reflectToAttribute: true
          },

          /**
           * If true, the drop-shadow is always shown no matter what mode is set to.
           */
          shadow: {
            type: Boolean,
            value: false
          },

          /**
           * The class used in waterfall-tall mode.  Change this if the header
           * accepts a different class for toggling height, e.g. "medium-tall"
           */
          tallClass: {
            type: String,
            value: 'tall'
          },

          /**
           * If true, the scroller is at the top
           */
          atTop: {
            type: Boolean,
            value: true,
            notify: true,
            readOnly: true,
            reflectToAttribute: true
          }
        },

        observers: [
          '_computeDropShadowHidden(atTop, mode, shadow)'
        ],

        ready: function() {
          this.scrollHandler = this._scroll.bind(this);
        },

        attached: function() {
          this._addListener();
          // Run `scroll` logic once to initialize class names, etc.
          this._keepScrollingState();
        },

        detached: function() {
          this._removeListener();
        },

        /**
         * Returns the header element
         *
         * @property header
         * @type Object
         */
        get header() {
          return Polymer.dom(this.$.headerContent).getDistributedNodes()[0];
        },

        /**
         * Returns the scrollable element.
         *
         * @property scroller
         * @type Object
         */
        get scroller() {
          return this._getScrollerForMode(this.mode);
        },

        /**
         * Returns true if the scroller has a visible shadow.
         *
         * @property visibleShadow
         * @type Boolean
         */
        get visibleShadow() {
          return this.$.dropShadow.classList.contains('has-shadow');
        },

        _computeDropShadowHidden: function(atTop, mode, shadow) {
          var shadowMode = MODE_CONFIGS.shadowMode[mode];

          if (this.shadow) {
            this.toggleClass('has-shadow', true, this.$.dropShadow);
          } else if (shadowMode === SHADOW_ALWAYS) {
            this.toggleClass('has-shadow', true, this.$.dropShadow);
          } else if (shadowMode === SHADOW_WHEN_SCROLLING && !atTop) {
            this.toggleClass('has-shadow', true, this.$.dropShadow);
          } else {
            this.toggleClass('has-shadow', false, this.$.dropShadow);
          }
        },

        _computeMainContainerClass: function(mode) {
          // TODO:  It will be useful to have a utility for classes
          // e.g. Polymer.Utils.classes({ foo: true });

          var classes = {};

          classes['flex'] = mode !== 'cover';

          return Object.keys(classes).filter(
            function(className) {
              return classes[className];
            }).join(' ');
        },

        _addListener: function() {
          this.scroller.addEventListener('scroll', this.scrollHandler, false);
        },

        _removeListener: function() {
          this.scroller.removeEventListener('scroll', this.scrollHandler);
        },

        _modeChanged: function(newMode, oldMode) {
          var configs = MODE_CONFIGS;
          var header = this.header;
          var animateDuration = 200;

          if (header) {
            // in tallMode it may add tallClass to the header; so do the cleanup
            // when mode is changed from tallMode to not tallMode
            if (configs.tallMode[oldMode] && !configs.tallMode[newMode]) {
              header.classList.remove(this.tallClass);
              this.async(function() {
                header.classList.remove('animate');
              }, animateDuration);
            } else {
              this.toggleClass('animate', configs.tallMode[newMode], header);
            }
          }
          this._keepScrollingState();
        },

        _keepScrollingState: function() {
          var main = this.scroller;
          var header = this.header;

          this._setAtTop(main.scrollTop === 0);

          if (header && this.tallClass && MODE_CONFIGS.tallMode[this.mode]) {
            this.toggleClass(this.tallClass, this.atTop ||
                header.classList.contains(this.tallClass) &&
                main.scrollHeight < this.offsetHeight, header);
          }
        },

        _scroll: function() {
          this._keepScrollingState();
          this.fire('content-scroll', {target: this.scroller}, {bubbles: false});
        },

        _getScrollerForMode: function(mode) {
          return MODE_CONFIGS.outerScroll[mode] ?
              this : this.$.mainContainer;
        }
      });
    })();
/**
   * `Polymer.PaperInkyFocusBehavior` implements a ripple when the element has keyboard focus.
   *
   * @polymerBehavior Polymer.PaperInkyFocusBehavior
   */
  Polymer.PaperInkyFocusBehaviorImpl = {
    observers: [
      '_focusedChanged(receivedFocusFromKeyboard)'
    ],

    _focusedChanged: function(receivedFocusFromKeyboard) {
      if (receivedFocusFromKeyboard) {
        this.ensureRipple();
      }
      if (this.hasRipple()) {
        this._ripple.holdDown = receivedFocusFromKeyboard;
      }
    },

    _createRipple: function() {
      var ripple = Polymer.PaperRippleBehavior._createRipple();
      ripple.id = 'ink';
      ripple.setAttribute('center', '');
      ripple.classList.add('circle');
      return ripple;
    }
  };

  /** @polymerBehavior Polymer.PaperInkyFocusBehavior */
  Polymer.PaperInkyFocusBehavior = [
    Polymer.IronButtonState,
    Polymer.IronControlState,
    Polymer.PaperRippleBehavior,
    Polymer.PaperInkyFocusBehaviorImpl
  ];
Polymer({
      is: 'paper-icon-button',

      hostAttributes: {
        role: 'button',
        tabindex: '0'
      },

      behaviors: [
        Polymer.PaperInkyFocusBehavior
      ],

      properties: {
        /**
         * The URL of an image for the icon. If the src property is specified,
         * the icon property should not be.
         */
        src: {
          type: String
        },

        /**
         * Specifies the icon name or index in the set of icons available in
         * the icon's icon set. If the icon property is specified,
         * the src property should not be.
         */
        icon: {
          type: String
        },

        /**
         * Specifies the alternate text for the button, for accessibility.
         */
        alt: {
          type: String,
          observer: "_altChanged"
        }
      },

      _altChanged: function(newValue, oldValue) {
        var label = this.getAttribute('aria-label');

        // Don't stomp over a user-set aria-label.
        if (!label || oldValue == label) {
          this.setAttribute('aria-label', newValue);
        }
      }
    });
/**
  Polymer.IronFormElementBehavior enables a custom element to be included
  in an `iron-form`.

  @demo demo/index.html
  @polymerBehavior
  */
  Polymer.IronFormElementBehavior = {

    properties: {
      /**
       * Fired when the element is added to an `iron-form`.
       *
       * @event iron-form-element-register
       */

      /**
       * Fired when the element is removed from an `iron-form`.
       *
       * @event iron-form-element-unregister
       */

      /**
       * The name of this element.
       */
      name: {
        type: String
      },

      /**
       * The value for this element.
       */
      value: {
        notify: true,
        type: String
      },

      /**
       * Set to true to mark the input as required. If used in a form, a
       * custom element that uses this behavior should also use
       * Polymer.IronValidatableBehavior and define a custom validation method.
       * Otherwise, a `required` element will always be considered valid.
       * It's also strongly recommended to provide a visual style for the element
       * when its value is invalid.
       */
      required: {
        type: Boolean,
        value: false
      },

      /**
       * The form that the element is registered to.
       */
      _parentForm: {
        type: Object
      }
    },

    attached: function() {
      // Note: the iron-form that this element belongs to will set this
      // element's _parentForm property when handling this event.
      this.fire('iron-form-element-register');
    },

    detached: function() {
      if (this._parentForm) {
        this._parentForm.fire('iron-form-element-unregister', {target: this});
      }
    }

  };
(function() {
      'use strict';

      Polymer.IronA11yAnnouncer = Polymer({
        is: 'iron-a11y-announcer',

        properties: {

          /**
           * The value of mode is used to set the `aria-live` attribute
           * for the element that will be announced. Valid values are: `off`,
           * `polite` and `assertive`.
           */
          mode: {
            type: String,
            value: 'polite'
          },

          _text: {
            type: String,
            value: ''
          }
        },

        created: function() {
          if (!Polymer.IronA11yAnnouncer.instance) {
            Polymer.IronA11yAnnouncer.instance = this;
          }

          document.body.addEventListener('iron-announce', this._onIronAnnounce.bind(this));
        },

        /**
         * Cause a text string to be announced by screen readers.
         *
         * @param {string} text The text that should be announced.
         */
        announce: function(text) {
          this._text = '';
          this.async(function() {
            this._text = text;
          }, 100);
        },

        _onIronAnnounce: function(event) {
          if (event.detail && event.detail.text) {
            this.announce(event.detail.text);
          }
        }
      });

      Polymer.IronA11yAnnouncer.instance = null;

      Polymer.IronA11yAnnouncer.requestAvailability = function() {
        if (!Polymer.IronA11yAnnouncer.instance) {
          Polymer.IronA11yAnnouncer.instance = document.createElement('iron-a11y-announcer');
        }

        document.body.appendChild(Polymer.IronA11yAnnouncer.instance);
      };
    })();
/**
   * Singleton IronMeta instance.
   */
  Polymer.IronValidatableBehaviorMeta = null;

  /**
   * `Use Polymer.IronValidatableBehavior` to implement an element that validates user input.
   * Use the related `Polymer.IronValidatorBehavior` to add custom validation logic to an iron-input.
   *
   * By default, an `<iron-form>` element validates its fields when the user presses the submit button.
   * To validate a form imperatively, call the form's `validate()` method, which in turn will
   * call `validate()` on all its children. By using `Polymer.IronValidatableBehavior`, your
   * custom element will get a public `validate()`, which
   * will return the validity of the element, and a corresponding `invalid` attribute,
   * which can be used for styling.
   *
   * To implement the custom validation logic of your element, you must override
   * the protected `_getValidity()` method of this behaviour, rather than `validate()`.
   * See [this](https://github.com/PolymerElements/iron-form/blob/master/demo/simple-element.html)
   * for an example.
   *
   * ### Accessibility
   *
   * Changing the `invalid` property, either manually or by calling `validate()` will update the
   * `aria-invalid` attribute.
   *
   * @demo demo/index.html
   * @polymerBehavior
   */
  Polymer.IronValidatableBehavior = {

    properties: {

      /**
       * Name of the validator to use.
       */
      validator: {
        type: String
      },

      /**
       * True if the last call to `validate` is invalid.
       */
      invalid: {
        notify: true,
        reflectToAttribute: true,
        type: Boolean,
        value: false
      },

      /**
       * This property is deprecated and should not be used. Use the global
       * validator meta singleton, `Polymer.IronValidatableBehaviorMeta` instead.
       */
      _validatorMeta: {
        type: Object
      },

      /**
       * Namespace for this validator. This property is deprecated and should
       * not be used. For all intents and purposes, please consider it a
       * read-only, config-time property.
       */
      validatorType: {
        type: String,
        value: 'validator'
      },

      _validator: {
        type: Object,
        computed: '__computeValidator(validator)'
      }
    },

    observers: [
      '_invalidChanged(invalid)'
    ],

    registered: function() {
      Polymer.IronValidatableBehaviorMeta = new Polymer.IronMeta({type: 'validator'});
    },

    _invalidChanged: function() {
      if (this.invalid) {
        this.setAttribute('aria-invalid', 'true');
      } else {
        this.removeAttribute('aria-invalid');
      }
    },

    /**
     * @return {boolean} True if the validator `validator` exists.
     */
    hasValidator: function() {
      return this._validator != null;
    },

    /**
     * Returns true if the `value` is valid, and updates `invalid`. If you want
     * your element to have custom validation logic, do not override this method;
     * override `_getValidity(value)` instead.

     * @param {Object} value The value to be validated. By default, it is passed
     * to the validator's `validate()` function, if a validator is set.
     * @return {boolean} True if `value` is valid.
     */
    validate: function(value) {
      this.invalid = !this._getValidity(value);
      return !this.invalid;
    },

    /**
     * Returns true if `value` is valid.  By default, it is passed
     * to the validator's `validate()` function, if a validator is set. You
     * should override this method if you want to implement custom validity
     * logic for your element.
     *
     * @param {Object} value The value to be validated.
     * @return {boolean} True if `value` is valid.
     */

    _getValidity: function(value) {
      if (this.hasValidator()) {
        return this._validator.validate(value);
      }
      return true;
    },

    __computeValidator: function() {
      return Polymer.IronValidatableBehaviorMeta &&
          Polymer.IronValidatableBehaviorMeta.byKey(this.validator);
    }
  };
/*
`<iron-input>` adds two-way binding and custom validators using `Polymer.IronValidatorBehavior`
to `<input>`.

### Two-way binding

By default you can only get notified of changes to an `input`'s `value` due to user input:

    <input value="{{myValue::input}}">

`iron-input` adds the `bind-value` property that mirrors the `value` property, and can be used
for two-way data binding. `bind-value` will notify if it is changed either by user input or by script.

    <input is="iron-input" bind-value="{{myValue}}">

### Custom validators

You can use custom validators that implement `Polymer.IronValidatorBehavior` with `<iron-input>`.

    <input is="iron-input" validator="my-custom-validator">

### Stopping invalid input

It may be desirable to only allow users to enter certain characters. You can use the
`prevent-invalid-input` and `allowed-pattern` attributes together to accomplish this. This feature
is separate from validation, and `allowed-pattern` does not affect how the input is validated.

    <!-- only allow characters that match [0-9] -->
    <input is="iron-input" prevent-invalid-input allowed-pattern="[0-9]">

@hero hero.svg
@demo demo/index.html
*/

  Polymer({

    is: 'iron-input',

    extends: 'input',

    behaviors: [
      Polymer.IronValidatableBehavior
    ],

    properties: {

      /**
       * Use this property instead of `value` for two-way data binding.
       */
      bindValue: {
        observer: '_bindValueChanged',
        type: String
      },

      /**
       * Set to true to prevent the user from entering invalid input. If `allowedPattern` is set,
       * any character typed by the user will be matched against that pattern, and rejected if it's not a match.
       * Pasted input will have each character checked individually; if any character
       * doesn't match `allowedPattern`, the entire pasted string will be rejected.
       * If `allowedPattern` is not set, it will use the `type` attribute (only supported for `type=number`).
       */
      preventInvalidInput: {
        type: Boolean
      },

      /**
       * Regular expression that list the characters allowed as input.
       * This pattern represents the allowed characters for the field; as the user inputs text,
       * each individual character will be checked against the pattern (rather than checking
       * the entire value as a whole). The recommended format should be a list of allowed characters;
       * for example, `[a-zA-Z0-9.+-!;:]`
       */
      allowedPattern: {
        type: String,
        observer: "_allowedPatternChanged"
      },

      _previousValidInput: {
        type: String,
        value: ''
      },

      _patternAlreadyChecked: {
        type: Boolean,
        value: false
      }

    },

    listeners: {
      'input': '_onInput',
      'keypress': '_onKeypress'
    },

    /** @suppress {checkTypes} */
    registered: function() {
      // Feature detect whether we need to patch dispatchEvent (i.e. on FF and IE).
      if (!this._canDispatchEventOnDisabled()) {
        this._origDispatchEvent = this.dispatchEvent;
        this.dispatchEvent = this._dispatchEventFirefoxIE;
      }
    },

    created: function() {
      Polymer.IronA11yAnnouncer.requestAvailability();
    },

    _canDispatchEventOnDisabled: function() {
      var input = document.createElement('input');
      var canDispatch = false;
      input.disabled = true;

      input.addEventListener('feature-check-dispatch-event', function() {
        canDispatch = true;
      });

      try {
        input.dispatchEvent(new Event('feature-check-dispatch-event'));
      } catch(e) {}

      return canDispatch;
    },

    _dispatchEventFirefoxIE: function() {
      // Due to Firefox bug, events fired on disabled form controls can throw
      // errors; furthermore, neither IE nor Firefox will actually dispatch
      // events from disabled form controls; as such, we toggle disable around
      // the dispatch to allow notifying properties to notify
      // See issue #47 for details
      var disabled = this.disabled;
      this.disabled = false;
      this._origDispatchEvent.apply(this, arguments);
      this.disabled = disabled;
    },

    get _patternRegExp() {
      var pattern;
      if (this.allowedPattern) {
        pattern = new RegExp(this.allowedPattern);
      } else {
        switch (this.type) {
          case 'number':
            pattern = /[0-9.,e-]/;
            break;
        }
      }
      return pattern;
    },

    ready: function() {
      this.bindValue = this.value;
    },

    /**
     * @suppress {checkTypes}
     */
    _bindValueChanged: function() {
      if (this.value !== this.bindValue) {
        this.value = !(this.bindValue || this.bindValue === 0 || this.bindValue === false) ? '' : this.bindValue;
      }
      // manually notify because we don't want to notify until after setting value
      this.fire('bind-value-changed', {value: this.bindValue});
    },

    _allowedPatternChanged: function() {
      // Force to prevent invalid input when an `allowed-pattern` is set
      this.preventInvalidInput = this.allowedPattern ? true : false;
    },

    _onInput: function() {
      // Need to validate each of the characters pasted if they haven't
      // been validated inside `_onKeypress` already.
      if (this.preventInvalidInput && !this._patternAlreadyChecked) {
        var valid = this._checkPatternValidity();
        if (!valid) {
          this._announceInvalidCharacter('Invalid string of characters not entered.');
          this.value = this._previousValidInput;
        }
      }

      this.bindValue = this.value;
      this._previousValidInput = this.value;
      this._patternAlreadyChecked = false;
    },

    _isPrintable: function(event) {
      // What a control/printable character is varies wildly based on the browser.
      // - most control characters (arrows, backspace) do not send a `keypress` event
      //   in Chrome, but the *do* on Firefox
      // - in Firefox, when they do send a `keypress` event, control chars have
      //   a charCode = 0, keyCode = xx (for ex. 40 for down arrow)
      // - printable characters always send a keypress event.
      // - in Firefox, printable chars always have a keyCode = 0. In Chrome, the keyCode
      //   always matches the charCode.
      // None of this makes any sense.

      // For these keys, ASCII code == browser keycode.
      var anyNonPrintable =
        (event.keyCode == 8)   ||  // backspace
        (event.keyCode == 9)   ||  // tab
        (event.keyCode == 13)  ||  // enter
        (event.keyCode == 27);     // escape

      // For these keys, make sure it's a browser keycode and not an ASCII code.
      var mozNonPrintable =
        (event.keyCode == 19)  ||  // pause
        (event.keyCode == 20)  ||  // caps lock
        (event.keyCode == 45)  ||  // insert
        (event.keyCode == 46)  ||  // delete
        (event.keyCode == 144) ||  // num lock
        (event.keyCode == 145) ||  // scroll lock
        (event.keyCode > 32 && event.keyCode < 41)   || // page up/down, end, home, arrows
        (event.keyCode > 111 && event.keyCode < 124); // fn keys

      return !anyNonPrintable && !(event.charCode == 0 && mozNonPrintable);
    },

    _onKeypress: function(event) {
      if (!this.preventInvalidInput && this.type !== 'number') {
        return;
      }
      var regexp = this._patternRegExp;
      if (!regexp) {
        return;
      }

      // Handle special keys and backspace
      if (event.metaKey || event.ctrlKey || event.altKey)
        return;

      // Check the pattern either here or in `_onInput`, but not in both.
      this._patternAlreadyChecked = true;

      var thisChar = String.fromCharCode(event.charCode);
      if (this._isPrintable(event) && !regexp.test(thisChar)) {
        event.preventDefault();
        this._announceInvalidCharacter('Invalid character ' + thisChar + ' not entered.');
      }
    },

    _checkPatternValidity: function() {
      var regexp = this._patternRegExp;
      if (!regexp) {
        return true;
      }
      for (var i = 0; i < this.value.length; i++) {
        if (!regexp.test(this.value[i])) {
          return false;
        }
      }
      return true;
    },

    /**
     * Returns true if `value` is valid. The validator provided in `validator` will be used first,
     * then any constraints.
     * @return {boolean} True if the value is valid.
     */
    validate: function() {
      // First, check what the browser thinks. Some inputs (like type=number)
      // behave weirdly and will set the value to "" if something invalid is
      // entered, but will set the validity correctly.
      var valid =  this.checkValidity();

      // Only do extra checking if the browser thought this was valid.
      if (valid) {
        // Empty, required input is invalid
        if (this.required && this.value === '') {
          valid = false;
        } else if (this.hasValidator()) {
          valid = Polymer.IronValidatableBehavior.validate.call(this, this.value);
        }
      }

      this.invalid = !valid;
      this.fire('iron-input-validate');
      return valid;
    },

    _announceInvalidCharacter: function(message) {
      this.fire('iron-announce', { text: message });
    }
  });

  /*
  The `iron-input-validate` event is fired whenever `validate()` is called.
  @event iron-input-validate
  */
// Generate unique, monotonically increasing IDs for labels (needed by
  // aria-labelledby) and add-ons.
  Polymer.PaperInputHelper = {};
  Polymer.PaperInputHelper.NextLabelID = 1;
  Polymer.PaperInputHelper.NextAddonID = 1;

  /**
   * Use `Polymer.PaperInputBehavior` to implement inputs with `<paper-input-container>`. This
   * behavior is implemented by `<paper-input>`. It exposes a number of properties from
   * `<paper-input-container>` and `<input is="iron-input">` and they should be bound in your
   * template.
   *
   * The input element can be accessed by the `inputElement` property if you need to access
   * properties or methods that are not exposed.
   * @polymerBehavior Polymer.PaperInputBehavior
   */
  Polymer.PaperInputBehaviorImpl = {

    properties: {
      /**
       * Fired when the input changes due to user interaction.
       *
       * @event change
       */

      /**
       * The label for this input. If you're using PaperInputBehavior to
       * implement your own paper-input-like element, bind this to
       * `<label>`'s content and `hidden` property, e.g.
       * `<label hidden$="[[!label]]">[[label]]</label>` in your `template`
       */
      label: {
        type: String
      },

      /**
       * The value for this input. If you're using PaperInputBehavior to
       * implement your own paper-input-like element, bind this to
       * the `<input is="iron-input">`'s `bindValue`
       * property, or the value property of your input that is `notify:true`.
       */
      value: {
        notify: true,
        type: String
      },

      /**
       * Set to true to disable this input. If you're using PaperInputBehavior to
       * implement your own paper-input-like element, bind this to
       * both the `<paper-input-container>`'s and the input's `disabled` property.
       */
      disabled: {
        type: Boolean,
        value: false
      },

      /**
       * Returns true if the value is invalid. If you're using PaperInputBehavior to
       * implement your own paper-input-like element, bind this to both the
       * `<paper-input-container>`'s and the input's `invalid` property.
       *
       * If `autoValidate` is true, the `invalid` attribute is managed automatically,
       * which can clobber attempts to manage it manually.
       */
      invalid: {
        type: Boolean,
        value: false,
        notify: true
      },

      /**
       * Set to true to prevent the user from entering invalid input. If you're
       * using PaperInputBehavior to  implement your own paper-input-like element,
       * bind this to `<input is="iron-input">`'s `preventInvalidInput` property.
       */
      preventInvalidInput: {
        type: Boolean
      },

      /**
       * Set this to specify the pattern allowed by `preventInvalidInput`. If
       * you're using PaperInputBehavior to implement your own paper-input-like
       * element, bind this to the `<input is="iron-input">`'s `allowedPattern`
       * property.
       */
      allowedPattern: {
        type: String
      },

      /**
       * The type of the input. The supported types are `text`, `number` and `password`.
       * If you're using PaperInputBehavior to implement your own paper-input-like element,
       * bind this to the `<input is="iron-input">`'s `type` property.
       */
      type: {
        type: String
      },

      /**
       * The datalist of the input (if any). This should match the id of an existing `<datalist>`.
       * If you're using PaperInputBehavior to implement your own paper-input-like
       * element, bind this to the `<input is="iron-input">`'s `list` property.
       */
      list: {
        type: String
      },

      /**
       * A pattern to validate the `input` with. If you're using PaperInputBehavior to
       * implement your own paper-input-like element, bind this to
       * the `<input is="iron-input">`'s `pattern` property.
       */
      pattern: {
        type: String
      },

      /**
       * Set to true to mark the input as required. If you're using PaperInputBehavior to
       * implement your own paper-input-like element, bind this to
       * the `<input is="iron-input">`'s `required` property.
       */
      required: {
        type: Boolean,
        value: false
      },

      /**
       * The error message to display when the input is invalid. If you're using
       * PaperInputBehavior to implement your own paper-input-like element,
       * bind this to the `<paper-input-error>`'s content, if using.
       */
      errorMessage: {
        type: String
      },

      /**
       * Set to true to show a character counter.
       */
      charCounter: {
        type: Boolean,
        value: false
      },

      /**
       * Set to true to disable the floating label. If you're using PaperInputBehavior to
       * implement your own paper-input-like element, bind this to
       * the `<paper-input-container>`'s `noLabelFloat` property.
       */
      noLabelFloat: {
        type: Boolean,
        value: false
      },

      /**
       * Set to true to always float the label. If you're using PaperInputBehavior to
       * implement your own paper-input-like element, bind this to
       * the `<paper-input-container>`'s `alwaysFloatLabel` property.
       */
      alwaysFloatLabel: {
        type: Boolean,
        value: false
      },

      /**
       * Set to true to auto-validate the input value. If you're using PaperInputBehavior to
       * implement your own paper-input-like element, bind this to
       * the `<paper-input-container>`'s `autoValidate` property.
       */
      autoValidate: {
        type: Boolean,
        value: false
      },

      /**
       * Name of the validator to use. If you're using PaperInputBehavior to
       * implement your own paper-input-like element, bind this to
       * the `<input is="iron-input">`'s `validator` property.
       */
      validator: {
        type: String
      },

      // HTMLInputElement attributes for binding if needed

      /**
       * If you're using PaperInputBehavior to implement your own paper-input-like
       * element, bind this to the `<input is="iron-input">`'s `autocomplete` property.
       */
      autocomplete: {
        type: String,
        value: 'off'
      },

      /**
       * If you're using PaperInputBehavior to implement your own paper-input-like
       * element, bind this to the `<input is="iron-input">`'s `autofocus` property.
       */
      autofocus: {
        type: Boolean,
        observer: '_autofocusChanged'
      },

      /**
       * If you're using PaperInputBehavior to implement your own paper-input-like
       * element, bind this to the `<input is="iron-input">`'s `inputmode` property.
       */
      inputmode: {
        type: String
      },

      /**
       * The minimum length of the input value.
       * If you're using PaperInputBehavior to implement your own paper-input-like
       * element, bind this to the `<input is="iron-input">`'s `minlength` property.
       */
      minlength: {
        type: Number
      },

      /**
       * The maximum length of the input value.
       * If you're using PaperInputBehavior to implement your own paper-input-like
       * element, bind this to the `<input is="iron-input">`'s `maxlength` property.
       */
      maxlength: {
        type: Number
      },

      /**
       * The minimum (numeric or date-time) input value.
       * If you're using PaperInputBehavior to implement your own paper-input-like
       * element, bind this to the `<input is="iron-input">`'s `min` property.
       */
      min: {
        type: String
      },

      /**
       * The maximum (numeric or date-time) input value.
       * Can be a String (e.g. `"2000-01-01"`) or a Number (e.g. `2`).
       * If you're using PaperInputBehavior to implement your own paper-input-like
       * element, bind this to the `<input is="iron-input">`'s `max` property.
       */
      max: {
        type: String
      },

      /**
       * Limits the numeric or date-time increments.
       * If you're using PaperInputBehavior to implement your own paper-input-like
       * element, bind this to the `<input is="iron-input">`'s `step` property.
       */
      step: {
        type: String
      },

      /**
       * If you're using PaperInputBehavior to implement your own paper-input-like
       * element, bind this to the `<input is="iron-input">`'s `name` property.
       */
      name: {
        type: String
      },

      /**
       * A placeholder string in addition to the label. If this is set, the label will always float.
       */
      placeholder: {
        type: String,
        // need to set a default so _computeAlwaysFloatLabel is run
        value: ''
      },

      /**
       * If you're using PaperInputBehavior to implement your own paper-input-like
       * element, bind this to the `<input is="iron-input">`'s `readonly` property.
       */
      readonly: {
        type: Boolean,
        value: false
      },

      /**
       * If you're using PaperInputBehavior to implement your own paper-input-like
       * element, bind this to the `<input is="iron-input">`'s `size` property.
       */
      size: {
        type: Number
      },

      // Nonstandard attributes for binding if needed

      /**
       * If you're using PaperInputBehavior to implement your own paper-input-like
       * element, bind this to the `<input is="iron-input">`'s `autocapitalize` property.
       */
      autocapitalize: {
        type: String,
        value: 'none'
      },

      /**
       * If you're using PaperInputBehavior to implement your own paper-input-like
       * element, bind this to the `<input is="iron-input">`'s `autocorrect` property.
       */
      autocorrect: {
        type: String,
        value: 'off'
      },

      /**
       * If you're using PaperInputBehavior to implement your own paper-input-like
       * element, bind this to the `<input is="iron-input">`'s `autosave` property,
       * used with type=search.
       */
      autosave: {
        type: String
      },

      /**
       * If you're using PaperInputBehavior to implement your own paper-input-like
       * element, bind this to the `<input is="iron-input">`'s `results` property,
       * used with type=search.
       */
      results: {
        type: Number
      },

      /**
       * If you're using PaperInputBehavior to implement your own paper-input-like
       * element, bind this to the `<input is="iron-input">`'s `accept` property,
       * used with type=file.
       */
      accept: {
        type: String
      },

      /**
       * If you're using PaperInputBehavior to implement your own paper-input-like
       * element, bind this to the`<input is="iron-input">`'s `multiple` property,
       * used with type=file.
       */
      multiple: {
        type: Boolean
      },

      _ariaDescribedBy: {
        type: String,
        value: ''
      },

      _ariaLabelledBy: {
        type: String,
        value: ''
      }

    },

    listeners: {
      'addon-attached': '_onAddonAttached',
    },

    keyBindings: {
      'shift+tab:keydown': '_onShiftTabDown'
    },

    hostAttributes: {
      tabindex: 0
    },

    /**
     * Returns a reference to the input element.
     */
    get inputElement() {
      return this.$.input;
    },

    /**
     * Returns a reference to the focusable element.
     */
    get _focusableElement() {
      return this.inputElement;
    },

    registered: function() {
      // These types have some default placeholder text; overlapping
      // the label on top of it looks terrible. Auto-float the label in this case.
      this._typesThatHaveText = ["date", "datetime", "datetime-local", "month",
          "time", "week", "file"];
    },

    attached: function() {
      this._updateAriaLabelledBy();

      if (this.inputElement &&
          this._typesThatHaveText.indexOf(this.inputElement.type) !== -1) {
        this.alwaysFloatLabel = true;
      }
    },

    _appendStringWithSpace: function(str, more) {
      if (str) {
        str = str + ' ' + more;
      } else {
        str = more;
      }
      return str;
    },

    _onAddonAttached: function(event) {
      var target = event.path ? event.path[0] : event.target;
      if (target.id) {
        this._ariaDescribedBy = this._appendStringWithSpace(this._ariaDescribedBy, target.id);
      } else {
        var id = 'paper-input-add-on-' + Polymer.PaperInputHelper.NextAddonID++;
        target.id = id;
        this._ariaDescribedBy = this._appendStringWithSpace(this._ariaDescribedBy, id);
      }
    },

    /**
     * Validates the input element and sets an error style if needed.
     *
     * @return {boolean}
     */
    validate: function() {
      return this.inputElement.validate();
    },

    /**
     * Forward focus to inputElement. Overriden from IronControlState.
     */
    _focusBlurHandler: function(event) {
      Polymer.IronControlState._focusBlurHandler.call(this, event);

      // Forward the focus to the nested input.
      if (this.focused && !this._shiftTabPressed)
        this._focusableElement.focus();
    },

    /**
     * Handler that is called when a shift+tab keypress is detected by the menu.
     *
     * @param {CustomEvent} event A key combination event.
     */
    _onShiftTabDown: function(event) {
      var oldTabIndex = this.getAttribute('tabindex');
      this._shiftTabPressed = true;
      this.setAttribute('tabindex', '-1');
      this.async(function() {
        this.setAttribute('tabindex', oldTabIndex);
        this._shiftTabPressed = false;
      }, 1);
    },

    /**
     * If `autoValidate` is true, then validates the element.
     */
    _handleAutoValidate: function() {
      if (this.autoValidate)
        this.validate();
    },

    /**
     * Restores the cursor to its original position after updating the value.
     * @param {string} newValue The value that should be saved.
     */
    updateValueAndPreserveCaret: function(newValue) {
      // Not all elements might have selection, and even if they have the
      // right properties, accessing them might throw an exception (like for
      // <input type=number>)
      try {
        var start = this.inputElement.selectionStart;
        this.value = newValue;

        // The cursor automatically jumps to the end after re-setting the value,
        // so restore it to its original position.
        this.inputElement.selectionStart = start;
        this.inputElement.selectionEnd = start;
      } catch (e) {
        // Just set the value and give up on the caret.
        this.value = newValue;
      }
    },

    _computeAlwaysFloatLabel: function(alwaysFloatLabel, placeholder) {
      return placeholder || alwaysFloatLabel;
    },

    _updateAriaLabelledBy: function() {
      var label = Polymer.dom(this.root).querySelector('label');
      if (!label) {
        this._ariaLabelledBy = '';
        return;
      }
      var labelledBy;
      if (label.id) {
        labelledBy = label.id;
      } else {
        labelledBy = 'paper-input-label-' + Polymer.PaperInputHelper.NextLabelID++;
        label.id = labelledBy;
      }
      this._ariaLabelledBy = labelledBy;
    },

    _onChange:function(event) {
      // In the Shadow DOM, the `change` event is not leaked into the
      // ancestor tree, so we must do this manually.
      // See https://w3c.github.io/webcomponents/spec/shadow/#events-that-are-not-leaked-into-ancestor-trees.
      if (this.shadowRoot) {
        this.fire(event.type, {sourceEvent: event}, {
          node: this,
          bubbles: event.bubbles,
          cancelable: event.cancelable
        });
      }
    },

    _autofocusChanged: function() {
      // Firefox doesn't respect the autofocus attribute if it's applied after
      // the page is loaded (Chrome/WebKit do respect it), preventing an
      // autofocus attribute specified in markup from taking effect when the
      // element is upgraded. As a workaround, if the autofocus property is set,
      // and the focus hasn't already been moved elsewhere, we take focus.
      if (this.autofocus && this._focusableElement) {

        // In IE 11, the default document.activeElement can be the page's
        // outermost html element, but there are also cases (under the
        // polyfill?) in which the activeElement is not a real HTMLElement, but
        // just a plain object. We identify the latter case as having no valid
        // activeElement.
        var activeElement = document.activeElement;
        var isActiveElementValid = activeElement instanceof HTMLElement;

        // Has some other element has already taken the focus?
        var isSomeElementActive = isActiveElementValid &&
            activeElement !== document.body &&
            activeElement !== document.documentElement; /* IE 11 */
        if (!isSomeElementActive) {
          // No specific element has taken the focus yet, so we can take it.
          this._focusableElement.focus();
        }
      }
    }
  };

  /** @polymerBehavior */
  Polymer.PaperInputBehavior = [
    Polymer.IronControlState,
    Polymer.IronA11yKeysBehavior,
    Polymer.PaperInputBehaviorImpl
  ];
/**
   * Use `Polymer.PaperInputAddonBehavior` to implement an add-on for `<paper-input-container>`. A
   * add-on appears below the input, and may display information based on the input value and
   * validity such as a character counter or an error message.
   * @polymerBehavior
   */
  Polymer.PaperInputAddonBehavior = {

    hostAttributes: {
      'add-on': ''
    },

    attached: function() {
      this.fire('addon-attached');
    },

    /**
     * The function called by `<paper-input-container>` when the input value or validity changes.
     * @param {{
     *   inputElement: (Element|undefined),
     *   value: (string|undefined),
     *   invalid: boolean
     * }} state -
     *     inputElement: The input element.
     *     value: The input value.
     *     invalid: True if the input value is invalid.
     */
    update: function(state) {
    }

  };
Polymer({
    is: 'paper-input-char-counter',

    behaviors: [
      Polymer.PaperInputAddonBehavior
    ],

    properties: {
      _charCounterStr: {
        type: String,
        value: '0'
      }
    },

    /**
     * This overrides the update function in PaperInputAddonBehavior.
     * @param {{
     *   inputElement: (Element|undefined),
     *   value: (string|undefined),
     *   invalid: boolean
     * }} state -
     *     inputElement: The input element.
     *     value: The input value.
     *     invalid: True if the input value is invalid.
     */
    update: function(state) {
      if (!state.inputElement) {
        return;
      }

      state.value = state.value || '';

      var counter = state.value.toString().length.toString();

      if (state.inputElement.hasAttribute('maxlength')) {
        counter += '/' + state.inputElement.getAttribute('maxlength');
      }

      this._charCounterStr = counter;
    }
  });
Polymer({
    is: 'paper-input-container',

    properties: {
      /**
       * Set to true to disable the floating label. The label disappears when the input value is
       * not null.
       */
      noLabelFloat: {
        type: Boolean,
        value: false
      },

      /**
       * Set to true to always float the floating label.
       */
      alwaysFloatLabel: {
        type: Boolean,
        value: false
      },

      /**
       * The attribute to listen for value changes on.
       */
      attrForValue: {
        type: String,
        value: 'bind-value'
      },

      /**
       * Set to true to auto-validate the input value when it changes.
       */
      autoValidate: {
        type: Boolean,
        value: false
      },

      /**
       * True if the input is invalid. This property is set automatically when the input value
       * changes if auto-validating, or when the `iron-input-validate` event is heard from a child.
       */
      invalid: {
        observer: '_invalidChanged',
        type: Boolean,
        value: false
      },

      /**
       * True if the input has focus.
       */
      focused: {
        readOnly: true,
        type: Boolean,
        value: false,
        notify: true
      },

      _addons: {
        type: Array
        // do not set a default value here intentionally - it will be initialized lazily when a
        // distributed child is attached, which may occur before configuration for this element
        // in polyfill.
      },

      _inputHasContent: {
        type: Boolean,
        value: false
      },

      _inputSelector: {
        type: String,
        value: 'input,textarea,.paper-input-input'
      },

      _boundOnFocus: {
        type: Function,
        value: function() {
          return this._onFocus.bind(this);
        }
      },

      _boundOnBlur: {
        type: Function,
        value: function() {
          return this._onBlur.bind(this);
        }
      },

      _boundOnInput: {
        type: Function,
        value: function() {
          return this._onInput.bind(this);
        }
      },

      _boundValueChanged: {
        type: Function,
        value: function() {
          return this._onValueChanged.bind(this);
        }
      }
    },

    listeners: {
      'addon-attached': '_onAddonAttached',
      'iron-input-validate': '_onIronInputValidate'
    },

    get _valueChangedEvent() {
      return this.attrForValue + '-changed';
    },

    get _propertyForValue() {
      return Polymer.CaseMap.dashToCamelCase(this.attrForValue);
    },

    get _inputElement() {
      return Polymer.dom(this).querySelector(this._inputSelector);
    },

    get _inputElementValue() {
      return this._inputElement[this._propertyForValue] || this._inputElement.value;
    },

    ready: function() {
      if (!this._addons) {
        this._addons = [];
      }
      this.addEventListener('focus', this._boundOnFocus, true);
      this.addEventListener('blur', this._boundOnBlur, true);
    },

    attached: function() {
      if (this.attrForValue) {
        this._inputElement.addEventListener(this._valueChangedEvent, this._boundValueChanged);
      } else {
        this.addEventListener('input', this._onInput);
      }

      // Only validate when attached if the input already has a value.
      if (this._inputElementValue != '') {
        this._handleValueAndAutoValidate(this._inputElement);
      } else {
        this._handleValue(this._inputElement);
      }
    },

    _onAddonAttached: function(event) {
      if (!this._addons) {
        this._addons = [];
      }
      var target = event.target;
      if (this._addons.indexOf(target) === -1) {
        this._addons.push(target);
        if (this.isAttached) {
          this._handleValue(this._inputElement);
        }
      }
    },

    _onFocus: function() {
      this._setFocused(true);
    },

    _onBlur: function() {
      this._setFocused(false);
      this._handleValueAndAutoValidate(this._inputElement);
    },

    _onInput: function(event) {
      this._handleValueAndAutoValidate(event.target);
    },

    _onValueChanged: function(event) {
      this._handleValueAndAutoValidate(event.target);
    },

    _handleValue: function(inputElement) {
      var value = this._inputElementValue;

      // type="number" hack needed because this.value is empty until it's valid
      if (value || value === 0 || (inputElement.type === 'number' && !inputElement.checkValidity())) {
        this._inputHasContent = true;
      } else {
        this._inputHasContent = false;
      }

      this.updateAddons({
        inputElement: inputElement,
        value: value,
        invalid: this.invalid
      });
    },

    _handleValueAndAutoValidate: function(inputElement) {
      if (this.autoValidate) {
        var valid;
        if (inputElement.validate) {
          valid = inputElement.validate(this._inputElementValue);
        } else {
          valid = inputElement.checkValidity();
        }
        this.invalid = !valid;
      }

      // Call this last to notify the add-ons.
      this._handleValue(inputElement);
    },

    _onIronInputValidate: function(event) {
      this.invalid = this._inputElement.invalid;
    },

    _invalidChanged: function() {
      if (this._addons) {
        this.updateAddons({invalid: this.invalid});
      }
    },

    /**
     * Call this to update the state of add-ons.
     * @param {Object} state Add-on state.
     */
    updateAddons: function(state) {
      for (var addon, index = 0; addon = this._addons[index]; index++) {
        addon.update(state);
      }
    },

    _computeInputContentClass: function(noLabelFloat, alwaysFloatLabel, focused, invalid, _inputHasContent) {
      var cls = 'input-content';
      if (!noLabelFloat) {
        var label = this.querySelector('label');

        if (alwaysFloatLabel || _inputHasContent) {
          cls += ' label-is-floating';
          // If the label is floating, ignore any offsets that may have been
          // applied from a prefix element.
          this.$.labelAndInputContainer.style.position = 'static';

          if (invalid) {
            cls += ' is-invalid';
          } else if (focused) {
            cls += " label-is-highlighted";
          }
        } else {
          // When the label is not floating, it should overlap the input element.
          if (label) {
            this.$.labelAndInputContainer.style.position = 'relative';
          }
        }
      } else {
        if (_inputHasContent) {
          cls += ' label-is-hidden';
        }
      }
      return cls;
    },

    _computeUnderlineClass: function(focused, invalid) {
      var cls = 'underline';
      if (invalid) {
        cls += ' is-invalid';
      } else if (focused) {
        cls += ' is-highlighted'
      }
      return cls;
    },

    _computeAddOnContentClass: function(focused, invalid) {
      var cls = 'add-on-content';
      if (invalid) {
        cls += ' is-invalid';
      } else if (focused) {
        cls += ' is-highlighted'
      }
      return cls;
    }
  });
Polymer({
    is: 'paper-input-error',

    behaviors: [
      Polymer.PaperInputAddonBehavior
    ],

    properties: {
      /**
       * True if the error is showing.
       */
      invalid: {
        readOnly: true,
        reflectToAttribute: true,
        type: Boolean
      }
    },

    /**
     * This overrides the update function in PaperInputAddonBehavior.
     * @param {{
     *   inputElement: (Element|undefined),
     *   value: (string|undefined),
     *   invalid: boolean
     * }} state -
     *     inputElement: The input element.
     *     value: The input value.
     *     invalid: True if the input value is invalid.
     */
    update: function(state) {
      this._setInvalid(state.invalid);
    }
  });
Polymer({
    is: 'paper-input',

    behaviors: [
      Polymer.IronFormElementBehavior,
      Polymer.PaperInputBehavior
    ]
  });
/** @polymerBehavior Polymer.PaperItemBehavior */
  Polymer.PaperItemBehaviorImpl = {
    hostAttributes: {
      role: 'option',
      tabindex: '0'
    }
  };

  /** @polymerBehavior */
  Polymer.PaperItemBehavior = [
    Polymer.IronButtonState,
    Polymer.IronControlState,
    Polymer.PaperItemBehaviorImpl
  ];
Polymer({
      is: 'paper-item',

      behaviors: [
        Polymer.PaperItemBehavior
      ]
    });
/**
`Polymer.IronFitBehavior` fits an element in another element using `max-height` and `max-width`, and
optionally centers it in the window or another element.

The element will only be sized and/or positioned if it has not already been sized and/or positioned
by CSS.

CSS properties               | Action
-----------------------------|-------------------------------------------
`position` set               | Element is not centered horizontally or vertically
`top` or `bottom` set        | Element is not vertically centered
`left` or `right` set        | Element is not horizontally centered
`max-height` set             | Element respects `max-height`
`max-width` set              | Element respects `max-width`

`Polymer.IronFitBehavior` can position an element into another element using
`verticalAlign` and `horizontalAlign`. This will override the element's css position.

      <div class="container">
        <iron-fit-impl vertical-align="top" horizontal-align="auto">
          Positioned into the container
        </iron-fit-impl>
      </div>

Use `noOverlap` to position the element around another element without overlapping it.

      <div class="container">
        <iron-fit-impl no-overlap vertical-align="auto" horizontal-align="auto">
          Positioned around the container
        </iron-fit-impl>
      </div>

Use `horizontalOffset, verticalOffset` to offset the element from its `positionTarget`;
`Polymer.IronFitBehavior` will collapse these in order to keep the element
within `fitInto` boundaries, while preserving the element's CSS margin values.

      <div class="container">
        <iron-fit-impl vertical-align="top" vertical-offset="20">
          With vertical offset
        </iron-fit-impl>
      </div>


@demo demo/index.html
@polymerBehavior
*/

  Polymer.IronFitBehavior = {

    properties: {

      /**
       * The element that will receive a `max-height`/`width`. By default it is the same as `this`,
       * but it can be set to a child element. This is useful, for example, for implementing a
       * scrolling region inside the element.
       * @type {!Element}
       */
      sizingTarget: {
        type: Object,
        value: function() {
          return this;
        }
      },

      /**
       * The element to fit `this` into.
       */
      fitInto: {
        type: Object,
        value: window
      },

      /**
       * Will position the element around the positionTarget without overlapping it.
       */
      noOverlap: {
        type: Boolean
      },

      /**
       * The element that should be used to position the element. If not set, it will
       * default to the parent node.
       * @type {!Element}
       */
      positionTarget: {
        type: Element
      },

      /**
       * The orientation against which to align the element horizontally
       * relative to the `positionTarget`. Possible values are "left", "right", "auto".
       */
      horizontalAlign: {
        type: String
      },

      /**
       * The orientation against which to align the element vertically
       * relative to the `positionTarget`. Possible values are "top", "bottom", "auto".
       */
      verticalAlign: {
        type: String
      },

      /**
       * If true, it will use `horizontalAlign` and `verticalAlign` values as preferred alignment
       * and if there's not enough space, it will pick the values which minimize the cropping.
       */
      dynamicAlign: {
        type: Boolean
      },

      /**
       * A pixel value that will be added to the position calculated for the
       * given `horizontalAlign`, in the direction of alignment. You can think
       * of it as increasing or decreasing the distance to the side of the
       * screen given by `horizontalAlign`.
       *
       * If `horizontalAlign` is "left", this offset will increase or decrease
       * the distance to the left side of the screen: a negative offset will
       * move the dropdown to the left; a positive one, to the right.
       *
       * Conversely if `horizontalAlign` is "right", this offset will increase
       * or decrease the distance to the right side of the screen: a negative
       * offset will move the dropdown to the right; a positive one, to the left.
       */
      horizontalOffset: {
        type: Number,
        value: 0,
        notify: true
      },

      /**
       * A pixel value that will be added to the position calculated for the
       * given `verticalAlign`, in the direction of alignment. You can think
       * of it as increasing or decreasing the distance to the side of the
       * screen given by `verticalAlign`.
       *
       * If `verticalAlign` is "top", this offset will increase or decrease
       * the distance to the top side of the screen: a negative offset will
       * move the dropdown upwards; a positive one, downwards.
       *
       * Conversely if `verticalAlign` is "bottom", this offset will increase
       * or decrease the distance to the bottom side of the screen: a negative
       * offset will move the dropdown downwards; a positive one, upwards.
       */
      verticalOffset: {
        type: Number,
        value: 0,
        notify: true
      },

      /**
       * Set to true to auto-fit on attach.
       */
      autoFitOnAttach: {
        type: Boolean,
        value: false
      },

      /** @type {?Object} */
      _fitInfo: {
        type: Object
      }
    },

    get _fitWidth() {
      var fitWidth;
      if (this.fitInto === window) {
        fitWidth = this.fitInto.innerWidth;
      } else {
        fitWidth = this.fitInto.getBoundingClientRect().width;
      }
      return fitWidth;
    },

    get _fitHeight() {
      var fitHeight;
      if (this.fitInto === window) {
        fitHeight = this.fitInto.innerHeight;
      } else {
        fitHeight = this.fitInto.getBoundingClientRect().height;
      }
      return fitHeight;
    },

    get _fitLeft() {
      var fitLeft;
      if (this.fitInto === window) {
        fitLeft = 0;
      } else {
        fitLeft = this.fitInto.getBoundingClientRect().left;
      }
      return fitLeft;
    },

    get _fitTop() {
      var fitTop;
      if (this.fitInto === window) {
        fitTop = 0;
      } else {
        fitTop = this.fitInto.getBoundingClientRect().top;
      }
      return fitTop;
    },

    /**
     * The element that should be used to position the element,
     * if no position target is configured.
     */
    get _defaultPositionTarget() {
      var parent = Polymer.dom(this).parentNode;

      if (parent && parent.nodeType === Node.DOCUMENT_FRAGMENT_NODE) {
        parent = parent.host;
      }

      return parent;
    },

    /**
     * The horizontal align value, accounting for the RTL/LTR text direction.
     */
    get _localeHorizontalAlign() {
      if (this._isRTL) {
        // In RTL, "left" becomes "right".
        if (this.horizontalAlign === 'right') {
          return 'left';
        }
        if (this.horizontalAlign === 'left') {
          return 'right';
        }
      }
      return this.horizontalAlign;
    },

    attached: function() {
      // Memoize this to avoid expensive calculations & relayouts.
      // Make sure we do it only once
      if (typeof this._isRTL === 'undefined') {
        this._isRTL = window.getComputedStyle(this).direction == 'rtl';
      }
          
      this.positionTarget = this.positionTarget || this._defaultPositionTarget;
      if (this.autoFitOnAttach) {
        if (window.getComputedStyle(this).display === 'none') {
          setTimeout(function() {
            this.fit();
          }.bind(this));
        } else {
          this.fit();
        }
      }
    },

    /**
     * Positions and fits the element into the `fitInto` element.
     */
    fit: function() {
      this.position();
      this.constrain();
      this.center();
    },

    /**
     * Memoize information needed to position and size the target element.
     * @suppress {deprecated}
     */
    _discoverInfo: function() {
      if (this._fitInfo) {
        return;
      }
      var target = window.getComputedStyle(this);
      var sizer = window.getComputedStyle(this.sizingTarget);

      this._fitInfo = {
        inlineStyle: {
          top: this.style.top || '',
          left: this.style.left || '',
          position: this.style.position || ''
        },
        sizerInlineStyle: {
          maxWidth: this.sizingTarget.style.maxWidth || '',
          maxHeight: this.sizingTarget.style.maxHeight || '',
          boxSizing: this.sizingTarget.style.boxSizing || ''
        },
        positionedBy: {
          vertically: target.top !== 'auto' ? 'top' : (target.bottom !== 'auto' ?
            'bottom' : null),
          horizontally: target.left !== 'auto' ? 'left' : (target.right !== 'auto' ?
            'right' : null)
        },
        sizedBy: {
          height: sizer.maxHeight !== 'none',
          width: sizer.maxWidth !== 'none',
          minWidth: parseInt(sizer.minWidth, 10) || 0,
          minHeight: parseInt(sizer.minHeight, 10) || 0
        },
        margin: {
          top: parseInt(target.marginTop, 10) || 0,
          right: parseInt(target.marginRight, 10) || 0,
          bottom: parseInt(target.marginBottom, 10) || 0,
          left: parseInt(target.marginLeft, 10) || 0
        }
      };
    },

    /**
     * Resets the target element's position and size constraints, and clear
     * the memoized data.
     */
    resetFit: function() {
      var info = this._fitInfo || {};
      for (var property in info.sizerInlineStyle) {
        this.sizingTarget.style[property] = info.sizerInlineStyle[property];
      }
      for (var property in info.inlineStyle) {
        this.style[property] = info.inlineStyle[property];
      }

      this._fitInfo = null;
    },

    /**
     * Equivalent to calling `resetFit()` and `fit()`. Useful to call this after
     * the element or the `fitInto` element has been resized, or if any of the
     * positioning properties (e.g. `horizontalAlign, verticalAlign`) is updated.
     * It preserves the scroll position of the sizingTarget.
     */
    refit: function() {
      var scrollLeft = this.sizingTarget.scrollLeft;
      var scrollTop = this.sizingTarget.scrollTop;
      this.resetFit();
      this.fit();
      this.sizingTarget.scrollLeft = scrollLeft;
      this.sizingTarget.scrollTop = scrollTop;
    },

    /**
     * Positions the element according to `horizontalAlign, verticalAlign`.
     */
    position: function() {
      if (!this.horizontalAlign && !this.verticalAlign) {
        // needs to be centered, and it is done after constrain.
        return;
      }
      this._discoverInfo();

      this.style.position = 'fixed';
      // Need border-box for margin/padding.
      this.sizingTarget.style.boxSizing = 'border-box';
      // Set to 0, 0 in order to discover any offset caused by parent stacking contexts.
      this.style.left = '0px';
      this.style.top = '0px';

      var rect = this.getBoundingClientRect();
      var positionRect = this.__getNormalizedRect(this.positionTarget);
      var fitRect = this.__getNormalizedRect(this.fitInto);

      var margin = this._fitInfo.margin;

      // Consider the margin as part of the size for position calculations.
      var size = {
        width: rect.width + margin.left + margin.right,
        height: rect.height + margin.top + margin.bottom
      };

      var position = this.__getPosition(this._localeHorizontalAlign, this.verticalAlign, size, positionRect, fitRect);

      var left = position.left + margin.left;
      var top = position.top + margin.top;

      // We first limit right/bottom within fitInto respecting the margin,
      // then use those values to limit top/left.
      var right = Math.min(fitRect.right - margin.right, left + rect.width);
      var bottom = Math.min(fitRect.bottom - margin.bottom, top + rect.height);

      // Keep left/top within fitInto respecting the margin.
      left = Math.max(fitRect.left + margin.left,
        Math.min(left, right - this._fitInfo.sizedBy.minWidth));
      top = Math.max(fitRect.top + margin.top,
        Math.min(top, bottom - this._fitInfo.sizedBy.minHeight));

      // Use right/bottom to set maxWidth/maxHeight, and respect minWidth/minHeight.
      this.sizingTarget.style.maxWidth = Math.max(right - left, this._fitInfo.sizedBy.minWidth) + 'px';
      this.sizingTarget.style.maxHeight = Math.max(bottom - top, this._fitInfo.sizedBy.minHeight) + 'px';

      // Remove the offset caused by any stacking context.
      this.style.left = (left - rect.left) + 'px';
      this.style.top = (top - rect.top) + 'px';
    },

    /**
     * Constrains the size of the element to `fitInto` by setting `max-height`
     * and/or `max-width`.
     */
    constrain: function() {
      if (this.horizontalAlign || this.verticalAlign) {
        return;
      }
      this._discoverInfo();

      var info = this._fitInfo;
      // position at (0px, 0px) if not already positioned, so we can measure the natural size.
      if (!info.positionedBy.vertically) {
        this.style.position = 'fixed';
        this.style.top = '0px';
      }
      if (!info.positionedBy.horizontally) {
        this.style.position = 'fixed';
        this.style.left = '0px';
      }

      // need border-box for margin/padding
      this.sizingTarget.style.boxSizing = 'border-box';
      // constrain the width and height if not already set
      var rect = this.getBoundingClientRect();
      if (!info.sizedBy.height) {
        this.__sizeDimension(rect, info.positionedBy.vertically, 'top', 'bottom', 'Height');
      }
      if (!info.sizedBy.width) {
        this.__sizeDimension(rect, info.positionedBy.horizontally, 'left', 'right', 'Width');
      }
    },

    /**
     * @protected
     * @deprecated
     */
    _sizeDimension: function(rect, positionedBy, start, end, extent) {
      this.__sizeDimension(rect, positionedBy, start, end, extent);
    },

    /**
     * @private
     */
    __sizeDimension: function(rect, positionedBy, start, end, extent) {
      var info = this._fitInfo;
      var fitRect = this.__getNormalizedRect(this.fitInto);
      var max = extent === 'Width' ? fitRect.width : fitRect.height;
      var flip = (positionedBy === end);
      var offset = flip ? max - rect[end] : rect[start];
      var margin = info.margin[flip ? start : end];
      var offsetExtent = 'offset' + extent;
      var sizingOffset = this[offsetExtent] - this.sizingTarget[offsetExtent];
      this.sizingTarget.style['max' + extent] = (max - margin - offset - sizingOffset) + 'px';
    },

    /**
     * Centers horizontally and vertically if not already positioned. This also sets
     * `position:fixed`.
     */
    center: function() {
      if (this.horizontalAlign || this.verticalAlign) {
        return;
      }
      this._discoverInfo();

      var positionedBy = this._fitInfo.positionedBy;
      if (positionedBy.vertically && positionedBy.horizontally) {
        // Already positioned.
        return;
      }
      // Need position:fixed to center
      this.style.position = 'fixed';
      // Take into account the offset caused by parents that create stacking
      // contexts (e.g. with transform: translate3d). Translate to 0,0 and
      // measure the bounding rect.
      if (!positionedBy.vertically) {
        this.style.top = '0px';
      }
      if (!positionedBy.horizontally) {
        this.style.left = '0px';
      }
      // It will take in consideration margins and transforms
      var rect = this.getBoundingClientRect();
      var fitRect = this.__getNormalizedRect(this.fitInto);
      if (!positionedBy.vertically) {
        var top = fitRect.top - rect.top + (fitRect.height - rect.height) / 2;
        this.style.top = top + 'px';
      }
      if (!positionedBy.horizontally) {
        var left = fitRect.left - rect.left + (fitRect.width - rect.width) / 2;
        this.style.left = left + 'px';
      }
    },

    __getNormalizedRect: function(target) {
      if (target === document.documentElement || target === window) {
        return {
          top: 0,
          left: 0,
          width: window.innerWidth,
          height: window.innerHeight,
          right: window.innerWidth,
          bottom: window.innerHeight
        };
      }
      return target.getBoundingClientRect();
    },

    __getCroppedArea: function(position, size, fitRect) {
      var verticalCrop = Math.min(0, position.top) + Math.min(0, fitRect.bottom - (position.top + size.height));
      var horizontalCrop = Math.min(0, position.left) + Math.min(0, fitRect.right - (position.left + size.width));
      return Math.abs(verticalCrop) * size.width + Math.abs(horizontalCrop) * size.height;
    },


    __getPosition: function(hAlign, vAlign, size, positionRect, fitRect) {
      // All the possible configurations.
      // Ordered as top-left, top-right, bottom-left, bottom-right.
      var positions = [{
        verticalAlign: 'top',
        horizontalAlign: 'left',
        top: positionRect.top + this.verticalOffset,
        left: positionRect.left + this.horizontalOffset
      }, {
        verticalAlign: 'top',
        horizontalAlign: 'right',
        top: positionRect.top + this.verticalOffset,
        left: positionRect.right - size.width - this.horizontalOffset
      }, {
        verticalAlign: 'bottom',
        horizontalAlign: 'left',
        top: positionRect.bottom - size.height - this.verticalOffset,
        left: positionRect.left + this.horizontalOffset
      }, {
        verticalAlign: 'bottom',
        horizontalAlign: 'right',
        top: positionRect.bottom - size.height - this.verticalOffset,
        left: positionRect.right - size.width - this.horizontalOffset
      }];

      if (this.noOverlap) {
        // Duplicate.
        for (var i = 0, l = positions.length; i < l; i++) {
          var copy = {};
          for (var key in positions[i]) {
            copy[key] = positions[i][key];
          }
          positions.push(copy);
        }
        // Horizontal overlap only.
        positions[0].top = positions[1].top += positionRect.height;
        positions[2].top = positions[3].top -= positionRect.height;
        // Vertical overlap only.
        positions[4].left = positions[6].left += positionRect.width;
        positions[5].left = positions[7].left -= positionRect.width;
      }

      // Consider auto as null for coding convenience.
      vAlign = vAlign === 'auto' ? null : vAlign;
      hAlign = hAlign === 'auto' ? null : hAlign;

      var position;
      for (var i = 0; i < positions.length; i++) {
        var pos = positions[i];

        // If both vAlign and hAlign are defined, return exact match.
        // For dynamicAlign and noOverlap we'll have more than one candidate, so
        // we'll have to check the croppedArea to make the best choice.
        if (!this.dynamicAlign && !this.noOverlap &&
            pos.verticalAlign === vAlign && pos.horizontalAlign === hAlign) {
          position = pos;
          break;
        }

        // Align is ok if alignment preferences are respected. If no preferences,
        // it is considered ok.
        var alignOk = (!vAlign || pos.verticalAlign === vAlign) &&
                      (!hAlign || pos.horizontalAlign === hAlign);

        // Filter out elements that don't match the alignment (if defined).
        // With dynamicAlign, we need to consider all the positions to find the
        // one that minimizes the cropped area.
        if (!this.dynamicAlign && !alignOk) {
          continue;
        }

        position = position || pos;
        pos.croppedArea = this.__getCroppedArea(pos, size, fitRect);
        var diff = pos.croppedArea - position.croppedArea;
        // Check which crops less. If it crops equally, check if align is ok.
        if (diff < 0 || (diff === 0 && alignOk)) {
          position = pos;
        }
        // If not cropped and respects the align requirements, keep it.
        // This allows to prefer positions overlapping horizontally over the
        // ones overlapping vertically.
        if (position.croppedArea === 0 && alignOk) {
          break;
        }
      }

      return position;
    }

  };
(function() {
'use strict';

  Polymer({

    is: 'iron-overlay-backdrop',

    properties: {

      /**
       * Returns true if the backdrop is opened.
       */
      opened: {
        reflectToAttribute: true,
        type: Boolean,
        value: false,
        observer: '_openedChanged'
      }

    },

    listeners: {
      'transitionend': '_onTransitionend'
    },

    created: function() {
      // Used to cancel previous requestAnimationFrame calls when opened changes.
      this.__openedRaf = null;
    },

    attached: function() {
      this.opened && this._openedChanged(this.opened);
    },

    /**
     * Appends the backdrop to document body if needed.
     */
    prepare: function() {
      if (this.opened && !this.parentNode) {
        Polymer.dom(document.body).appendChild(this);
      }
    },

    /**
     * Shows the backdrop.
     */
    open: function() {
      this.opened = true;
    },

    /**
     * Hides the backdrop.
     */
    close: function() {
      this.opened = false;
    },

    /**
     * Removes the backdrop from document body if needed.
     */
    complete: function() {
      if (!this.opened && this.parentNode === document.body) {
        Polymer.dom(this.parentNode).removeChild(this);
      }
    },

    _onTransitionend: function(event) {
      if (event && event.target === this) {
        this.complete();
      }
    },

    /**
     * @param {boolean} opened
     * @private
     */
    _openedChanged: function(opened) {
      if (opened) {
        // Auto-attach.
        this.prepare();
      } else {
        // Animation might be disabled via the mixin or opacity custom property.
        // If it is disabled in other ways, it's up to the user to call complete.
        var cs = window.getComputedStyle(this);
        if (cs.transitionDuration === '0s' || cs.opacity == 0) {
          this.complete();
        }
      }

      if (!this.isAttached) {
        return;
      }

      // Always cancel previous requestAnimationFrame.
      if (this.__openedRaf) {
        window.cancelAnimationFrame(this.__openedRaf);
        this.__openedRaf = null;
      }
      // Force relayout to ensure proper transitions.
      this.scrollTop = this.scrollTop;
      this.__openedRaf = window.requestAnimationFrame(function() {
        this.__openedRaf = null;
        this.toggleClass('opened', this.opened);
      }.bind(this));
    }
  });

})();
/**
   * @struct
   * @constructor
   * @private
   */
  Polymer.IronOverlayManagerClass = function() {
    /**
     * Used to keep track of the opened overlays.
     * @private {Array<Element>}
     */
    this._overlays = [];

    /**
     * iframes have a default z-index of 100,
     * so this default should be at least that.
     * @private {number}
     */
    this._minimumZ = 101;

    /**
     * Memoized backdrop element.
     * @private {Element|null}
     */
    this._backdropElement = null;

    // Enable document-wide tap recognizer.
    // NOTE: Use useCapture=true to avoid accidentally prevention of the closing
    // of an overlay via event.stopPropagation(). The only way to prevent
    // closing of an overlay should be through its APIs.
    Polymer.Gestures.add(document, 'tap', null);
    document.addEventListener('tap', this._onCaptureClick.bind(this), true);
    document.addEventListener('focus', this._onCaptureFocus.bind(this), true);
    document.addEventListener('keydown', this._onCaptureKeyDown.bind(this), true);
  };

  Polymer.IronOverlayManagerClass.prototype = {

    constructor: Polymer.IronOverlayManagerClass,

    /**
     * The shared backdrop element.
     * @type {!Element} backdropElement
     */
    get backdropElement() {
      if (!this._backdropElement) {
        this._backdropElement = document.createElement('iron-overlay-backdrop');
      }
      return this._backdropElement;
    },

    /**
     * The deepest active element.
     * @type {!Element} activeElement the active element
     */
    get deepActiveElement() {
      // document.activeElement can be null
      // https://developer.mozilla.org/en-US/docs/Web/API/Document/activeElement
      // In case of null, default it to document.body.
      var active = document.activeElement || document.body;
      while (active.root && Polymer.dom(active.root).activeElement) {
        active = Polymer.dom(active.root).activeElement;
      }
      return active;
    },

    /**
     * Brings the overlay at the specified index to the front.
     * @param {number} i
     * @private
     */
    _bringOverlayAtIndexToFront: function(i) {
      var overlay = this._overlays[i];
      if (!overlay) {
        return;
      }
      var lastI = this._overlays.length - 1;
      var currentOverlay = this._overlays[lastI];
      // Ensure always-on-top overlay stays on top.
      if (currentOverlay && this._shouldBeBehindOverlay(overlay, currentOverlay)) {
        lastI--;
      }
      // If already the top element, return.
      if (i >= lastI) {
        return;
      }
      // Update z-index to be on top.
      var minimumZ = Math.max(this.currentOverlayZ(), this._minimumZ);
      if (this._getZ(overlay) <= minimumZ) {
        this._applyOverlayZ(overlay, minimumZ);
      }

      // Shift other overlays behind the new on top.
      while (i < lastI) {
        this._overlays[i] = this._overlays[i + 1];
        i++;
      }
      this._overlays[lastI] = overlay;
    },

    /**
     * Adds the overlay and updates its z-index if it's opened, or removes it if it's closed.
     * Also updates the backdrop z-index.
     * @param {!Element} overlay
     */
    addOrRemoveOverlay: function(overlay) {
      if (overlay.opened) {
        this.addOverlay(overlay);
      } else {
        this.removeOverlay(overlay);
      }
    },

    /**
     * Tracks overlays for z-index and focus management.
     * Ensures the last added overlay with always-on-top remains on top.
     * @param {!Element} overlay
     */
    addOverlay: function(overlay) {
      var i = this._overlays.indexOf(overlay);
      if (i >= 0) {
        this._bringOverlayAtIndexToFront(i);
        this.trackBackdrop();
        return;
      }
      var insertionIndex = this._overlays.length;
      var currentOverlay = this._overlays[insertionIndex - 1];
      var minimumZ = Math.max(this._getZ(currentOverlay), this._minimumZ);
      var newZ = this._getZ(overlay);

      // Ensure always-on-top overlay stays on top.
      if (currentOverlay && this._shouldBeBehindOverlay(overlay, currentOverlay)) {
        // This bumps the z-index of +2.
        this._applyOverlayZ(currentOverlay, minimumZ);
        insertionIndex--;
        // Update minimumZ to match previous overlay's z-index.
        var previousOverlay = this._overlays[insertionIndex - 1];
        minimumZ = Math.max(this._getZ(previousOverlay), this._minimumZ);
      }

      // Update z-index and insert overlay.
      if (newZ <= minimumZ) {
        this._applyOverlayZ(overlay, minimumZ);
      }
      this._overlays.splice(insertionIndex, 0, overlay);

      this.trackBackdrop();
    },

    /**
     * @param {!Element} overlay
     */
    removeOverlay: function(overlay) {
      var i = this._overlays.indexOf(overlay);
      if (i === -1) {
        return;
      }
      this._overlays.splice(i, 1);

      this.trackBackdrop();
    },

    /**
     * Returns the current overlay.
     * @return {Element|undefined}
     */
    currentOverlay: function() {
      var i = this._overlays.length - 1;
      return this._overlays[i];
    },

    /**
     * Returns the current overlay z-index.
     * @return {number}
     */
    currentOverlayZ: function() {
      return this._getZ(this.currentOverlay());
    },

    /**
     * Ensures that the minimum z-index of new overlays is at least `minimumZ`.
     * This does not effect the z-index of any existing overlays.
     * @param {number} minimumZ
     */
    ensureMinimumZ: function(minimumZ) {
      this._minimumZ = Math.max(this._minimumZ, minimumZ);
    },

    focusOverlay: function() {
      var current = /** @type {?} */ (this.currentOverlay());
      if (current) {
        current._applyFocus();
      }
    },

    /**
     * Updates the backdrop z-index.
     */
    trackBackdrop: function() {
      var overlay = this._overlayWithBackdrop();
      // Avoid creating the backdrop if there is no overlay with backdrop.
      if (!overlay && !this._backdropElement) {
        return;
      }
      this.backdropElement.style.zIndex = this._getZ(overlay) - 1;
      this.backdropElement.opened = !!overlay;
    },

    /**
     * @return {Array<Element>}
     */
    getBackdrops: function() {
      var backdrops = [];
      for (var i = 0; i < this._overlays.length; i++) {
        if (this._overlays[i].withBackdrop) {
          backdrops.push(this._overlays[i]);
        }
      }
      return backdrops;
    },

    /**
     * Returns the z-index for the backdrop.
     * @return {number}
     */
    backdropZ: function() {
      return this._getZ(this._overlayWithBackdrop()) - 1;
    },

    /**
     * Returns the first opened overlay that has a backdrop.
     * @return {Element|undefined}
     * @private
     */
    _overlayWithBackdrop: function() {
      for (var i = 0; i < this._overlays.length; i++) {
        if (this._overlays[i].withBackdrop) {
          return this._overlays[i];
        }
      }
    },

    /**
     * Calculates the minimum z-index for the overlay.
     * @param {Element=} overlay
     * @private
     */
    _getZ: function(overlay) {
      var z = this._minimumZ;
      if (overlay) {
        var z1 = Number(overlay.style.zIndex || window.getComputedStyle(overlay).zIndex);
        // Check if is a number
        // Number.isNaN not supported in IE 10+
        if (z1 === z1) {
          z = z1;
        }
      }
      return z;
    },

    /**
     * @param {!Element} element
     * @param {number|string} z
     * @private
     */
    _setZ: function(element, z) {
      element.style.zIndex = z;
    },

    /**
     * @param {!Element} overlay
     * @param {number} aboveZ
     * @private
     */
    _applyOverlayZ: function(overlay, aboveZ) {
      this._setZ(overlay, aboveZ + 2);
    },

    /**
     * Returns the deepest overlay in the path.
     * @param {Array<Element>=} path
     * @return {Element|undefined}
     * @suppress {missingProperties}
     * @private
     */
    _overlayInPath: function(path) {
      path = path || [];
      for (var i = 0; i < path.length; i++) {
        if (path[i]._manager === this) {
          return path[i];
        }
      }
    },

    /**
     * Ensures the click event is delegated to the right overlay.
     * @param {!Event} event
     * @private
     */
    _onCaptureClick: function(event) {
      var overlay = /** @type {?} */ (this.currentOverlay());
      // Check if clicked outside of top overlay.
      if (overlay && this._overlayInPath(Polymer.dom(event).path) !== overlay) {
        overlay._onCaptureClick(event);
      }
    },

    /**
     * Ensures the focus event is delegated to the right overlay.
     * @param {!Event} event
     * @private
     */
    _onCaptureFocus: function(event) {
      var overlay = /** @type {?} */ (this.currentOverlay());
      if (overlay) {
        overlay._onCaptureFocus(event);
      }
    },

    /**
     * Ensures TAB and ESC keyboard events are delegated to the right overlay.
     * @param {!Event} event
     * @private
     */
    _onCaptureKeyDown: function(event) {
      var overlay = /** @type {?} */ (this.currentOverlay());
      if (overlay) {
        if (Polymer.IronA11yKeysBehavior.keyboardEventMatchesKeys(event, 'esc')) {
          overlay._onCaptureEsc(event);
        } else if (Polymer.IronA11yKeysBehavior.keyboardEventMatchesKeys(event, 'tab')) {
          overlay._onCaptureTab(event);
        }
      }
    },

    /**
     * Returns if the overlay1 should be behind overlay2.
     * @param {!Element} overlay1
     * @param {!Element} overlay2
     * @return {boolean}
     * @suppress {missingProperties}
     * @private
     */
    _shouldBeBehindOverlay: function(overlay1, overlay2) {
      return !overlay1.alwaysOnTop && overlay2.alwaysOnTop;
    }
  };

  Polymer.IronOverlayManager = new Polymer.IronOverlayManagerClass();
(function() {
    'use strict';

    var p = Element.prototype;
    var matches = p.matches || p.matchesSelector || p.mozMatchesSelector ||
      p.msMatchesSelector || p.oMatchesSelector || p.webkitMatchesSelector;

    Polymer.IronFocusablesHelper = {

      /**
       * Returns a sorted array of tabbable nodes, including the root node.
       * It searches the tabbable nodes in the light and shadow dom of the chidren,
       * sorting the result by tabindex.
       * @param {!Node} node
       * @return {Array<HTMLElement>}
       */
      getTabbableNodes: function(node) {
        var result = [];
        // If there is at least one element with tabindex > 0, we need to sort
        // the final array by tabindex.
        var needsSortByTabIndex = this._collectTabbableNodes(node, result);
        if (needsSortByTabIndex) {
          return this._sortByTabIndex(result);
        }
        return result;
      },

      /**
       * Returns if a element is focusable.
       * @param {!HTMLElement} element
       * @return {boolean}
       */
      isFocusable: function(element) {
        // From http://stackoverflow.com/a/1600194/4228703:
        // There isn't a definite list, it's up to the browser. The only
        // standard we have is DOM Level 2 HTML https://www.w3.org/TR/DOM-Level-2-HTML/html.html,
        // according to which the only elements that have a focus() method are
        // HTMLInputElement,  HTMLSelectElement, HTMLTextAreaElement and
        // HTMLAnchorElement. This notably omits HTMLButtonElement and
        // HTMLAreaElement.
        // Referring to these tests with tabbables in different browsers
        // http://allyjs.io/data-tables/focusable.html

        // Elements that cannot be focused if they have [disabled] attribute.
        if (matches.call(element, 'input, select, textarea, button, object')) {
          return matches.call(element, ':not([disabled])');
        }
        // Elements that can be focused even if they have [disabled] attribute.
        return matches.call(element,
          'a[href], area[href], iframe, [tabindex], [contentEditable]');
      },

      /**
       * Returns if a element is tabbable. To be tabbable, a element must be
       * focusable, visible, and with a tabindex !== -1.
       * @param {!HTMLElement} element
       * @return {boolean}
       */
      isTabbable: function(element) {
        return this.isFocusable(element) &&
          matches.call(element, ':not([tabindex="-1"])') &&
          this._isVisible(element);
      },

      /**
       * Returns the normalized element tabindex. If not focusable, returns -1.
       * It checks for the attribute "tabindex" instead of the element property
       * `tabIndex` since browsers assign different values to it.
       * e.g. in Firefox `<div contenteditable>` has `tabIndex = -1`
       * @param {!HTMLElement} element
       * @return {!number}
       * @private
       */
      _normalizedTabIndex: function(element) {
        if (this.isFocusable(element)) {
          var tabIndex = element.getAttribute('tabindex') || 0;
          return Number(tabIndex);
        }
        return -1;
      },

      /**
       * Searches for nodes that are tabbable and adds them to the `result` array.
       * Returns if the `result` array needs to be sorted by tabindex.
       * @param {!Node} node The starting point for the search; added to `result`
       * if tabbable.
       * @param {!Array<HTMLElement>} result
       * @return {boolean}
       * @private
       */
      _collectTabbableNodes: function(node, result) {
        // If not an element or not visible, no need to explore children.
        if (node.nodeType !== Node.ELEMENT_NODE || !this._isVisible(node)) {
          return false;
        }
        var element = /** @type {HTMLElement} */ (node);
        var tabIndex = this._normalizedTabIndex(element);
        var needsSortByTabIndex = tabIndex > 0;
        if (tabIndex >= 0) {
          result.push(element);
        }

        // In ShadowDOM v1, tab order is affected by the order of distrubution.
        // E.g. getTabbableNodes(#root) in ShadowDOM v1 should return [#A, #B];
        // in ShadowDOM v0 tab order is not affected by the distrubution order,
        // in fact getTabbableNodes(#root) returns [#B, #A].
        //  <div id="root">
        //   <!-- shadow -->
        //     <slot name="a">
        //     <slot name="b">
        //   <!-- /shadow -->
        //   <input id="A" slot="a">
        //   <input id="B" slot="b" tabindex="1">
        //  </div>
        // TODO(valdrin) support ShadowDOM v1 when upgrading to Polymer v2.0.
        var children;
        if (element.localName === 'content') {
          children = Polymer.dom(element).getDistributedNodes();
        } else {
          // Use shadow root if possible, will check for distributed nodes.
          children = Polymer.dom(element.root || element).children;
        }
        for (var i = 0; i < children.length; i++) {
          // Ensure method is always invoked to collect tabbable children.
          var needsSort = this._collectTabbableNodes(children[i], result);
          needsSortByTabIndex = needsSortByTabIndex || needsSort;
        }
        return needsSortByTabIndex;
      },

      /**
       * Returns false if the element has `visibility: hidden` or `display: none`
       * @param {!HTMLElement} element
       * @return {boolean}
       * @private
       */
      _isVisible: function(element) {
        // Check inline style first to save a re-flow. If looks good, check also
        // computed style.
        var style = element.style;
        if (style.visibility !== 'hidden' && style.display !== 'none') {
          style = window.getComputedStyle(element);
          return (style.visibility !== 'hidden' && style.display !== 'none');
        }
        return false;
      },

      /**
       * Sorts an array of tabbable elements by tabindex. Returns a new array.
       * @param {!Array<HTMLElement>} tabbables
       * @return {Array<HTMLElement>}
       * @private
       */
      _sortByTabIndex: function(tabbables) {
        // Implement a merge sort as Array.prototype.sort does a non-stable sort
        // https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/sort
        var len = tabbables.length;
        if (len < 2) {
          return tabbables;
        }
        var pivot = Math.ceil(len / 2);
        var left = this._sortByTabIndex(tabbables.slice(0, pivot));
        var right = this._sortByTabIndex(tabbables.slice(pivot));
        return this._mergeSortByTabIndex(left, right);
      },

      /**
       * Merge sort iterator, merges the two arrays into one, sorted by tab index.
       * @param {!Array<HTMLElement>} left
       * @param {!Array<HTMLElement>} right
       * @return {Array<HTMLElement>}
       * @private
       */
      _mergeSortByTabIndex: function(left, right) {
        var result = [];
        while ((left.length > 0) && (right.length > 0)) {
          if (this._hasLowerTabOrder(left[0], right[0])) {
            result.push(right.shift());
          } else {
            result.push(left.shift());
          }
        }

        return result.concat(left, right);
      },

      /**
       * Returns if element `a` has lower tab order compared to element `b`
       * (both elements are assumed to be focusable and tabbable).
       * Elements with tabindex = 0 have lower tab order compared to elements
       * with tabindex > 0.
       * If both have same tabindex, it returns false.
       * @param {!HTMLElement} a
       * @param {!HTMLElement} b
       * @return {boolean}
       * @private
       */
      _hasLowerTabOrder: function(a, b) {
        // Normalize tabIndexes
        // e.g. in Firefox `<div contenteditable>` has `tabIndex = -1`
        var ati = Math.max(a.tabIndex, 0);
        var bti = Math.max(b.tabIndex, 0);
        return (ati === 0 || bti === 0) ? bti > ati : ati > bti;
      }
    };
  })();
(function() {
  'use strict';

  /** @polymerBehavior */
  Polymer.IronOverlayBehaviorImpl = {

    properties: {

      /**
       * True if the overlay is currently displayed.
       */
      opened: {
        observer: '_openedChanged',
        type: Boolean,
        value: false,
        notify: true
      },

      /**
       * True if the overlay was canceled when it was last closed.
       */
      canceled: {
        observer: '_canceledChanged',
        readOnly: true,
        type: Boolean,
        value: false
      },

      /**
       * Set to true to display a backdrop behind the overlay. It traps the focus
       * within the light DOM of the overlay.
       */
      withBackdrop: {
        observer: '_withBackdropChanged',
        type: Boolean
      },

      /**
       * Set to true to disable auto-focusing the overlay or child nodes with
       * the `autofocus` attribute` when the overlay is opened.
       */
      noAutoFocus: {
        type: Boolean,
        value: false
      },

      /**
       * Set to true to disable canceling the overlay with the ESC key.
       */
      noCancelOnEscKey: {
        type: Boolean,
        value: false
      },

      /**
       * Set to true to disable canceling the overlay by clicking outside it.
       */
      noCancelOnOutsideClick: {
        type: Boolean,
        value: false
      },

      /**
       * Contains the reason(s) this overlay was last closed (see `iron-overlay-closed`).
       * `IronOverlayBehavior` provides the `canceled` reason; implementers of the
       * behavior can provide other reasons in addition to `canceled`.
       */
      closingReason: {
        // was a getter before, but needs to be a property so other
        // behaviors can override this.
        type: Object
      },

      /**
       * Set to true to enable restoring of focus when overlay is closed.
       */
      restoreFocusOnClose: {
        type: Boolean,
        value: false
      },

      /**
       * Set to true to keep overlay always on top.
       */
      alwaysOnTop: {
        type: Boolean
      },

      /**
       * Shortcut to access to the overlay manager.
       * @private
       * @type {Polymer.IronOverlayManagerClass}
       */
      _manager: {
        type: Object,
        value: Polymer.IronOverlayManager
      },

      /**
       * The node being focused.
       * @type {?Node}
       */
      _focusedChild: {
        type: Object
      }

    },

    listeners: {
      'iron-resize': '_onIronResize'
    },

    /**
     * The backdrop element.
     * @type {Element}
     */
    get backdropElement() {
      return this._manager.backdropElement;
    },

    /**
     * Returns the node to give focus to.
     * @type {Node}
     */
    get _focusNode() {
      return this._focusedChild || Polymer.dom(this).querySelector('[autofocus]') || this;
    },

    /**
     * Array of nodes that can receive focus (overlay included), ordered by `tabindex`.
     * This is used to retrieve which is the first and last focusable nodes in order
     * to wrap the focus for overlays `with-backdrop`.
     *
     * If you know what is your content (specifically the first and last focusable children),
     * you can override this method to return only `[firstFocusable, lastFocusable];`
     * @type {Array<Node>}
     * @protected
     */
    get _focusableNodes() {
      return Polymer.IronFocusablesHelper.getTabbableNodes(this);
    },

    ready: function() {
      // Used to skip calls to notifyResize and refit while the overlay is animating.
      this.__isAnimating = false;
      // with-backdrop needs tabindex to be set in order to trap the focus.
      // If it is not set, IronOverlayBehavior will set it, and remove it if with-backdrop = false.
      this.__shouldRemoveTabIndex = false;
      // Used for wrapping the focus on TAB / Shift+TAB.
      this.__firstFocusableNode = this.__lastFocusableNode = null;
      // Used by __onNextAnimationFrame to cancel any previous callback.
      this.__raf = null;
      // Focused node before overlay gets opened. Can be restored on close.
      this.__restoreFocusNode = null;
      this._ensureSetup();
    },

    attached: function() {
      // Call _openedChanged here so that position can be computed correctly.
      if (this.opened) {
        this._openedChanged(this.opened);
      }
      this._observer = Polymer.dom(this).observeNodes(this._onNodesChange);
    },

    detached: function() {
      Polymer.dom(this).unobserveNodes(this._observer);
      this._observer = null;
      if (this.__raf) {
        window.cancelAnimationFrame(this.__raf);
        this.__raf = null;
      }
      this._manager.removeOverlay(this);
    },

    /**
     * Toggle the opened state of the overlay.
     */
    toggle: function() {
      this._setCanceled(false);
      this.opened = !this.opened;
    },

    /**
     * Open the overlay.
     */
    open: function() {
      this._setCanceled(false);
      this.opened = true;
    },

    /**
     * Close the overlay.
     */
    close: function() {
      this._setCanceled(false);
      this.opened = false;
    },

    /**
     * Cancels the overlay.
     * @param {Event=} event The original event
     */
    cancel: function(event) {
      var cancelEvent = this.fire('iron-overlay-canceled', event, {cancelable: true});
      if (cancelEvent.defaultPrevented) {
        return;
      }

      this._setCanceled(true);
      this.opened = false;
    },

    /**
     * Invalidates the cached tabbable nodes. To be called when any of the focusable
     * content changes (e.g. a button is disabled).
     */
    invalidateTabbables: function() {
      this.__firstFocusableNode = this.__lastFocusableNode = null;
    },

    _ensureSetup: function() {
      if (this._overlaySetup) {
        return;
      }
      this._overlaySetup = true;
      this.style.outline = 'none';
      this.style.display = 'none';
    },

    /**
     * Called when `opened` changes.
     * @param {boolean=} opened
     * @protected
     */
    _openedChanged: function(opened) {
      if (opened) {
        this.removeAttribute('aria-hidden');
      } else {
        this.setAttribute('aria-hidden', 'true');
      }

      // Defer any animation-related code on attached
      // (_openedChanged gets called again on attached).
      if (!this.isAttached) {
        return;
      }

      this.__isAnimating = true;

      // Use requestAnimationFrame for non-blocking rendering.
      this.__onNextAnimationFrame(this.__openedChanged);
    },

    _canceledChanged: function() {
      this.closingReason = this.closingReason || {};
      this.closingReason.canceled = this.canceled;
    },

    _withBackdropChanged: function() {
      // If tabindex is already set, no need to override it.
      if (this.withBackdrop && !this.hasAttribute('tabindex')) {
        this.setAttribute('tabindex', '-1');
        this.__shouldRemoveTabIndex = true;
      } else if (this.__shouldRemoveTabIndex) {
        this.removeAttribute('tabindex');
        this.__shouldRemoveTabIndex = false;
      }
      if (this.opened && this.isAttached) {
        this._manager.trackBackdrop();
      }
    },

    /**
     * tasks which must occur before opening; e.g. making the element visible.
     * @protected
     */
    _prepareRenderOpened: function() {
      // Store focused node.
      this.__restoreFocusNode = this._manager.deepActiveElement;

      // Needed to calculate the size of the overlay so that transitions on its size
      // will have the correct starting points.
      this._preparePositioning();
      this.refit();
      this._finishPositioning();

      // Safari will apply the focus to the autofocus element when displayed
      // for the first time, so we make sure to return the focus where it was.
      if (this.noAutoFocus && document.activeElement === this._focusNode) {
        this._focusNode.blur();
        this.__restoreFocusNode.focus();
      }
    },

    /**
     * Tasks which cause the overlay to actually open; typically play an animation.
     * @protected
     */
    _renderOpened: function() {
      this._finishRenderOpened();
    },

    /**
     * Tasks which cause the overlay to actually close; typically play an animation.
     * @protected
     */
    _renderClosed: function() {
      this._finishRenderClosed();
    },

    /**
     * Tasks to be performed at the end of open action. Will fire `iron-overlay-opened`.
     * @protected
     */
    _finishRenderOpened: function() {
      this.notifyResize();
      this.__isAnimating = false;

      this.fire('iron-overlay-opened');
    },

    /**
     * Tasks to be performed at the end of close action. Will fire `iron-overlay-closed`.
     * @protected
     */
    _finishRenderClosed: function() {
      // Hide the overlay.
      this.style.display = 'none';
      // Reset z-index only at the end of the animation.
      this.style.zIndex = '';
      this.notifyResize();
      this.__isAnimating = false;
      this.fire('iron-overlay-closed', this.closingReason);
    },

    _preparePositioning: function() {
      this.style.transition = this.style.webkitTransition = 'none';
      this.style.transform = this.style.webkitTransform = 'none';
      this.style.display = '';
    },

    _finishPositioning: function() {
      // First, make it invisible & reactivate animations.
      this.style.display = 'none';
      // Force reflow before re-enabling animations so that they don't start.
      // Set scrollTop to itself so that Closure Compiler doesn't remove this.
      this.scrollTop = this.scrollTop;
      this.style.transition = this.style.webkitTransition = '';
      this.style.transform = this.style.webkitTransform = '';
      // Now that animations are enabled, make it visible again
      this.style.display = '';
      // Force reflow, so that following animations are properly started.
      // Set scrollTop to itself so that Closure Compiler doesn't remove this.
      this.scrollTop = this.scrollTop;
    },

    /**
     * Applies focus according to the opened state.
     * @protected
     */
    _applyFocus: function() {
      if (this.opened) {
        if (!this.noAutoFocus) {
          this._focusNode.focus();
        }
      }
      else {
        this._focusNode.blur();
        this._focusedChild = null;
        // Restore focus.
        if (this.restoreFocusOnClose && this.__restoreFocusNode) {
          this.__restoreFocusNode.focus();
        }
        this.__restoreFocusNode = null;
        // If many overlays get closed at the same time, one of them would still
        // be the currentOverlay even if already closed, and would call _applyFocus
        // infinitely, so we check for this not to be the current overlay.
        var currentOverlay = this._manager.currentOverlay();
        if (currentOverlay && this !== currentOverlay) {
          currentOverlay._applyFocus();
        }
      }
    },

    /**
     * Cancels (closes) the overlay. Call when click happens outside the overlay.
     * @param {!Event} event
     * @protected
     */
    _onCaptureClick: function(event) {
      if (!this.noCancelOnOutsideClick) {
        this.cancel(event);
      }
    },

    /**
     * Keeps track of the focused child. If withBackdrop, traps focus within overlay.
     * @param {!Event} event
     * @protected
     */
    _onCaptureFocus: function (event) {
      if (!this.withBackdrop) {
        return;
      }
      var path = Polymer.dom(event).path;
      if (path.indexOf(this) === -1) {
        event.stopPropagation();
        this._applyFocus();
      } else {
        this._focusedChild = path[0];
      }
    },

    /**
     * Handles the ESC key event and cancels (closes) the overlay.
     * @param {!Event} event
     * @protected
     */
    _onCaptureEsc: function(event) {
      if (!this.noCancelOnEscKey) {
        this.cancel(event);
      }
    },

    /**
     * Handles TAB key events to track focus changes.
     * Will wrap focus for overlays withBackdrop.
     * @param {!Event} event
     * @protected
     */
    _onCaptureTab: function(event) {
      if (!this.withBackdrop) {
        return;
      }
      this.__ensureFirstLastFocusables();
      // TAB wraps from last to first focusable.
      // Shift + TAB wraps from first to last focusable.
      var shift = event.shiftKey;
      var nodeToCheck = shift ? this.__firstFocusableNode : this.__lastFocusableNode;
      var nodeToSet = shift ? this.__lastFocusableNode : this.__firstFocusableNode;
      var shouldWrap = false;
      if (nodeToCheck === nodeToSet) {
        // If nodeToCheck is the same as nodeToSet, it means we have an overlay
        // with 0 or 1 focusables; in either case we still need to trap the
        // focus within the overlay.
        shouldWrap = true;
      } else {
        // In dom=shadow, the manager will receive focus changes on the main
        // root but not the ones within other shadow roots, so we can't rely on
        // _focusedChild, but we should check the deepest active element.
        var focusedNode = this._manager.deepActiveElement;
        // If the active element is not the nodeToCheck but the overlay itself,
        // it means the focus is about to go outside the overlay, hence we
        // should prevent that (e.g. user opens the overlay and hit Shift+TAB).
        shouldWrap = (focusedNode === nodeToCheck || focusedNode === this);
      }

      if (shouldWrap) {
        // When the overlay contains the last focusable element of the document
        // and it's already focused, pressing TAB would move the focus outside
        // the document (e.g. to the browser search bar). Similarly, when the
        // overlay contains the first focusable element of the document and it's
        // already focused, pressing Shift+TAB would move the focus outside the
        // document (e.g. to the browser search bar).
        // In both cases, we would not receive a focus event, but only a blur.
        // In order to achieve focus wrapping, we prevent this TAB event and
        // force the focus. This will also prevent the focus to temporarily move
        // outside the overlay, which might cause scrolling.
        event.preventDefault();
        this._focusedChild = nodeToSet;
        this._applyFocus();
      }
    },

    /**
     * Refits if the overlay is opened and not animating.
     * @protected
     */
    _onIronResize: function() {
      if (this.opened && !this.__isAnimating) {
        this.__onNextAnimationFrame(this.refit);
      }
    },

    /**
     * Will call notifyResize if overlay is opened.
     * Can be overridden in order to avoid multiple observers on the same node.
     * @protected
     */
    _onNodesChange: function() {
      if (this.opened && !this.__isAnimating) {
        // It might have added focusable nodes, so invalidate cached values.
        this.invalidateTabbables();
        this.notifyResize();
      }
    },

    /**
     * Will set first and last focusable nodes if any of them is not set.
     * @private
     */
    __ensureFirstLastFocusables: function() {
      if (!this.__firstFocusableNode || !this.__lastFocusableNode) {
        var focusableNodes = this._focusableNodes;
        this.__firstFocusableNode = focusableNodes[0];
        this.__lastFocusableNode = focusableNodes[focusableNodes.length - 1];
      }
    },

    /**
     * Tasks executed when opened changes: prepare for the opening, move the
     * focus, update the manager, render opened/closed.
     * @private
     */
    __openedChanged: function() {
      if (this.opened) {
        // Make overlay visible, then add it to the manager.
        this._prepareRenderOpened();
        this._manager.addOverlay(this);
        // Move the focus to the child node with [autofocus].
        this._applyFocus();

        this._renderOpened();
      } else {
        // Remove overlay, then restore the focus before actually closing.
        this._manager.removeOverlay(this);
        this._applyFocus();

        this._renderClosed();
      }
    },

    /**
     * Executes a callback on the next animation frame, overriding any previous
     * callback awaiting for the next animation frame. e.g.
     * `__onNextAnimationFrame(callback1) && __onNextAnimationFrame(callback2)`;
     * `callback1` will never be invoked.
     * @param {!Function} callback Its `this` parameter is the overlay itself.
     * @private
     */
    __onNextAnimationFrame: function(callback) {
      if (this.__raf) {
        window.cancelAnimationFrame(this.__raf);
      }
      var self = this;
      this.__raf = window.requestAnimationFrame(function nextAnimationFrame() {
        self.__raf = null;
        callback.call(self);
      });
    }

  };

  /**
  Use `Polymer.IronOverlayBehavior` to implement an element that can be hidden or shown, and displays
  on top of other content. It includes an optional backdrop, and can be used to implement a variety
  of UI controls including dialogs and drop downs. Multiple overlays may be displayed at once.

  See the [demo source code](https://github.com/PolymerElements/iron-overlay-behavior/blob/master/demo/simple-overlay.html)
  for an example.

  ### Closing and canceling

  An overlay may be hidden by closing or canceling. The difference between close and cancel is user
  intent. Closing generally implies that the user acknowledged the content on the overlay. By default,
  it will cancel whenever the user taps outside it or presses the escape key. This behavior is
  configurable with the `no-cancel-on-esc-key` and the `no-cancel-on-outside-click` properties.
  `close()` should be called explicitly by the implementer when the user interacts with a control
  in the overlay element. When the dialog is canceled, the overlay fires an 'iron-overlay-canceled'
  event. Call `preventDefault` on this event to prevent the overlay from closing.

  ### Positioning

  By default the element is sized and positioned to fit and centered inside the window. You can
  position and size it manually using CSS. See `Polymer.IronFitBehavior`.

  ### Backdrop

  Set the `with-backdrop` attribute to display a backdrop behind the overlay. The backdrop is
  appended to `<body>` and is of type `<iron-overlay-backdrop>`. See its doc page for styling
  options.

  In addition, `with-backdrop` will wrap the focus within the content in the light DOM.
  Override the [`_focusableNodes` getter](#Polymer.IronOverlayBehavior:property-_focusableNodes)
  to achieve a different behavior.

  ### Limitations

  The element is styled to appear on top of other content by setting its `z-index` property. You
  must ensure no element has a stacking context with a higher `z-index` than its parent stacking
  context. You should place this element as a child of `<body>` whenever possible.

  @demo demo/index.html
  @polymerBehavior
  */
  Polymer.IronOverlayBehavior = [Polymer.IronFitBehavior, Polymer.IronResizableBehavior, Polymer.IronOverlayBehaviorImpl];

  /**
   * Fired after the overlay opens.
   * @event iron-overlay-opened
   */

  /**
   * Fired when the overlay is canceled, but before it is closed.
   * @event iron-overlay-canceled
   * @param {Event} event The closing of the overlay can be prevented
   * by calling `event.preventDefault()`. The `event.detail` is the original event that
   * originated the canceling (e.g. ESC keyboard event or click event outside the overlay).
   */

  /**
   * Fired after the overlay closes.
   * @event iron-overlay-closed
   * @param {Event} event The `event.detail` is the `closingReason` property
   * (contains `canceled`, whether the overlay was canceled).
   */

})();
/**
   * `Polymer.NeonAnimatableBehavior` is implemented by elements containing animations for use with
   * elements implementing `Polymer.NeonAnimationRunnerBehavior`.
   * @polymerBehavior
   */
  Polymer.NeonAnimatableBehavior = {

    properties: {

      /**
       * Animation configuration. See README for more info.
       */
      animationConfig: {
        type: Object
      },

      /**
       * Convenience property for setting an 'entry' animation. Do not set `animationConfig.entry`
       * manually if using this. The animated node is set to `this` if using this property.
       */
      entryAnimation: {
        observer: '_entryAnimationChanged',
        type: String
      },

      /**
       * Convenience property for setting an 'exit' animation. Do not set `animationConfig.exit`
       * manually if using this. The animated node is set to `this` if using this property.
       */
      exitAnimation: {
        observer: '_exitAnimationChanged',
        type: String
      }

    },

    _entryAnimationChanged: function() {
      this.animationConfig = this.animationConfig || {};
      this.animationConfig['entry'] = [{
        name: this.entryAnimation,
        node: this
      }];
    },

    _exitAnimationChanged: function() {
      this.animationConfig = this.animationConfig || {};
      this.animationConfig['exit'] = [{
        name: this.exitAnimation,
        node: this
      }];
    },

    _copyProperties: function(config1, config2) {
      // shallowly copy properties from config2 to config1
      for (var property in config2) {
        config1[property] = config2[property];
      }
    },

    _cloneConfig: function(config) {
      var clone = {
        isClone: true
      };
      this._copyProperties(clone, config);
      return clone;
    },

    _getAnimationConfigRecursive: function(type, map, allConfigs) {
      if (!this.animationConfig) {
        return;
      }

      if(this.animationConfig.value && typeof this.animationConfig.value === 'function') {
      	this._warn(this._logf('playAnimation', "Please put 'animationConfig' inside of your components 'properties' object instead of outside of it."));
      	return;
      }

      // type is optional
      var thisConfig;
      if (type) {
        thisConfig = this.animationConfig[type];
      } else {
        thisConfig = this.animationConfig;
      }

      if (!Array.isArray(thisConfig)) {
        thisConfig = [thisConfig];
      }

      // iterate animations and recurse to process configurations from child nodes
      if (thisConfig) {
        for (var config, index = 0; config = thisConfig[index]; index++) {
          if (config.animatable) {
            config.animatable._getAnimationConfigRecursive(config.type || type, map, allConfigs);
          } else {
            if (config.id) {
              var cachedConfig = map[config.id];
              if (cachedConfig) {
                // merge configurations with the same id, making a clone lazily
                if (!cachedConfig.isClone) {
                  map[config.id] = this._cloneConfig(cachedConfig)
                  cachedConfig = map[config.id];
                }
                this._copyProperties(cachedConfig, config);
              } else {
                // put any configs with an id into a map
                map[config.id] = config;
              }
            } else {
              allConfigs.push(config);
            }
          }
        }
      }
    },

    /**
     * An element implementing `Polymer.NeonAnimationRunnerBehavior` calls this method to configure
     * an animation with an optional type. Elements implementing `Polymer.NeonAnimatableBehavior`
     * should define the property `animationConfig`, which is either a configuration object
     * or a map of animation type to array of configuration objects.
     */
    getAnimationConfig: function(type) {
      var map = {};
      var allConfigs = [];
      this._getAnimationConfigRecursive(type, map, allConfigs);
      // append the configurations saved in the map to the array
      for (var key in map) {
        allConfigs.push(map[key]);
      }
      return allConfigs;
    }

  };
/**
   * `Polymer.NeonAnimationRunnerBehavior` adds a method to run animations.
   *
   * @polymerBehavior Polymer.NeonAnimationRunnerBehavior
   */
  Polymer.NeonAnimationRunnerBehaviorImpl = {

    _configureAnimations: function(configs) {
      var results = [];
      if (configs.length > 0) {
        for (var config, index = 0; config = configs[index]; index++) {
          var neonAnimation = document.createElement(config.name);
          // is this element actually a neon animation?
          if (neonAnimation.isNeonAnimation) {
            var result = null;
            // configuration or play could fail if polyfills aren't loaded
            try {
              result = neonAnimation.configure(config);
              // Check if we have an Effect rather than an Animation
              if (typeof result.cancel != 'function') { 
                result = document.timeline.play(result);
              }
            } catch (e) {
              result = null;
              console.warn('Couldnt play', '(', config.name, ').', e);
            }
            if (result) {
              results.push({
                neonAnimation: neonAnimation,
                config: config,
                animation: result,
              });
            }
          } else {
            console.warn(this.is + ':', config.name, 'not found!');
          }
        }
      }
      return results;
    },

    _shouldComplete: function(activeEntries) {
      var finished = true;
      for (var i = 0; i < activeEntries.length; i++) {
        if (activeEntries[i].animation.playState != 'finished') {
          finished = false;
          break;
        }
      }
      return finished;
    },

    _complete: function(activeEntries) {
      for (var i = 0; i < activeEntries.length; i++) {
        activeEntries[i].neonAnimation.complete(activeEntries[i].config);
      }
      for (var i = 0; i < activeEntries.length; i++) {
        activeEntries[i].animation.cancel();
      }
    },

    /**
     * Plays an animation with an optional `type`.
     * @param {string=} type
     * @param {!Object=} cookie
     */
    playAnimation: function(type, cookie) {
      var configs = this.getAnimationConfig(type);
      if (!configs) {
        return;
      }
      this._active = this._active || {};
      if (this._active[type]) {
        this._complete(this._active[type]);
        delete this._active[type];
      }

      var activeEntries = this._configureAnimations(configs);

      if (activeEntries.length == 0) {
        this.fire('neon-animation-finish', cookie, {bubbles: false});
        return;
      }

      this._active[type] = activeEntries;

      for (var i = 0; i < activeEntries.length; i++) {
        activeEntries[i].animation.onfinish = function() {
          if (this._shouldComplete(activeEntries)) {
            this._complete(activeEntries);
            delete this._active[type];
            this.fire('neon-animation-finish', cookie, {bubbles: false});
          }
        }.bind(this);
      }
    },

    /**
     * Cancels the currently running animations.
     */
    cancelAnimation: function() {
      for (var k in this._animations) {
        this._animations[k].cancel();
      }
      this._animations = {};
    }
  };

  /** @polymerBehavior Polymer.NeonAnimationRunnerBehavior */
  Polymer.NeonAnimationRunnerBehavior = [
    Polymer.NeonAnimatableBehavior,
    Polymer.NeonAnimationRunnerBehaviorImpl
  ];
/**
   * Use `Polymer.NeonAnimationBehavior` to implement an animation.
   * @polymerBehavior
   */
  Polymer.NeonAnimationBehavior = {

    properties: {

      /**
       * Defines the animation timing.
       */
      animationTiming: {
        type: Object,
        value: function() {
          return {
            duration: 500,
            easing: 'cubic-bezier(0.4, 0, 0.2, 1)',
            fill: 'both'
          }
        }
      }

    },

    /**
     * Can be used to determine that elements implement this behavior.
     */
    isNeonAnimation: true,

    /**
     * Do any animation configuration here.
     */
    // configure: function(config) {
    // },

    /**
     * Returns the animation timing by mixing in properties from `config` to the defaults defined
     * by the animation.
     */
    timingFromConfig: function(config) {
      if (config.timing) {
        for (var property in config.timing) {
          this.animationTiming[property] = config.timing[property];
        }
      }
      return this.animationTiming;
    },

    /**
     * Sets `transform` and `transformOrigin` properties along with the prefixed versions.
     */
    setPrefixedProperty: function(node, property, value) {
      var map = {
        'transform': ['webkitTransform'],
        'transformOrigin': ['mozTransformOrigin', 'webkitTransformOrigin']
      };
      var prefixes = map[property];
      for (var prefix, index = 0; prefix = prefixes[index]; index++) {
        node.style[prefix] = value;
      }
      node.style[property] = value;
    },

    /**
     * Called when the animation finishes.
     */
    complete: function() {}

  };
// Copyright 2014 Google Inc. All rights reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
//     You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//     See the License for the specific language governing permissions and
// limitations under the License.

!function(a,b){var c={},d={},e={},f=null;!function(a,b){function c(a){if("number"==typeof a)return a;var b={};for(var c in a)b[c]=a[c];return b}function d(){this._delay=0,this._endDelay=0,this._fill="none",this._iterationStart=0,this._iterations=1,this._duration=0,this._playbackRate=1,this._direction="normal",this._easing="linear",this._easingFunction=x}function e(){return a.isDeprecated("Invalid timing inputs","2016-03-02","TypeError exceptions will be thrown instead.",!0)}function f(b,c,e){var f=new d;return c&&(f.fill="both",f.duration="auto"),"number"!=typeof b||isNaN(b)?void 0!==b&&Object.getOwnPropertyNames(b).forEach(function(c){if("auto"!=b[c]){if(("number"==typeof f[c]||"duration"==c)&&("number"!=typeof b[c]||isNaN(b[c])))return;if("fill"==c&&v.indexOf(b[c])==-1)return;if("direction"==c&&w.indexOf(b[c])==-1)return;if("playbackRate"==c&&1!==b[c]&&a.isDeprecated("AnimationEffectTiming.playbackRate","2014-11-28","Use Animation.playbackRate instead."))return;f[c]=b[c]}}):f.duration=b,f}function g(a){return"number"==typeof a&&(a=isNaN(a)?{duration:0}:{duration:a}),a}function h(b,c){return b=a.numericTimingToObject(b),f(b,c)}function i(a,b,c,d){return a<0||a>1||c<0||c>1?x:function(e){function f(a,b,c){return 3*a*(1-c)*(1-c)*c+3*b*(1-c)*c*c+c*c*c}if(e<=0){var g=0;return a>0?g=b/a:!b&&c>0&&(g=d/c),g*e}if(e>=1){var h=0;return c<1?h=(d-1)/(c-1):1==c&&a<1&&(h=(b-1)/(a-1)),1+h*(e-1)}for(var i=0,j=1;i<j;){var k=(i+j)/2,l=f(a,c,k);if(Math.abs(e-l)<1e-5)return f(b,d,k);l<e?i=k:j=k}return f(b,d,k)}}function j(a,b){return function(c){if(c>=1)return 1;var d=1/a;return c+=b*d,c-c%d}}function k(a){C||(C=document.createElement("div").style),C.animationTimingFunction="",C.animationTimingFunction=a;var b=C.animationTimingFunction;if(""==b&&e())throw new TypeError(a+" is not a valid value for easing");return b}function l(a){if("linear"==a)return x;var b=E.exec(a);if(b)return i.apply(this,b.slice(1).map(Number));var c=F.exec(a);if(c)return j(Number(c[1]),{start:y,middle:z,end:A}[c[2]]);var d=B[a];return d?d:x}function m(a){return Math.abs(n(a)/a.playbackRate)}function n(a){return 0===a.duration||0===a.iterations?0:a.duration*a.iterations}function o(a,b,c){if(null==b)return G;var d=c.delay+a+c.endDelay;return b<Math.min(c.delay,d)?H:b>=Math.min(c.delay+a,d)?I:J}function p(a,b,c,d,e){switch(d){case H:return"backwards"==b||"both"==b?0:null;case J:return c-e;case I:return"forwards"==b||"both"==b?a:null;case G:return null}}function q(a,b,c,d,e){var f=e;return 0===a?b!==H&&(f+=c):f+=d/a,f}function r(a,b,c,d,e,f){var g=a===1/0?b%1:a%1;return 0!==g||c!==I||0===d||0===e&&0!==f||(g=1),g}function s(a,b,c,d){return a===I&&b===1/0?1/0:1===c?Math.floor(d)-1:Math.floor(d)}function t(a,b,c){var d=a;if("normal"!==a&&"reverse"!==a){var e=b;"alternate-reverse"===a&&(e+=1),d="normal",e!==1/0&&e%2!==0&&(d="reverse")}return"normal"===d?c:1-c}function u(a,b,c){var d=o(a,b,c),e=p(a,c.fill,b,d,c.delay);if(null===e)return null;var f=q(c.duration,d,c.iterations,e,c.iterationStart),g=r(f,c.iterationStart,d,c.iterations,e,c.duration),h=s(d,c.iterations,g,f),i=t(c.direction,h,g);return c._easingFunction(i)}var v="backwards|forwards|both|none".split("|"),w="reverse|alternate|alternate-reverse".split("|"),x=function(a){return a};d.prototype={_setMember:function(b,c){this["_"+b]=c,this._effect&&(this._effect._timingInput[b]=c,this._effect._timing=a.normalizeTimingInput(this._effect._timingInput),this._effect.activeDuration=a.calculateActiveDuration(this._effect._timing),this._effect._animation&&this._effect._animation._rebuildUnderlyingAnimation())},get playbackRate(){return this._playbackRate},set delay(a){this._setMember("delay",a)},get delay(){return this._delay},set endDelay(a){this._setMember("endDelay",a)},get endDelay(){return this._endDelay},set fill(a){this._setMember("fill",a)},get fill(){return this._fill},set iterationStart(a){if((isNaN(a)||a<0)&&e())throw new TypeError("iterationStart must be a non-negative number, received: "+timing.iterationStart);this._setMember("iterationStart",a)},get iterationStart(){return this._iterationStart},set duration(a){if("auto"!=a&&(isNaN(a)||a<0)&&e())throw new TypeError("duration must be non-negative or auto, received: "+a);this._setMember("duration",a)},get duration(){return this._duration},set direction(a){this._setMember("direction",a)},get direction(){return this._direction},set easing(a){this._easingFunction=l(k(a)),this._setMember("easing",a)},get easing(){return this._easing},set iterations(a){if((isNaN(a)||a<0)&&e())throw new TypeError("iterations must be non-negative, received: "+a);this._setMember("iterations",a)},get iterations(){return this._iterations}};var y=1,z=.5,A=0,B={ease:i(.25,.1,.25,1),"ease-in":i(.42,0,1,1),"ease-out":i(0,0,.58,1),"ease-in-out":i(.42,0,.58,1),"step-start":j(1,y),"step-middle":j(1,z),"step-end":j(1,A)},C=null,D="\\s*(-?\\d+\\.?\\d*|-?\\.\\d+)\\s*",E=new RegExp("cubic-bezier\\("+D+","+D+","+D+","+D+"\\)"),F=/steps\(\s*(\d+)\s*,\s*(start|middle|end)\s*\)/,G=0,H=1,I=2,J=3;a.cloneTimingInput=c,a.makeTiming=f,a.numericTimingToObject=g,a.normalizeTimingInput=h,a.calculateActiveDuration=m,a.calculateIterationProgress=u,a.calculatePhase=o,a.normalizeEasing=k,a.parseEasingFunction=l}(c,f),function(a,b){function c(a,b){return a in k?k[a][b]||b:b}function d(a){return"display"===a||0===a.lastIndexOf("animation",0)||0===a.lastIndexOf("transition",0)}function e(a,b,e){if(!d(a)){var f=h[a];if(f){i.style[a]=b;for(var g in f){var j=f[g],k=i.style[j];e[j]=c(j,k)}}else e[a]=c(a,b)}}function f(a){var b=[];for(var c in a)if(!(c in["easing","offset","composite"])){var d=a[c];Array.isArray(d)||(d=[d]);for(var e,f=d.length,g=0;g<f;g++)e={},"offset"in a?e.offset=a.offset:1==f?e.offset=1:e.offset=g/(f-1),"easing"in a&&(e.easing=a.easing),"composite"in a&&(e.composite=a.composite),e[c]=d[g],b.push(e)}return b.sort(function(a,b){return a.offset-b.offset}),b}function g(b){function c(){var a=d.length;null==d[a-1].offset&&(d[a-1].offset=1),a>1&&null==d[0].offset&&(d[0].offset=0);for(var b=0,c=d[0].offset,e=1;e<a;e++){var f=d[e].offset;if(null!=f){for(var g=1;g<e-b;g++)d[b+g].offset=c+(f-c)*g/(e-b);b=e,c=f}}}if(null==b)return[];window.Symbol&&Symbol.iterator&&Array.prototype.from&&b[Symbol.iterator]&&(b=Array.from(b)),Array.isArray(b)||(b=f(b));for(var d=b.map(function(b){var c={};for(var d in b){var f=b[d];if("offset"==d){if(null!=f){if(f=Number(f),!isFinite(f))throw new TypeError("Keyframe offsets must be numbers.");if(f<0||f>1)throw new TypeError("Keyframe offsets must be between 0 and 1.")}}else if("composite"==d){if("add"==f||"accumulate"==f)throw{type:DOMException.NOT_SUPPORTED_ERR,name:"NotSupportedError",message:"add compositing is not supported"};if("replace"!=f)throw new TypeError("Invalid composite mode "+f+".")}else f="easing"==d?a.normalizeEasing(f):""+f;e(d,f,c)}return void 0==c.offset&&(c.offset=null),void 0==c.easing&&(c.easing="linear"),c}),g=!0,h=-(1/0),i=0;i<d.length;i++){var j=d[i].offset;if(null!=j){if(j<h)throw new TypeError("Keyframes are not loosely sorted by offset. Sort or specify offsets.");h=j}else g=!1}return d=d.filter(function(a){return a.offset>=0&&a.offset<=1}),g||c(),d}var h={background:["backgroundImage","backgroundPosition","backgroundSize","backgroundRepeat","backgroundAttachment","backgroundOrigin","backgroundClip","backgroundColor"],border:["borderTopColor","borderTopStyle","borderTopWidth","borderRightColor","borderRightStyle","borderRightWidth","borderBottomColor","borderBottomStyle","borderBottomWidth","borderLeftColor","borderLeftStyle","borderLeftWidth"],borderBottom:["borderBottomWidth","borderBottomStyle","borderBottomColor"],borderColor:["borderTopColor","borderRightColor","borderBottomColor","borderLeftColor"],borderLeft:["borderLeftWidth","borderLeftStyle","borderLeftColor"],borderRadius:["borderTopLeftRadius","borderTopRightRadius","borderBottomRightRadius","borderBottomLeftRadius"],borderRight:["borderRightWidth","borderRightStyle","borderRightColor"],borderTop:["borderTopWidth","borderTopStyle","borderTopColor"],borderWidth:["borderTopWidth","borderRightWidth","borderBottomWidth","borderLeftWidth"],flex:["flexGrow","flexShrink","flexBasis"],font:["fontFamily","fontSize","fontStyle","fontVariant","fontWeight","lineHeight"],margin:["marginTop","marginRight","marginBottom","marginLeft"],outline:["outlineColor","outlineStyle","outlineWidth"],padding:["paddingTop","paddingRight","paddingBottom","paddingLeft"]},i=document.createElementNS("http://www.w3.org/1999/xhtml","div"),j={thin:"1px",medium:"3px",thick:"5px"},k={borderBottomWidth:j,borderLeftWidth:j,borderRightWidth:j,borderTopWidth:j,fontSize:{"xx-small":"60%","x-small":"75%",small:"89%",medium:"100%",large:"120%","x-large":"150%","xx-large":"200%"},fontWeight:{normal:"400",bold:"700"},outlineWidth:j,textShadow:{none:"0px 0px 0px transparent"},boxShadow:{none:"0px 0px 0px 0px transparent"}};a.convertToArrayForm=f,a.normalizeKeyframes=g}(c,f),function(a){var b={};a.isDeprecated=function(a,c,d,e){var f=e?"are":"is",g=new Date,h=new Date(c);return h.setMonth(h.getMonth()+3),!(g<h&&(a in b||console.warn("Web Animations: "+a+" "+f+" deprecated and will stop working on "+h.toDateString()+". "+d),b[a]=!0,1))},a.deprecated=function(b,c,d,e){var f=e?"are":"is";if(a.isDeprecated(b,c,d,e))throw new Error(b+" "+f+" no longer supported. "+d)}}(c),function(){if(document.documentElement.animate){var a=document.documentElement.animate([],0),b=!0;if(a&&(b=!1,"play|currentTime|pause|reverse|playbackRate|cancel|finish|startTime|playState".split("|").forEach(function(c){void 0===a[c]&&(b=!0)})),!b)return}!function(a,b,c){function d(a){for(var b={},c=0;c<a.length;c++)for(var d in a[c])if("offset"!=d&&"easing"!=d&&"composite"!=d){var e={offset:a[c].offset,easing:a[c].easing,value:a[c][d]};b[d]=b[d]||[],b[d].push(e)}for(var f in b){var g=b[f];if(0!=g[0].offset||1!=g[g.length-1].offset)throw{type:DOMException.NOT_SUPPORTED_ERR,name:"NotSupportedError",message:"Partial keyframes are not supported"}}return b}function e(c){var d=[];for(var e in c)for(var f=c[e],g=0;g<f.length-1;g++){var h=g,i=g+1,j=f[h].offset,k=f[i].offset,l=j,m=k;0==g&&(l=-(1/0),0==k&&(i=h)),g==f.length-2&&(m=1/0,1==j&&(h=i)),d.push({applyFrom:l,applyTo:m,startOffset:f[h].offset,endOffset:f[i].offset,easingFunction:a.parseEasingFunction(f[h].easing),property:e,interpolation:b.propertyInterpolation(e,f[h].value,f[i].value)})}return d.sort(function(a,b){return a.startOffset-b.startOffset}),d}b.convertEffectInput=function(c){var f=a.normalizeKeyframes(c),g=d(f),h=e(g);return function(a,c){if(null!=c)h.filter(function(a){return c>=a.applyFrom&&c<a.applyTo}).forEach(function(d){var e=c-d.startOffset,f=d.endOffset-d.startOffset,g=0==f?0:d.easingFunction(e/f);b.apply(a,d.property,d.interpolation(g))});else for(var d in g)"offset"!=d&&"easing"!=d&&"composite"!=d&&b.clear(a,d)}}}(c,d,f),function(a,b,c){function d(a){return a.replace(/-(.)/g,function(a,b){return b.toUpperCase()})}function e(a,b,c){h[c]=h[c]||[],h[c].push([a,b])}function f(a,b,c){for(var f=0;f<c.length;f++){var g=c[f];e(a,b,d(g))}}function g(c,e,f){var g=c;/-/.test(c)&&!a.isDeprecated("Hyphenated property names","2016-03-22","Use camelCase instead.",!0)&&(g=d(c)),"initial"!=e&&"initial"!=f||("initial"==e&&(e=i[g]),"initial"==f&&(f=i[g]));for(var j=e==f?[]:h[g],k=0;j&&k<j.length;k++){var l=j[k][0](e),m=j[k][0](f);if(void 0!==l&&void 0!==m){var n=j[k][1](l,m);if(n){var o=b.Interpolation.apply(null,n);return function(a){return 0==a?e:1==a?f:o(a)}}}}return b.Interpolation(!1,!0,function(a){return a?f:e})}var h={};b.addPropertiesHandler=f;var i={backgroundColor:"transparent",backgroundPosition:"0% 0%",borderBottomColor:"currentColor",borderBottomLeftRadius:"0px",borderBottomRightRadius:"0px",borderBottomWidth:"3px",borderLeftColor:"currentColor",borderLeftWidth:"3px",borderRightColor:"currentColor",borderRightWidth:"3px",borderSpacing:"2px",borderTopColor:"currentColor",borderTopLeftRadius:"0px",borderTopRightRadius:"0px",borderTopWidth:"3px",bottom:"auto",clip:"rect(0px, 0px, 0px, 0px)",color:"black",fontSize:"100%",fontWeight:"400",height:"auto",left:"auto",letterSpacing:"normal",lineHeight:"120%",marginBottom:"0px",marginLeft:"0px",marginRight:"0px",marginTop:"0px",maxHeight:"none",maxWidth:"none",minHeight:"0px",minWidth:"0px",opacity:"1.0",outlineColor:"invert",outlineOffset:"0px",outlineWidth:"3px",paddingBottom:"0px",paddingLeft:"0px",paddingRight:"0px",paddingTop:"0px",right:"auto",textIndent:"0px",textShadow:"0px 0px 0px transparent",top:"auto",transform:"",verticalAlign:"0px",visibility:"visible",width:"auto",wordSpacing:"normal",zIndex:"auto"};b.propertyInterpolation=g}(c,d,f),function(a,b,c){function d(b){var c=a.calculateActiveDuration(b),d=function(d){return a.calculateIterationProgress(c,d,b)};return d._totalDuration=b.delay+c+b.endDelay,d}b.KeyframeEffect=function(c,e,f,g){var h,i=d(a.normalizeTimingInput(f)),j=b.convertEffectInput(e),k=function(){j(c,h)};return k._update=function(a){return h=i(a),null!==h},k._clear=function(){j(c,null)},k._hasSameTarget=function(a){return c===a},k._target=c,k._totalDuration=i._totalDuration,k._id=g,k},b.NullEffect=function(a){var b=function(){a&&(a(),a=null)};return b._update=function(){return null},b._totalDuration=0,b._hasSameTarget=function(){return!1},b}}(c,d,f),function(a,b){a.apply=function(b,c,d){b.style[a.propertyName(c)]=d},a.clear=function(b,c){b.style[a.propertyName(c)]=""}}(d,f),function(a){window.Element.prototype.animate=function(b,c){var d="";return c&&c.id&&(d=c.id),a.timeline._play(a.KeyframeEffect(this,b,c,d))}}(d),function(a,b){function c(a,b,d){if("number"==typeof a&&"number"==typeof b)return a*(1-d)+b*d;if("boolean"==typeof a&&"boolean"==typeof b)return d<.5?a:b;if(a.length==b.length){for(var e=[],f=0;f<a.length;f++)e.push(c(a[f],b[f],d));return e}throw"Mismatched interpolation arguments "+a+":"+b}a.Interpolation=function(a,b,d){return function(e){return d(c(a,b,e))}}}(d,f),function(a,b,c){a.sequenceNumber=0;var d=function(a,b,c){this.target=a,this.currentTime=b,this.timelineTime=c,this.type="finish",this.bubbles=!1,this.cancelable=!1,this.currentTarget=a,this.defaultPrevented=!1,this.eventPhase=Event.AT_TARGET,this.timeStamp=Date.now()};b.Animation=function(b){this.id="",b&&b._id&&(this.id=b._id),this._sequenceNumber=a.sequenceNumber++,this._currentTime=0,this._startTime=null,this._paused=!1,this._playbackRate=1,this._inTimeline=!0,this._finishedFlag=!0,this.onfinish=null,this._finishHandlers=[],this._effect=b,this._inEffect=this._effect._update(0),this._idle=!0,this._currentTimePending=!1},b.Animation.prototype={_ensureAlive:function(){this.playbackRate<0&&0===this.currentTime?this._inEffect=this._effect._update(-1):this._inEffect=this._effect._update(this.currentTime),this._inTimeline||!this._inEffect&&this._finishedFlag||(this._inTimeline=!0,b.timeline._animations.push(this))},_tickCurrentTime:function(a,b){a!=this._currentTime&&(this._currentTime=a,this._isFinished&&!b&&(this._currentTime=this._playbackRate>0?this._totalDuration:0),this._ensureAlive())},get currentTime(){return this._idle||this._currentTimePending?null:this._currentTime},set currentTime(a){a=+a,isNaN(a)||(b.restart(),this._paused||null==this._startTime||(this._startTime=this._timeline.currentTime-a/this._playbackRate),this._currentTimePending=!1,this._currentTime!=a&&(this._idle&&(this._idle=!1,this._paused=!0),this._tickCurrentTime(a,!0),b.applyDirtiedAnimation(this)))},get startTime(){return this._startTime},set startTime(a){a=+a,isNaN(a)||this._paused||this._idle||(this._startTime=a,this._tickCurrentTime((this._timeline.currentTime-this._startTime)*this.playbackRate),b.applyDirtiedAnimation(this))},get playbackRate(){return this._playbackRate},set playbackRate(a){if(a!=this._playbackRate){var c=this.currentTime;this._playbackRate=a,this._startTime=null,"paused"!=this.playState&&"idle"!=this.playState&&(this._finishedFlag=!1,this._idle=!1,this._ensureAlive(),b.applyDirtiedAnimation(this)),null!=c&&(this.currentTime=c)}},get _isFinished(){return!this._idle&&(this._playbackRate>0&&this._currentTime>=this._totalDuration||this._playbackRate<0&&this._currentTime<=0)},get _totalDuration(){return this._effect._totalDuration},get playState(){return this._idle?"idle":null==this._startTime&&!this._paused&&0!=this.playbackRate||this._currentTimePending?"pending":this._paused?"paused":this._isFinished?"finished":"running"},_rewind:function(){if(this._playbackRate>=0)this._currentTime=0;else{if(!(this._totalDuration<1/0))throw new DOMException("Unable to rewind negative playback rate animation with infinite duration","InvalidStateError");this._currentTime=this._totalDuration}},play:function(){this._paused=!1,(this._isFinished||this._idle)&&(this._rewind(),this._startTime=null),this._finishedFlag=!1,this._idle=!1,this._ensureAlive(),b.applyDirtiedAnimation(this)},pause:function(){this._isFinished||this._paused||this._idle?this._idle&&(this._rewind(),this._idle=!1):this._currentTimePending=!0,this._startTime=null,this._paused=!0},finish:function(){this._idle||(this.currentTime=this._playbackRate>0?this._totalDuration:0,this._startTime=this._totalDuration-this.currentTime,this._currentTimePending=!1,b.applyDirtiedAnimation(this))},cancel:function(){this._inEffect&&(this._inEffect=!1,this._idle=!0,this._paused=!1,this._isFinished=!0,this._finishedFlag=!0,this._currentTime=0,this._startTime=null,this._effect._update(null),b.applyDirtiedAnimation(this))},reverse:function(){this.playbackRate*=-1,this.play()},addEventListener:function(a,b){"function"==typeof b&&"finish"==a&&this._finishHandlers.push(b)},removeEventListener:function(a,b){if("finish"==a){var c=this._finishHandlers.indexOf(b);c>=0&&this._finishHandlers.splice(c,1)}},_fireEvents:function(a){if(this._isFinished){if(!this._finishedFlag){var b=new d(this,this._currentTime,a),c=this._finishHandlers.concat(this.onfinish?[this.onfinish]:[]);setTimeout(function(){c.forEach(function(a){a.call(b.target,b)})},0),this._finishedFlag=!0}}else this._finishedFlag=!1},_tick:function(a,b){this._idle||this._paused||(null==this._startTime?b&&(this.startTime=a-this._currentTime/this.playbackRate):this._isFinished||this._tickCurrentTime((a-this._startTime)*this.playbackRate)),b&&(this._currentTimePending=!1,this._fireEvents(a))},get _needsTick(){return this.playState in{pending:1,running:1}||!this._finishedFlag},_targetAnimations:function(){var a=this._effect._target;return a._activeAnimations||(a._activeAnimations=[]),a._activeAnimations},_markTarget:function(){var a=this._targetAnimations();a.indexOf(this)===-1&&a.push(this)},_unmarkTarget:function(){var a=this._targetAnimations(),b=a.indexOf(this);b!==-1&&a.splice(b,1)}}}(c,d,f),function(a,b,c){function d(a){var b=j;j=[],a<q.currentTime&&(a=q.currentTime),q._animations.sort(e),q._animations=h(a,!0,q._animations)[0],b.forEach(function(b){b[1](a)}),g(),l=void 0}function e(a,b){return a._sequenceNumber-b._sequenceNumber}function f(){this._animations=[],this.currentTime=window.performance&&performance.now?performance.now():0}function g(){o.forEach(function(a){a()}),o.length=0}function h(a,c,d){p=!0,n=!1;var e=b.timeline;e.currentTime=a,m=!1;var f=[],g=[],h=[],i=[];return d.forEach(function(b){b._tick(a,c),b._inEffect?(g.push(b._effect),b._markTarget()):(f.push(b._effect),b._unmarkTarget()),b._needsTick&&(m=!0);var d=b._inEffect||b._needsTick;b._inTimeline=d,d?h.push(b):i.push(b)}),o.push.apply(o,f),o.push.apply(o,g),m&&requestAnimationFrame(function(){}),p=!1,[h,i]}var i=window.requestAnimationFrame,j=[],k=0;window.requestAnimationFrame=function(a){var b=k++;return 0==j.length&&i(d),j.push([b,a]),b},window.cancelAnimationFrame=function(a){j.forEach(function(b){b[0]==a&&(b[1]=function(){})})},f.prototype={_play:function(c){c._timing=a.normalizeTimingInput(c.timing);var d=new b.Animation(c);return d._idle=!1,d._timeline=this,this._animations.push(d),b.restart(),b.applyDirtiedAnimation(d),d}};var l=void 0,m=!1,n=!1;b.restart=function(){return m||(m=!0,requestAnimationFrame(function(){}),n=!0),n},b.applyDirtiedAnimation=function(a){if(!p){a._markTarget();var c=a._targetAnimations();c.sort(e);var d=h(b.timeline.currentTime,!1,c.slice())[1];d.forEach(function(a){var b=q._animations.indexOf(a);b!==-1&&q._animations.splice(b,1)}),g()}};var o=[],p=!1,q=new f;b.timeline=q}(c,d,f),function(a){function b(a,b){var c=a.exec(b);if(c)return c=a.ignoreCase?c[0].toLowerCase():c[0],[c,b.substr(c.length)]}function c(a,b){b=b.replace(/^\s*/,"");var c=a(b);if(c)return[c[0],c[1].replace(/^\s*/,"")]}function d(a,d,e){a=c.bind(null,a);for(var f=[];;){var g=a(e);if(!g)return[f,e];if(f.push(g[0]),e=g[1],g=b(d,e),!g||""==g[1])return[f,e];e=g[1]}}function e(a,b){for(var c=0,d=0;d<b.length&&(!/\s|,/.test(b[d])||0!=c);d++)if("("==b[d])c++;else if(")"==b[d]&&(c--,0==c&&d++,c<=0))break;var e=a(b.substr(0,d));return void 0==e?void 0:[e,b.substr(d)]}function f(a,b){for(var c=a,d=b;c&&d;)c>d?c%=d:d%=c;return c=a*b/(c+d)}function g(a){return function(b){var c=a(b);return c&&(c[0]=void 0),c}}function h(a,b){return function(c){var d=a(c);return d?d:[b,c]}}function i(b,c){for(var d=[],e=0;e<b.length;e++){var f=a.consumeTrimmed(b[e],c);if(!f||""==f[0])return;void 0!==f[0]&&d.push(f[0]),c=f[1]}if(""==c)return d}function j(a,b,c,d,e){for(var g=[],h=[],i=[],j=f(d.length,e.length),k=0;k<j;k++){var l=b(d[k%d.length],e[k%e.length]);if(!l)return;g.push(l[0]),h.push(l[1]),i.push(l[2])}return[g,h,function(b){var d=b.map(function(a,b){return i[b](a)}).join(c);return a?a(d):d}]}function k(a,b,c){for(var d=[],e=[],f=[],g=0,h=0;h<c.length;h++)if("function"==typeof c[h]){var i=c[h](a[g],b[g++]);d.push(i[0]),e.push(i[1]),f.push(i[2])}else!function(a){d.push(!1),e.push(!1),f.push(function(){return c[a]})}(h);return[d,e,function(a){for(var b="",c=0;c<a.length;c++)b+=f[c](a[c]);return b}]}a.consumeToken=b,a.consumeTrimmed=c,a.consumeRepeated=d,a.consumeParenthesised=e,a.ignore=g,a.optional=h,a.consumeList=i,a.mergeNestedRepeated=j.bind(null,null),a.mergeWrappedNestedRepeated=j,a.mergeList=k}(d),function(a){function b(b){function c(b){var c=a.consumeToken(/^inset/i,b);if(c)return d.inset=!0,c;var c=a.consumeLengthOrPercent(b);if(c)return d.lengths.push(c[0]),c;var c=a.consumeColor(b);return c?(d.color=c[0],c):void 0}var d={inset:!1,lengths:[],color:null},e=a.consumeRepeated(c,/^/,b);if(e&&e[0].length)return[d,e[1]]}function c(c){var d=a.consumeRepeated(b,/^,/,c);if(d&&""==d[1])return d[0]}function d(b,c){for(;b.lengths.length<Math.max(b.lengths.length,c.lengths.length);)b.lengths.push({px:0});for(;c.lengths.length<Math.max(b.lengths.length,c.lengths.length);)c.lengths.push({px:0});if(b.inset==c.inset&&!!b.color==!!c.color){for(var d,e=[],f=[[],0],g=[[],0],h=0;h<b.lengths.length;h++){var i=a.mergeDimensions(b.lengths[h],c.lengths[h],2==h);f[0].push(i[0]),g[0].push(i[1]),e.push(i[2])}if(b.color&&c.color){var j=a.mergeColors(b.color,c.color);f[1]=j[0],g[1]=j[1],d=j[2]}return[f,g,function(a){for(var c=b.inset?"inset ":" ",f=0;f<e.length;f++)c+=e[f](a[0][f])+" ";return d&&(c+=d(a[1])),c}]}}function e(b,c,d,e){function f(a){return{inset:a,color:[0,0,0,0],lengths:[{px:0},{px:0},{px:0},{px:0}]}}for(var g=[],h=[],i=0;i<d.length||i<e.length;i++){var j=d[i]||f(e[i].inset),k=e[i]||f(d[i].inset);g.push(j),h.push(k)}return a.mergeNestedRepeated(b,c,g,h)}var f=e.bind(null,d,", ");a.addPropertiesHandler(c,f,["box-shadow","text-shadow"])}(d),function(a,b){function c(a){return a.toFixed(3).replace(".000","")}function d(a,b,c){return Math.min(b,Math.max(a,c))}function e(a){if(/^\s*[-+]?(\d*\.)?\d+\s*$/.test(a))return Number(a)}function f(a,b){return[a,b,c]}function g(a,b){if(0!=a)return i(0,1/0)(a,b)}function h(a,b){return[a,b,function(a){return Math.round(d(1,1/0,a))}]}function i(a,b){return function(e,f){return[e,f,function(e){return c(d(a,b,e))}]}}function j(a,b){return[a,b,Math.round]}a.clamp=d,a.addPropertiesHandler(e,i(0,1/0),["border-image-width","line-height"]),a.addPropertiesHandler(e,i(0,1),["opacity","shape-image-threshold"]),a.addPropertiesHandler(e,g,["flex-grow","flex-shrink"]),a.addPropertiesHandler(e,h,["orphans","widows"]),a.addPropertiesHandler(e,j,["z-index"]),a.parseNumber=e,a.mergeNumbers=f,a.numberToString=c}(d,f),function(a,b){function c(a,b){if("visible"==a||"visible"==b)return[0,1,function(c){return c<=0?a:c>=1?b:"visible"}]}a.addPropertiesHandler(String,c,["visibility"])}(d),function(a,b){function c(a){a=a.trim(),f.fillStyle="#000",f.fillStyle=a;var b=f.fillStyle;if(f.fillStyle="#fff",f.fillStyle=a,b==f.fillStyle){f.fillRect(0,0,1,1);var c=f.getImageData(0,0,1,1).data;f.clearRect(0,0,1,1);var d=c[3]/255;return[c[0]*d,c[1]*d,c[2]*d,d]}}function d(b,c){return[b,c,function(b){function c(a){return Math.max(0,Math.min(255,a))}if(b[3])for(var d=0;d<3;d++)b[d]=Math.round(c(b[d]/b[3]));return b[3]=a.numberToString(a.clamp(0,1,b[3])),"rgba("+b.join(",")+")"}]}var e=document.createElementNS("http://www.w3.org/1999/xhtml","canvas");e.width=e.height=1;var f=e.getContext("2d");a.addPropertiesHandler(c,d,["background-color","border-bottom-color","border-left-color","border-right-color","border-top-color","color","outline-color","text-decoration-color"]),a.consumeColor=a.consumeParenthesised.bind(null,c),a.mergeColors=d}(d,f),function(a,b){function c(a,b){if(b=b.trim().toLowerCase(),"0"==b&&"px".search(a)>=0)return{px:0};if(/^[^(]*$|^calc/.test(b)){b=b.replace(/calc\(/g,"(");var c={};b=b.replace(a,function(a){return c[a]=null,"U"+a});for(var d="U("+a.source+")",e=b.replace(/[-+]?(\d*\.)?\d+/g,"N").replace(new RegExp("N"+d,"g"),"D").replace(/\s[+-]\s/g,"O").replace(/\s/g,""),f=[/N\*(D)/g,/(N|D)[*\/]N/g,/(N|D)O\1/g,/\((N|D)\)/g],g=0;g<f.length;)f[g].test(e)?(e=e.replace(f[g],"$1"),g=0):g++;if("D"==e){for(var h in c){var i=eval(b.replace(new RegExp("U"+h,"g"),"").replace(new RegExp(d,"g"),"*0"));if(!isFinite(i))return;c[h]=i}return c}}}function d(a,b){return e(a,b,!0)}function e(b,c,d){var e,f=[];for(e in b)f.push(e);for(e in c)f.indexOf(e)<0&&f.push(e);return b=f.map(function(a){return b[a]||0}),c=f.map(function(a){return c[a]||0}),[b,c,function(b){var c=b.map(function(c,e){return 1==b.length&&d&&(c=Math.max(c,0)),a.numberToString(c)+f[e]}).join(" + ");return b.length>1?"calc("+c+")":c}]}var f="px|em|ex|ch|rem|vw|vh|vmin|vmax|cm|mm|in|pt|pc",g=c.bind(null,new RegExp(f,"g")),h=c.bind(null,new RegExp(f+"|%","g")),i=c.bind(null,/deg|rad|grad|turn/g);a.parseLength=g,a.parseLengthOrPercent=h,a.consumeLengthOrPercent=a.consumeParenthesised.bind(null,h),a.parseAngle=i,a.mergeDimensions=e;var j=a.consumeParenthesised.bind(null,g),k=a.consumeRepeated.bind(void 0,j,/^/),l=a.consumeRepeated.bind(void 0,k,/^,/);a.consumeSizePairList=l;var m=function(a){var b=l(a);if(b&&""==b[1])return b[0]},n=a.mergeNestedRepeated.bind(void 0,d," "),o=a.mergeNestedRepeated.bind(void 0,n,",");a.mergeNonNegativeSizePair=n,a.addPropertiesHandler(m,o,["background-size"]),a.addPropertiesHandler(h,d,["border-bottom-width","border-image-width","border-left-width","border-right-width","border-top-width","flex-basis","font-size","height","line-height","max-height","max-width","outline-width","width"]),a.addPropertiesHandler(h,e,["border-bottom-left-radius","border-bottom-right-radius","border-top-left-radius","border-top-right-radius","bottom","left","letter-spacing","margin-bottom","margin-left","margin-right","margin-top","min-height","min-width","outline-offset","padding-bottom","padding-left","padding-right","padding-top","perspective","right","shape-margin","text-indent","top","vertical-align","word-spacing"])}(d,f),function(a,b){function c(b){return a.consumeLengthOrPercent(b)||a.consumeToken(/^auto/,b)}function d(b){var d=a.consumeList([a.ignore(a.consumeToken.bind(null,/^rect/)),a.ignore(a.consumeToken.bind(null,/^\(/)),a.consumeRepeated.bind(null,c,/^,/),a.ignore(a.consumeToken.bind(null,/^\)/))],b);if(d&&4==d[0].length)return d[0]}function e(b,c){return"auto"==b||"auto"==c?[!0,!1,function(d){var e=d?b:c;if("auto"==e)return"auto";var f=a.mergeDimensions(e,e);return f[2](f[0])}]:a.mergeDimensions(b,c)}function f(a){return"rect("+a+")"}var g=a.mergeWrappedNestedRepeated.bind(null,f,e,", ");a.parseBox=d,a.mergeBoxes=g,a.addPropertiesHandler(d,g,["clip"])}(d,f),function(a,b){function c(a){return function(b){var c=0;return a.map(function(a){return a===k?b[c++]:a})}}function d(a){return a}function e(b){if(b=b.toLowerCase().trim(),"none"==b)return[];for(var c,d=/\s*(\w+)\(([^)]*)\)/g,e=[],f=0;c=d.exec(b);){if(c.index!=f)return;f=c.index+c[0].length;var g=c[1],h=n[g];if(!h)return;var i=c[2].split(","),j=h[0];if(j.length<i.length)return;for(var k=[],o=0;o<j.length;o++){var p,q=i[o],r=j[o];if(p=q?{A:function(b){return"0"==b.trim()?m:a.parseAngle(b)},N:a.parseNumber,T:a.parseLengthOrPercent,L:a.parseLength}[r.toUpperCase()](q):{a:m,n:k[0],t:l}[r],void 0===p)return;k.push(p)}if(e.push({t:g,d:k}),d.lastIndex==b.length)return e}}function f(a){return a.toFixed(6).replace(".000000","")}function g(b,c){if(b.decompositionPair!==c){b.decompositionPair=c;var d=a.makeMatrixDecomposition(b)}if(c.decompositionPair!==b){c.decompositionPair=b;var e=a.makeMatrixDecomposition(c)}return null==d[0]||null==e[0]?[[!1],[!0],function(a){return a?c[0].d:b[0].d}]:(d[0].push(0),e[0].push(1),[d,e,function(b){var c=a.quat(d[0][3],e[0][3],b[5]),g=a.composeMatrix(b[0],b[1],b[2],c,b[4]),h=g.map(f).join(",");return h}])}function h(a){return a.replace(/[xy]/,"")}function i(a){return a.replace(/(x|y|z|3d)?$/,"3d")}function j(b,c){var d=a.makeMatrixDecomposition&&!0,e=!1;if(!b.length||!c.length){b.length||(e=!0,b=c,c=[]);for(var f=0;f<b.length;f++){var j=b[f].t,k=b[f].d,l="scale"==j.substr(0,5)?1:0;c.push({t:j,d:k.map(function(a){if("number"==typeof a)return l;var b={};for(var c in a)b[c]=l;return b})})}}var m=function(a,b){return"perspective"==a&&"perspective"==b||("matrix"==a||"matrix3d"==a)&&("matrix"==b||"matrix3d"==b)},o=[],p=[],q=[];if(b.length!=c.length){if(!d)return;var r=g(b,c);o=[r[0]],p=[r[1]],q=[["matrix",[r[2]]]]}else for(var f=0;f<b.length;f++){var j,s=b[f].t,t=c[f].t,u=b[f].d,v=c[f].d,w=n[s],x=n[t];if(m(s,t)){if(!d)return;var r=g([b[f]],[c[f]]);o.push(r[0]),p.push(r[1]),q.push(["matrix",[r[2]]])}else{if(s==t)j=s;else if(w[2]&&x[2]&&h(s)==h(t))j=h(s),u=w[2](u),v=x[2](v);else{if(!w[1]||!x[1]||i(s)!=i(t)){if(!d)return;var r=g(b,c);o=[r[0]],p=[r[1]],q=[["matrix",[r[2]]]];break}j=i(s),u=w[1](u),v=x[1](v)}for(var y=[],z=[],A=[],B=0;B<u.length;B++){var C="number"==typeof u[B]?a.mergeNumbers:a.mergeDimensions,r=C(u[B],v[B]);y[B]=r[0],z[B]=r[1],A.push(r[2])}o.push(y),p.push(z),q.push([j,A])}}if(e){var D=o;o=p,p=D}return[o,p,function(a){return a.map(function(a,b){var c=a.map(function(a,c){return q[b][1][c](a)}).join(",");return"matrix"==q[b][0]&&16==c.split(",").length&&(q[b][0]="matrix3d"),q[b][0]+"("+c+")"}).join(" ")}]}var k=null,l={px:0},m={deg:0},n={matrix:["NNNNNN",[k,k,0,0,k,k,0,0,0,0,1,0,k,k,0,1],d],matrix3d:["NNNNNNNNNNNNNNNN",d],rotate:["A"],rotatex:["A"],rotatey:["A"],rotatez:["A"],rotate3d:["NNNA"],perspective:["L"],scale:["Nn",c([k,k,1]),d],scalex:["N",c([k,1,1]),c([k,1])],scaley:["N",c([1,k,1]),c([1,k])],scalez:["N",c([1,1,k])],scale3d:["NNN",d],skew:["Aa",null,d],skewx:["A",null,c([k,m])],skewy:["A",null,c([m,k])],translate:["Tt",c([k,k,l]),d],translatex:["T",c([k,l,l]),c([k,l])],translatey:["T",c([l,k,l]),c([l,k])],translatez:["L",c([l,l,k])],translate3d:["TTL",d]};a.addPropertiesHandler(e,j,["transform"])}(d,f),function(a,b){function c(a,b){b.concat([a]).forEach(function(b){b in document.documentElement.style&&(d[a]=b)})}var d={};c("transform",["webkitTransform","msTransform"]),c("transformOrigin",["webkitTransformOrigin"]),c("perspective",["webkitPerspective"]),c("perspectiveOrigin",["webkitPerspectiveOrigin"]),a.propertyName=function(a){return d[a]||a}}(d,f)}(),!function(){if(void 0===document.createElement("div").animate([]).oncancel){var a;if(window.performance&&performance.now)var a=function(){return performance.now()};else var a=function(){return Date.now()};var b=function(a,b,c){this.target=a,this.currentTime=b,this.timelineTime=c,this.type="cancel",this.bubbles=!1,this.cancelable=!1,
this.currentTarget=a,this.defaultPrevented=!1,this.eventPhase=Event.AT_TARGET,this.timeStamp=Date.now()},c=window.Element.prototype.animate;window.Element.prototype.animate=function(d,e){var f=c.call(this,d,e);f._cancelHandlers=[],f.oncancel=null;var g=f.cancel;f.cancel=function(){g.call(this);var c=new b(this,null,a()),d=this._cancelHandlers.concat(this.oncancel?[this.oncancel]:[]);setTimeout(function(){d.forEach(function(a){a.call(c.target,c)})},0)};var h=f.addEventListener;f.addEventListener=function(a,b){"function"==typeof b&&"cancel"==a?this._cancelHandlers.push(b):h.call(this,a,b)};var i=f.removeEventListener;return f.removeEventListener=function(a,b){if("cancel"==a){var c=this._cancelHandlers.indexOf(b);c>=0&&this._cancelHandlers.splice(c,1)}else i.call(this,a,b)},f}}}(),function(a){var b=document.documentElement,c=null,d=!1;try{var e=getComputedStyle(b).getPropertyValue("opacity"),f="0"==e?"1":"0";c=b.animate({opacity:[f,f]},{duration:1}),c.currentTime=0,d=getComputedStyle(b).getPropertyValue("opacity")==f}catch(a){}finally{c&&c.cancel()}if(!d){var g=window.Element.prototype.animate;window.Element.prototype.animate=function(b,c){return window.Symbol&&Symbol.iterator&&Array.prototype.from&&b[Symbol.iterator]&&(b=Array.from(b)),Array.isArray(b)||null===b||(b=a.convertToArrayForm(b)),g.call(this,b,c)}}}(c),!function(a,b,c){function d(a){var c=b.timeline;c.currentTime=a,c._discardAnimations(),0==c._animations.length?f=!1:requestAnimationFrame(d)}var e=window.requestAnimationFrame;window.requestAnimationFrame=function(a){return e(function(c){b.timeline._updateAnimationsPromises(),a(c),b.timeline._updateAnimationsPromises()})},b.AnimationTimeline=function(){this._animations=[],this.currentTime=void 0},b.AnimationTimeline.prototype={getAnimations:function(){return this._discardAnimations(),this._animations.slice()},_updateAnimationsPromises:function(){b.animationsWithPromises=b.animationsWithPromises.filter(function(a){return a._updatePromises()})},_discardAnimations:function(){this._updateAnimationsPromises(),this._animations=this._animations.filter(function(a){return"finished"!=a.playState&&"idle"!=a.playState})},_play:function(a){var c=new b.Animation(a,this);return this._animations.push(c),b.restartWebAnimationsNextTick(),c._updatePromises(),c._animation.play(),c._updatePromises(),c},play:function(a){return a&&a.remove(),this._play(a)}};var f=!1;b.restartWebAnimationsNextTick=function(){f||(f=!0,requestAnimationFrame(d))};var g=new b.AnimationTimeline;b.timeline=g;try{Object.defineProperty(window.document,"timeline",{configurable:!0,get:function(){return g}})}catch(a){}try{window.document.timeline=g}catch(a){}}(c,e,f),function(a,b,c){b.animationsWithPromises=[],b.Animation=function(b,c){if(this.id="",b&&b._id&&(this.id=b._id),this.effect=b,b&&(b._animation=this),!c)throw new Error("Animation with null timeline is not supported");this._timeline=c,this._sequenceNumber=a.sequenceNumber++,this._holdTime=0,this._paused=!1,this._isGroup=!1,this._animation=null,this._childAnimations=[],this._callback=null,this._oldPlayState="idle",this._rebuildUnderlyingAnimation(),this._animation.cancel(),this._updatePromises()},b.Animation.prototype={_updatePromises:function(){var a=this._oldPlayState,b=this.playState;return this._readyPromise&&b!==a&&("idle"==b?(this._rejectReadyPromise(),this._readyPromise=void 0):"pending"==a?this._resolveReadyPromise():"pending"==b&&(this._readyPromise=void 0)),this._finishedPromise&&b!==a&&("idle"==b?(this._rejectFinishedPromise(),this._finishedPromise=void 0):"finished"==b?this._resolveFinishedPromise():"finished"==a&&(this._finishedPromise=void 0)),this._oldPlayState=this.playState,this._readyPromise||this._finishedPromise},_rebuildUnderlyingAnimation:function(){this._updatePromises();var a,c,d,e,f=!!this._animation;f&&(a=this.playbackRate,c=this._paused,d=this.startTime,e=this.currentTime,this._animation.cancel(),this._animation._wrapper=null,this._animation=null),(!this.effect||this.effect instanceof window.KeyframeEffect)&&(this._animation=b.newUnderlyingAnimationForKeyframeEffect(this.effect),b.bindAnimationForKeyframeEffect(this)),(this.effect instanceof window.SequenceEffect||this.effect instanceof window.GroupEffect)&&(this._animation=b.newUnderlyingAnimationForGroup(this.effect),b.bindAnimationForGroup(this)),this.effect&&this.effect._onsample&&b.bindAnimationForCustomEffect(this),f&&(1!=a&&(this.playbackRate=a),null!==d?this.startTime=d:null!==e?this.currentTime=e:null!==this._holdTime&&(this.currentTime=this._holdTime),c&&this.pause()),this._updatePromises()},_updateChildren:function(){if(this.effect&&"idle"!=this.playState){var a=this.effect._timing.delay;this._childAnimations.forEach(function(c){this._arrangeChildren(c,a),this.effect instanceof window.SequenceEffect&&(a+=b.groupChildDuration(c.effect))}.bind(this))}},_setExternalAnimation:function(a){if(this.effect&&this._isGroup)for(var b=0;b<this.effect.children.length;b++)this.effect.children[b]._animation=a,this._childAnimations[b]._setExternalAnimation(a)},_constructChildAnimations:function(){if(this.effect&&this._isGroup){var a=this.effect._timing.delay;this._removeChildAnimations(),this.effect.children.forEach(function(c){var d=b.timeline._play(c);this._childAnimations.push(d),d.playbackRate=this.playbackRate,this._paused&&d.pause(),c._animation=this.effect._animation,this._arrangeChildren(d,a),this.effect instanceof window.SequenceEffect&&(a+=b.groupChildDuration(c))}.bind(this))}},_arrangeChildren:function(a,b){null===this.startTime?a.currentTime=this.currentTime-b/this.playbackRate:a.startTime!==this.startTime+b/this.playbackRate&&(a.startTime=this.startTime+b/this.playbackRate)},get timeline(){return this._timeline},get playState(){return this._animation?this._animation.playState:"idle"},get finished(){return window.Promise?(this._finishedPromise||(b.animationsWithPromises.indexOf(this)==-1&&b.animationsWithPromises.push(this),this._finishedPromise=new Promise(function(a,b){this._resolveFinishedPromise=function(){a(this)},this._rejectFinishedPromise=function(){b({type:DOMException.ABORT_ERR,name:"AbortError"})}}.bind(this)),"finished"==this.playState&&this._resolveFinishedPromise()),this._finishedPromise):(console.warn("Animation Promises require JavaScript Promise constructor"),null)},get ready(){return window.Promise?(this._readyPromise||(b.animationsWithPromises.indexOf(this)==-1&&b.animationsWithPromises.push(this),this._readyPromise=new Promise(function(a,b){this._resolveReadyPromise=function(){a(this)},this._rejectReadyPromise=function(){b({type:DOMException.ABORT_ERR,name:"AbortError"})}}.bind(this)),"pending"!==this.playState&&this._resolveReadyPromise()),this._readyPromise):(console.warn("Animation Promises require JavaScript Promise constructor"),null)},get onfinish(){return this._animation.onfinish},set onfinish(a){"function"==typeof a?this._animation.onfinish=function(b){b.target=this,a.call(this,b)}.bind(this):this._animation.onfinish=a},get oncancel(){return this._animation.oncancel},set oncancel(a){"function"==typeof a?this._animation.oncancel=function(b){b.target=this,a.call(this,b)}.bind(this):this._animation.oncancel=a},get currentTime(){this._updatePromises();var a=this._animation.currentTime;return this._updatePromises(),a},set currentTime(a){this._updatePromises(),this._animation.currentTime=isFinite(a)?a:Math.sign(a)*Number.MAX_VALUE,this._register(),this._forEachChild(function(b,c){b.currentTime=a-c}),this._updatePromises()},get startTime(){return this._animation.startTime},set startTime(a){this._updatePromises(),this._animation.startTime=isFinite(a)?a:Math.sign(a)*Number.MAX_VALUE,this._register(),this._forEachChild(function(b,c){b.startTime=a+c}),this._updatePromises()},get playbackRate(){return this._animation.playbackRate},set playbackRate(a){this._updatePromises();var b=this.currentTime;this._animation.playbackRate=a,this._forEachChild(function(b){b.playbackRate=a}),null!==b&&(this.currentTime=b),this._updatePromises()},play:function(){this._updatePromises(),this._paused=!1,this._animation.play(),this._timeline._animations.indexOf(this)==-1&&this._timeline._animations.push(this),this._register(),b.awaitStartTime(this),this._forEachChild(function(a){var b=a.currentTime;a.play(),a.currentTime=b}),this._updatePromises()},pause:function(){this._updatePromises(),this.currentTime&&(this._holdTime=this.currentTime),this._animation.pause(),this._register(),this._forEachChild(function(a){a.pause()}),this._paused=!0,this._updatePromises()},finish:function(){this._updatePromises(),this._animation.finish(),this._register(),this._updatePromises()},cancel:function(){this._updatePromises(),this._animation.cancel(),this._register(),this._removeChildAnimations(),this._updatePromises()},reverse:function(){this._updatePromises();var a=this.currentTime;this._animation.reverse(),this._forEachChild(function(a){a.reverse()}),null!==a&&(this.currentTime=a),this._updatePromises()},addEventListener:function(a,b){var c=b;"function"==typeof b&&(c=function(a){a.target=this,b.call(this,a)}.bind(this),b._wrapper=c),this._animation.addEventListener(a,c)},removeEventListener:function(a,b){this._animation.removeEventListener(a,b&&b._wrapper||b)},_removeChildAnimations:function(){for(;this._childAnimations.length;)this._childAnimations.pop().cancel()},_forEachChild:function(b){var c=0;if(this.effect.children&&this._childAnimations.length<this.effect.children.length&&this._constructChildAnimations(),this._childAnimations.forEach(function(a){b.call(this,a,c),this.effect instanceof window.SequenceEffect&&(c+=a.effect.activeDuration)}.bind(this)),"pending"!=this.playState){var d=this.effect._timing,e=this.currentTime;null!==e&&(e=a.calculateIterationProgress(a.calculateActiveDuration(d),e,d)),(null==e||isNaN(e))&&this._removeChildAnimations()}}},window.Animation=b.Animation}(c,e,f),function(a,b,c){function d(b){this._frames=a.normalizeKeyframes(b)}function e(){for(var a=!1;i.length;){var b=i.shift();b._updateChildren(),a=!0}return a}var f=function(a){if(a._animation=void 0,a instanceof window.SequenceEffect||a instanceof window.GroupEffect)for(var b=0;b<a.children.length;b++)f(a.children[b])};b.removeMulti=function(a){for(var b=[],c=0;c<a.length;c++){var d=a[c];d._parent?(b.indexOf(d._parent)==-1&&b.push(d._parent),d._parent.children.splice(d._parent.children.indexOf(d),1),d._parent=null,f(d)):d._animation&&d._animation.effect==d&&(d._animation.cancel(),d._animation.effect=new KeyframeEffect(null,[]),d._animation._callback&&(d._animation._callback._animation=null),d._animation._rebuildUnderlyingAnimation(),f(d))}for(c=0;c<b.length;c++)b[c]._rebuild()},b.KeyframeEffect=function(b,c,e,f){return this.target=b,this._parent=null,e=a.numericTimingToObject(e),this._timingInput=a.cloneTimingInput(e),this._timing=a.normalizeTimingInput(e),this.timing=a.makeTiming(e,!1,this),this.timing._effect=this,"function"==typeof c?(a.deprecated("Custom KeyframeEffect","2015-06-22","Use KeyframeEffect.onsample instead."),this._normalizedKeyframes=c):this._normalizedKeyframes=new d(c),this._keyframes=c,this.activeDuration=a.calculateActiveDuration(this._timing),this._id=f,this},b.KeyframeEffect.prototype={getFrames:function(){return"function"==typeof this._normalizedKeyframes?this._normalizedKeyframes:this._normalizedKeyframes._frames},set onsample(a){if("function"==typeof this.getFrames())throw new Error("Setting onsample on custom effect KeyframeEffect is not supported.");this._onsample=a,this._animation&&this._animation._rebuildUnderlyingAnimation()},get parent(){return this._parent},clone:function(){if("function"==typeof this.getFrames())throw new Error("Cloning custom effects is not supported.");var b=new KeyframeEffect(this.target,[],a.cloneTimingInput(this._timingInput),this._id);return b._normalizedKeyframes=this._normalizedKeyframes,b._keyframes=this._keyframes,b},remove:function(){b.removeMulti([this])}};var g=Element.prototype.animate;Element.prototype.animate=function(a,c){var d="";return c&&c.id&&(d=c.id),b.timeline._play(new b.KeyframeEffect(this,a,c,d))};var h=document.createElementNS("http://www.w3.org/1999/xhtml","div");b.newUnderlyingAnimationForKeyframeEffect=function(a){if(a){var b=a.target||h,c=a._keyframes;"function"==typeof c&&(c=[]);var d=a._timingInput;d.id=a._id}else var b=h,c=[],d=0;return g.apply(b,[c,d])},b.bindAnimationForKeyframeEffect=function(a){a.effect&&"function"==typeof a.effect._normalizedKeyframes&&b.bindAnimationForCustomEffect(a)};var i=[];b.awaitStartTime=function(a){null===a.startTime&&a._isGroup&&(0==i.length&&requestAnimationFrame(e),i.push(a))};var j=window.getComputedStyle;Object.defineProperty(window,"getComputedStyle",{configurable:!0,enumerable:!0,value:function(){b.timeline._updateAnimationsPromises();var a=j.apply(this,arguments);return e()&&(a=j.apply(this,arguments)),b.timeline._updateAnimationsPromises(),a}}),window.KeyframeEffect=b.KeyframeEffect,window.Element.prototype.getAnimations=function(){return document.timeline.getAnimations().filter(function(a){return null!==a.effect&&a.effect.target==this}.bind(this))}}(c,e,f),function(a,b,c){function d(a){a._registered||(a._registered=!0,g.push(a),h||(h=!0,requestAnimationFrame(e)))}function e(a){var b=g;g=[],b.sort(function(a,b){return a._sequenceNumber-b._sequenceNumber}),b=b.filter(function(a){a();var b=a._animation?a._animation.playState:"idle";return"running"!=b&&"pending"!=b&&(a._registered=!1),a._registered}),g.push.apply(g,b),g.length?(h=!0,requestAnimationFrame(e)):h=!1}var f=(document.createElementNS("http://www.w3.org/1999/xhtml","div"),0);b.bindAnimationForCustomEffect=function(b){var c,e=b.effect.target,g="function"==typeof b.effect.getFrames();c=g?b.effect.getFrames():b.effect._onsample;var h=b.effect.timing,i=null;h=a.normalizeTimingInput(h);var j=function(){var d=j._animation?j._animation.currentTime:null;null!==d&&(d=a.calculateIterationProgress(a.calculateActiveDuration(h),d,h),isNaN(d)&&(d=null)),d!==i&&(g?c(d,e,b.effect):c(d,b.effect,b.effect._animation)),i=d};j._animation=b,j._registered=!1,j._sequenceNumber=f++,b._callback=j,d(j)};var g=[],h=!1;b.Animation.prototype._register=function(){this._callback&&d(this._callback)}}(c,e,f),function(a,b,c){function d(a){return a._timing.delay+a.activeDuration+a._timing.endDelay}function e(b,c,d){this._id=d,this._parent=null,this.children=b||[],this._reparent(this.children),c=a.numericTimingToObject(c),this._timingInput=a.cloneTimingInput(c),this._timing=a.normalizeTimingInput(c,!0),this.timing=a.makeTiming(c,!0,this),this.timing._effect=this,"auto"===this._timing.duration&&(this._timing.duration=this.activeDuration)}window.SequenceEffect=function(){e.apply(this,arguments)},window.GroupEffect=function(){e.apply(this,arguments)},e.prototype={_isAncestor:function(a){for(var b=this;null!==b;){if(b==a)return!0;b=b._parent}return!1},_rebuild:function(){for(var a=this;a;)"auto"===a.timing.duration&&(a._timing.duration=a.activeDuration),a=a._parent;this._animation&&this._animation._rebuildUnderlyingAnimation()},_reparent:function(a){b.removeMulti(a);for(var c=0;c<a.length;c++)a[c]._parent=this},_putChild:function(a,b){for(var c=b?"Cannot append an ancestor or self":"Cannot prepend an ancestor or self",d=0;d<a.length;d++)if(this._isAncestor(a[d]))throw{type:DOMException.HIERARCHY_REQUEST_ERR,name:"HierarchyRequestError",message:c};for(var d=0;d<a.length;d++)b?this.children.push(a[d]):this.children.unshift(a[d]);this._reparent(a),this._rebuild()},append:function(){this._putChild(arguments,!0)},prepend:function(){this._putChild(arguments,!1)},get parent(){return this._parent},get firstChild(){return this.children.length?this.children[0]:null},get lastChild(){return this.children.length?this.children[this.children.length-1]:null},clone:function(){for(var b=a.cloneTimingInput(this._timingInput),c=[],d=0;d<this.children.length;d++)c.push(this.children[d].clone());return this instanceof GroupEffect?new GroupEffect(c,b):new SequenceEffect(c,b)},remove:function(){b.removeMulti([this])}},window.SequenceEffect.prototype=Object.create(e.prototype),Object.defineProperty(window.SequenceEffect.prototype,"activeDuration",{get:function(){var a=0;return this.children.forEach(function(b){a+=d(b)}),Math.max(a,0)}}),window.GroupEffect.prototype=Object.create(e.prototype),Object.defineProperty(window.GroupEffect.prototype,"activeDuration",{get:function(){var a=0;return this.children.forEach(function(b){a=Math.max(a,d(b))}),a}}),b.newUnderlyingAnimationForGroup=function(c){var d,e=null,f=function(b){var c=d._wrapper;if(c&&"pending"!=c.playState&&c.effect)return null==b?void c._removeChildAnimations():0==b&&c.playbackRate<0&&(e||(e=a.normalizeTimingInput(c.effect.timing)),b=a.calculateIterationProgress(a.calculateActiveDuration(e),-1,e),isNaN(b)||null==b)?(c._forEachChild(function(a){a.currentTime=-1}),void c._removeChildAnimations()):void 0},g=new KeyframeEffect(null,[],c._timing,c._id);return g.onsample=f,d=b.timeline._play(g)},b.bindAnimationForGroup=function(a){a._animation._wrapper=a,a._isGroup=!0,b.awaitStartTime(a),a._constructChildAnimations(),a._setExternalAnimation(a)},b.groupChildDuration=d}(c,e,f),b.true=a}({},function(){return this}());
//# sourceMappingURL=web-animations-next-lite.min.js.map
Polymer({

    is: 'opaque-animation',

    behaviors: [
      Polymer.NeonAnimationBehavior
    ],

    configure: function(config) {
      var node = config.node;
      this._effect = new KeyframeEffect(node, [
        {'opacity': '1'},
        {'opacity': '1'}
      ], this.timingFromConfig(config));
      node.style.opacity = '0';
      return this._effect;
    },

    complete: function(config) {
      config.node.style.opacity = '';
    }

  });
(function() {
    'use strict';
    /**
     * Used to calculate the scroll direction during touch events.
     * @type {!Object}
     */
    var lastTouchPosition = {
      pageX: 0,
      pageY: 0
    };
    /**
     * Used to avoid computing event.path and filter scrollable nodes (better perf).
     * @type {?EventTarget}
     */
    var lastRootTarget = null;
    /**
     * @type {!Array<Node>}
     */
    var lastScrollableNodes = [];

    /**
     * The IronDropdownScrollManager is intended to provide a central source
     * of authority and control over which elements in a document are currently
     * allowed to scroll.
     */

    Polymer.IronDropdownScrollManager = {

      /**
       * The current element that defines the DOM boundaries of the
       * scroll lock. This is always the most recently locking element.
       */
      get currentLockingElement() {
        return this._lockingElements[this._lockingElements.length - 1];
      },

      /**
       * Returns true if the provided element is "scroll locked", which is to
       * say that it cannot be scrolled via pointer or keyboard interactions.
       *
       * @param {HTMLElement} element An HTML element instance which may or may
       * not be scroll locked.
       */
      elementIsScrollLocked: function(element) {
        var currentLockingElement = this.currentLockingElement;

        if (currentLockingElement === undefined)
          return false;

        var scrollLocked;

        if (this._hasCachedLockedElement(element)) {
          return true;
        }

        if (this._hasCachedUnlockedElement(element)) {
          return false;
        }

        scrollLocked = !!currentLockingElement &&
          currentLockingElement !== element &&
          !this._composedTreeContains(currentLockingElement, element);

        if (scrollLocked) {
          this._lockedElementCache.push(element);
        } else {
          this._unlockedElementCache.push(element);
        }

        return scrollLocked;
      },

      /**
       * Push an element onto the current scroll lock stack. The most recently
       * pushed element and its children will be considered scrollable. All
       * other elements will not be scrollable.
       *
       * Scroll locking is implemented as a stack so that cases such as
       * dropdowns within dropdowns are handled well.
       *
       * @param {HTMLElement} element The element that should lock scroll.
       */
      pushScrollLock: function(element) {
        // Prevent pushing the same element twice
        if (this._lockingElements.indexOf(element) >= 0) {
          return;
        }

        if (this._lockingElements.length === 0) {
          this._lockScrollInteractions();
        }

        this._lockingElements.push(element);

        this._lockedElementCache = [];
        this._unlockedElementCache = [];
      },

      /**
       * Remove an element from the scroll lock stack. The element being
       * removed does not need to be the most recently pushed element. However,
       * the scroll lock constraints only change when the most recently pushed
       * element is removed.
       *
       * @param {HTMLElement} element The element to remove from the scroll
       * lock stack.
       */
      removeScrollLock: function(element) {
        var index = this._lockingElements.indexOf(element);

        if (index === -1) {
          return;
        }

        this._lockingElements.splice(index, 1);

        this._lockedElementCache = [];
        this._unlockedElementCache = [];

        if (this._lockingElements.length === 0) {
          this._unlockScrollInteractions();
        }
      },

      _lockingElements: [],

      _lockedElementCache: null,

      _unlockedElementCache: null,

      _hasCachedLockedElement: function(element) {
        return this._lockedElementCache.indexOf(element) > -1;
      },

      _hasCachedUnlockedElement: function(element) {
        return this._unlockedElementCache.indexOf(element) > -1;
      },

      _composedTreeContains: function(element, child) {
        // NOTE(cdata): This method iterates over content elements and their
        // corresponding distributed nodes to implement a contains-like method
        // that pierces through the composed tree of the ShadowDOM. Results of
        // this operation are cached (elsewhere) on a per-scroll-lock basis, to
        // guard against potentially expensive lookups happening repeatedly as
        // a user scrolls / touchmoves.
        var contentElements;
        var distributedNodes;
        var contentIndex;
        var nodeIndex;

        if (element.contains(child)) {
          return true;
        }

        contentElements = Polymer.dom(element).querySelectorAll('content');

        for (contentIndex = 0; contentIndex < contentElements.length; ++contentIndex) {

          distributedNodes = Polymer.dom(contentElements[contentIndex]).getDistributedNodes();

          for (nodeIndex = 0; nodeIndex < distributedNodes.length; ++nodeIndex) {

            if (this._composedTreeContains(distributedNodes[nodeIndex], child)) {
              return true;
            }
          }
        }

        return false;
      },

      _scrollInteractionHandler: function(event) {
        // Avoid canceling an event with cancelable=false, e.g. scrolling is in
        // progress and cannot be interrupted.
        if (event.cancelable && this._shouldPreventScrolling(event)) {
          event.preventDefault();
        }
        // If event has targetTouches (touch event), update last touch position.
        if (event.targetTouches) {
          var touch = event.targetTouches[0];
          lastTouchPosition.pageX = touch.pageX;
          lastTouchPosition.pageY = touch.pageY;
        }
      },

      _lockScrollInteractions: function() {
        this._boundScrollHandler = this._boundScrollHandler ||
          this._scrollInteractionHandler.bind(this);
        // Modern `wheel` event for mouse wheel scrolling:
        document.addEventListener('wheel', this._boundScrollHandler, true);
        // Older, non-standard `mousewheel` event for some FF:
        document.addEventListener('mousewheel', this._boundScrollHandler, true);
        // IE:
        document.addEventListener('DOMMouseScroll', this._boundScrollHandler, true);
        // Save the lastScrollableNodes on touchstart, to be used on touchmove.
        document.addEventListener('touchstart', this._boundScrollHandler, true);
        // Mobile devices can scroll on touch move:
        document.addEventListener('touchmove', this._boundScrollHandler, true);
      },

      _unlockScrollInteractions: function() {
        document.removeEventListener('wheel', this._boundScrollHandler, true);
        document.removeEventListener('mousewheel', this._boundScrollHandler, true);
        document.removeEventListener('DOMMouseScroll', this._boundScrollHandler, true);
        document.removeEventListener('touchstart', this._boundScrollHandler, true);
        document.removeEventListener('touchmove', this._boundScrollHandler, true);
      },

      /**
       * Returns true if the event causes scroll outside the current locking
       * element, e.g. pointer/keyboard interactions, or scroll "leaking"
       * outside the locking element when it is already at its scroll boundaries.
       * @param {!Event} event
       * @return {boolean}
       * @private
       */
      _shouldPreventScrolling: function(event) {

        // Update if root target changed. For touch events, ensure we don't
        // update during touchmove.
        var target = Polymer.dom(event).rootTarget;
        if (event.type !== 'touchmove' && lastRootTarget !== target) {
          lastRootTarget = target;
          lastScrollableNodes = this._getScrollableNodes(Polymer.dom(event).path);
        }

        // Prevent event if no scrollable nodes.
        if (!lastScrollableNodes.length) {
          return true;
        }
        // Don't prevent touchstart event inside the locking element when it has
        // scrollable nodes.
        if (event.type === 'touchstart') {
          return false;
        }
        // Get deltaX/Y.
        var info = this._getScrollInfo(event);
        // Prevent if there is no child that can scroll.
        return !this._getScrollingNode(lastScrollableNodes, info.deltaX, info.deltaY);
      },

      /**
       * Returns an array of scrollable nodes up to the current locking element,
       * which is included too if scrollable.
       * @param {!Array<Node>} nodes
       * @return {Array<Node>} scrollables
       * @private
       */
      _getScrollableNodes: function(nodes) {
        var scrollables = [];
        var lockingIndex = nodes.indexOf(this.currentLockingElement);
        // Loop from root target to locking element (included).
        for (var i = 0; i <= lockingIndex; i++) {
          // Skip non-Element nodes.
          if (nodes[i].nodeType !== Node.ELEMENT_NODE) {
            continue;
          }
          var node = /** @type {!Element} */ (nodes[i]);
          // Check inline style before checking computed style.
          var style = node.style;
          if (style.overflow !== 'scroll' && style.overflow !== 'auto') {
            style = window.getComputedStyle(node);
          }
          if (style.overflow === 'scroll' || style.overflow === 'auto') {
            scrollables.push(node);
          }
        }
        return scrollables;
      },

      /**
       * Returns the node that is scrolling. If there is no scrolling,
       * returns undefined.
       * @param {!Array<Node>} nodes
       * @param {number} deltaX Scroll delta on the x-axis
       * @param {number} deltaY Scroll delta on the y-axis
       * @return {Node|undefined}
       * @private
       */
      _getScrollingNode: function(nodes, deltaX, deltaY) {
        // No scroll.
        if (!deltaX && !deltaY) {
          return;
        }
        // Check only one axis according to where there is more scroll.
        // Prefer vertical to horizontal.
        var verticalScroll = Math.abs(deltaY) >= Math.abs(deltaX);
        for (var i = 0; i < nodes.length; i++) {
          var node = nodes[i];
          var canScroll = false;
          if (verticalScroll) {
            // delta < 0 is scroll up, delta > 0 is scroll down.
            canScroll = deltaY < 0 ? node.scrollTop > 0 :
              node.scrollTop < node.scrollHeight - node.clientHeight;
          } else {
            // delta < 0 is scroll left, delta > 0 is scroll right.
            canScroll = deltaX < 0 ? node.scrollLeft > 0 :
              node.scrollLeft < node.scrollWidth - node.clientWidth;
          }
          if (canScroll) {
            return node;
          }
        }
      },

      /**
       * Returns scroll `deltaX` and `deltaY`.
       * @param {!Event} event The scroll event
       * @return {{deltaX: number, deltaY: number}} Object containing the
       * x-axis scroll delta (positive: scroll right, negative: scroll left,
       * 0: no scroll), and the y-axis scroll delta (positive: scroll down,
       * negative: scroll up, 0: no scroll).
       * @private
       */
      _getScrollInfo: function(event) {
        var info = {
          deltaX: event.deltaX,
          deltaY: event.deltaY
        };
        // Already available.
        if ('deltaX' in event) {
          // do nothing, values are already good.
        }
        // Safari has scroll info in `wheelDeltaX/Y`.
        else if ('wheelDeltaX' in event) {
          info.deltaX = -event.wheelDeltaX;
          info.deltaY = -event.wheelDeltaY;
        }
        // Firefox has scroll info in `detail` and `axis`.
        else if ('axis' in event) {
          info.deltaX = event.axis === 1 ? event.detail : 0;
          info.deltaY = event.axis === 2 ? event.detail : 0;
        }
        // On mobile devices, calculate scroll direction.
        else if (event.targetTouches) {
          var touch = event.targetTouches[0];
          // Touch moves from right to left => scrolling goes right.
          info.deltaX = lastTouchPosition.pageX - touch.pageX;
          // Touch moves from down to up => scrolling goes down.
          info.deltaY = lastTouchPosition.pageY - touch.pageY;
        }
        return info;
      }
    };
  })();
(function() {
      'use strict';

      Polymer({
        is: 'iron-dropdown',

        behaviors: [
          Polymer.IronControlState,
          Polymer.IronA11yKeysBehavior,
          Polymer.IronOverlayBehavior,
          Polymer.NeonAnimationRunnerBehavior
        ],

        properties: {
          /**
           * The orientation against which to align the dropdown content
           * horizontally relative to the dropdown trigger.
           * Overridden from `Polymer.IronFitBehavior`.
           */
          horizontalAlign: {
            type: String,
            value: 'left',
            reflectToAttribute: true
          },

          /**
           * The orientation against which to align the dropdown content
           * vertically relative to the dropdown trigger.
           * Overridden from `Polymer.IronFitBehavior`.
           */
          verticalAlign: {
            type: String,
            value: 'top',
            reflectToAttribute: true
          },

          /**
           * An animation config. If provided, this will be used to animate the
           * opening of the dropdown. Pass an Array for multiple animations.
           * See `neon-animation` documentation for more animation configuration
           * details.
           */
          openAnimationConfig: {
            type: Object
          },

          /**
           * An animation config. If provided, this will be used to animate the
           * closing of the dropdown. Pass an Array for multiple animations.
           * See `neon-animation` documentation for more animation configuration
           * details.
           */
          closeAnimationConfig: {
            type: Object
          },

          /**
           * If provided, this will be the element that will be focused when
           * the dropdown opens.
           */
          focusTarget: {
            type: Object
          },

          /**
           * Set to true to disable animations when opening and closing the
           * dropdown.
           */
          noAnimations: {
            type: Boolean,
            value: false
          },

          /**
           * By default, the dropdown will constrain scrolling on the page
           * to itself when opened.
           * Set to true in order to prevent scroll from being constrained
           * to the dropdown when it opens.
           */
          allowOutsideScroll: {
            type: Boolean,
            value: false
          },

          /**
           * Callback for scroll events.
           * @type {Function}
           * @private
           */
          _boundOnCaptureScroll: {
            type: Function,
            value: function() {
              return this._onCaptureScroll.bind(this);
            }
          }
        },

        listeners: {
          'neon-animation-finish': '_onNeonAnimationFinish'
        },

        observers: [
          '_updateOverlayPosition(positionTarget, verticalAlign, horizontalAlign, verticalOffset, horizontalOffset)'
        ],

        /**
         * The element that is contained by the dropdown, if any.
         */
        get containedElement() {
          return Polymer.dom(this.$.content).getDistributedNodes()[0];
        },

        /**
         * The element that should be focused when the dropdown opens.
         * @deprecated
         */
        get _focusTarget() {
          return this.focusTarget || this.containedElement;
        },

        ready: function() {
          // Memoized scrolling position, used to block scrolling outside.
          this._scrollTop = 0;
          this._scrollLeft = 0;
          // Used to perform a non-blocking refit on scroll.
          this._refitOnScrollRAF = null;
        },

        attached: function () {
          if (!this.sizingTarget || this.sizingTarget === this) {
            this.sizingTarget = this.containedElement || this;
          }
        },

        detached: function() {
          this.cancelAnimation();
          document.removeEventListener('scroll', this._boundOnCaptureScroll);
          Polymer.IronDropdownScrollManager.removeScrollLock(this);
        },

        /**
         * Called when the value of `opened` changes.
         * Overridden from `IronOverlayBehavior`
         */
        _openedChanged: function() {
          if (this.opened && this.disabled) {
            this.cancel();
          } else {
            this.cancelAnimation();
            this._updateAnimationConfig();
            this._saveScrollPosition();
            if (this.opened) {
              document.addEventListener('scroll', this._boundOnCaptureScroll);
              !this.allowOutsideScroll && Polymer.IronDropdownScrollManager.pushScrollLock(this);
            } else {
              document.removeEventListener('scroll', this._boundOnCaptureScroll);
              Polymer.IronDropdownScrollManager.removeScrollLock(this);
            }
            Polymer.IronOverlayBehaviorImpl._openedChanged.apply(this, arguments);
          }
        },

        /**
         * Overridden from `IronOverlayBehavior`.
         */
        _renderOpened: function() {
          if (!this.noAnimations && this.animationConfig.open) {
            this.$.contentWrapper.classList.add('animating');
            this.playAnimation('open');
          } else {
            Polymer.IronOverlayBehaviorImpl._renderOpened.apply(this, arguments);
          }
        },

        /**
         * Overridden from `IronOverlayBehavior`.
         */
        _renderClosed: function() {

          if (!this.noAnimations && this.animationConfig.close) {
            this.$.contentWrapper.classList.add('animating');
            this.playAnimation('close');
          } else {
            Polymer.IronOverlayBehaviorImpl._renderClosed.apply(this, arguments);
          }
        },

        /**
         * Called when animation finishes on the dropdown (when opening or
         * closing). Responsible for "completing" the process of opening or
         * closing the dropdown by positioning it or setting its display to
         * none.
         */
        _onNeonAnimationFinish: function() {
          this.$.contentWrapper.classList.remove('animating');
          if (this.opened) {
            this._finishRenderOpened();
          } else {
            this._finishRenderClosed();
          }
        },

        _onCaptureScroll: function() {
          if (!this.allowOutsideScroll) {
            this._restoreScrollPosition();
          } else {
            this._refitOnScrollRAF && window.cancelAnimationFrame(this._refitOnScrollRAF);
            this._refitOnScrollRAF = window.requestAnimationFrame(this.refit.bind(this));
          }
        },

        /**
         * Memoizes the scroll position of the outside scrolling element.
         * @private
         */
        _saveScrollPosition: function() {
          if (document.scrollingElement) {
            this._scrollTop = document.scrollingElement.scrollTop;
            this._scrollLeft = document.scrollingElement.scrollLeft;
          } else {
            // Since we don't know if is the body or html, get max.
            this._scrollTop = Math.max(document.documentElement.scrollTop, document.body.scrollTop);
            this._scrollLeft = Math.max(document.documentElement.scrollLeft, document.body.scrollLeft);
          }
        },

        /**
         * Resets the scroll position of the outside scrolling element.
         * @private
         */
        _restoreScrollPosition: function() {
          if (document.scrollingElement) {
            document.scrollingElement.scrollTop = this._scrollTop;
            document.scrollingElement.scrollLeft = this._scrollLeft;
          } else {
            // Since we don't know if is the body or html, set both.
            document.documentElement.scrollTop = this._scrollTop;
            document.documentElement.scrollLeft = this._scrollLeft;
            document.body.scrollTop = this._scrollTop;
            document.body.scrollLeft = this._scrollLeft;
          }
        },

        /**
         * Constructs the final animation config from different properties used
         * to configure specific parts of the opening and closing animations.
         */
        _updateAnimationConfig: function() {
          // Update the animation node to be the containedElement.
          var animationNode = this.containedElement;
          var animations = [].concat(this.openAnimationConfig || []).concat(this.closeAnimationConfig || []);
          for (var i = 0; i < animations.length; i++) {
            animations[i].node = animationNode;
          }
          this.animationConfig = {
            open: this.openAnimationConfig,
            close: this.closeAnimationConfig
          };
        },

        /**
         * Updates the overlay position based on configured horizontal
         * and vertical alignment.
         */
        _updateOverlayPosition: function() {
          if (this.isAttached) {
            // This triggers iron-resize, and iron-overlay-behavior will call refit if needed.
            this.notifyResize();
          }
        },

        /**
         * Apply focus to focusTarget or containedElement
         */
        _applyFocus: function () {
          var focusTarget = this.focusTarget || this.containedElement;
          if (focusTarget && this.opened && !this.noAutoFocus) {
            focusTarget.focus();
          } else {
            Polymer.IronOverlayBehaviorImpl._applyFocus.apply(this, arguments);
          }
        }
      });
    })();
Polymer({

    is: 'fade-in-animation',

    behaviors: [
      Polymer.NeonAnimationBehavior
    ],

    configure: function(config) {
      var node = config.node;
      this._effect = new KeyframeEffect(node, [
        {'opacity': '0'},
        {'opacity': '1'}
      ], this.timingFromConfig(config));
      return this._effect;
    }

  });
Polymer({

    is: 'fade-out-animation',

    behaviors: [
      Polymer.NeonAnimationBehavior
    ],

    configure: function(config) {
      var node = config.node;
      this._effect = new KeyframeEffect(node, [
        {'opacity': '1'},
        {'opacity': '0'}
      ], this.timingFromConfig(config));
      return this._effect;
    }

  });
Polymer({
    is: 'paper-menu-grow-height-animation',

    behaviors: [
      Polymer.NeonAnimationBehavior
    ],

    configure: function(config) {
      var node = config.node;
      var rect = node.getBoundingClientRect();
      var height = rect.height;

      this._effect = new KeyframeEffect(node, [{
        height: (height / 2) + 'px'
      }, {
        height: height + 'px'
      }], this.timingFromConfig(config));

      return this._effect;
    }
  });

  Polymer({
    is: 'paper-menu-grow-width-animation',

    behaviors: [
      Polymer.NeonAnimationBehavior
    ],

    configure: function(config) {
      var node = config.node;
      var rect = node.getBoundingClientRect();
      var width = rect.width;

      this._effect = new KeyframeEffect(node, [{
        width: (width / 2) + 'px'
      }, {
        width: width + 'px'
      }], this.timingFromConfig(config));

      return this._effect;
    }
  });

  Polymer({
    is: 'paper-menu-shrink-width-animation',

    behaviors: [
      Polymer.NeonAnimationBehavior
    ],

    configure: function(config) {
      var node = config.node;
      var rect = node.getBoundingClientRect();
      var width = rect.width;

      this._effect = new KeyframeEffect(node, [{
        width: width + 'px'
      }, {
        width: width - (width / 20) + 'px'
      }], this.timingFromConfig(config));

      return this._effect;
    }
  });

  Polymer({
    is: 'paper-menu-shrink-height-animation',

    behaviors: [
      Polymer.NeonAnimationBehavior
    ],

    configure: function(config) {
      var node = config.node;
      var rect = node.getBoundingClientRect();
      var height = rect.height;
      var top = rect.top;

      this.setPrefixedProperty(node, 'transformOrigin', '0 0');

      this._effect = new KeyframeEffect(node, [{
        height: height + 'px',
        transform: 'translateY(0)'
      }, {
        height: height / 2 + 'px',
        transform: 'translateY(-20px)'
      }], this.timingFromConfig(config));

      return this._effect;
    }
  });
(function() {
      'use strict';

      var config = {
        ANIMATION_CUBIC_BEZIER: 'cubic-bezier(.3,.95,.5,1)',
        MAX_ANIMATION_TIME_MS: 400
      };

      var PaperMenuButton = Polymer({
        is: 'paper-menu-button',

        /**
         * Fired when the dropdown opens.
         *
         * @event paper-dropdown-open
         */

        /**
         * Fired when the dropdown closes.
         *
         * @event paper-dropdown-close
         */

        behaviors: [
          Polymer.IronA11yKeysBehavior,
          Polymer.IronControlState
        ],

        properties: {
          /**
           * True if the content is currently displayed.
           */
          opened: {
            type: Boolean,
            value: false,
            notify: true,
            observer: '_openedChanged'
          },

          /**
           * The orientation against which to align the menu dropdown
           * horizontally relative to the dropdown trigger.
           */
          horizontalAlign: {
            type: String,
            value: 'left',
            reflectToAttribute: true
          },

          /**
           * The orientation against which to align the menu dropdown
           * vertically relative to the dropdown trigger.
           */
          verticalAlign: {
            type: String,
            value: 'top',
            reflectToAttribute: true
          },

          /**
           * If true, the `horizontalAlign` and `verticalAlign` properties will
           * be considered preferences instead of strict requirements when
           * positioning the dropdown and may be changed if doing so reduces
           * the area of the dropdown falling outside of `fitInto`.
           */
          dynamicAlign: {
            type: Boolean
          },

          /**
           * A pixel value that will be added to the position calculated for the
           * given `horizontalAlign`. Use a negative value to offset to the
           * left, or a positive value to offset to the right.
           */
          horizontalOffset: {
            type: Number,
            value: 0,
            notify: true
          },

          /**
           * A pixel value that will be added to the position calculated for the
           * given `verticalAlign`. Use a negative value to offset towards the
           * top, or a positive value to offset towards the bottom.
           */
          verticalOffset: {
            type: Number,
            value: 0,
            notify: true
          },

          /**
           * If true, the dropdown will be positioned so that it doesn't overlap
           * the button.
           */
          noOverlap: {
            type: Boolean
          },

          /**
           * Set to true to disable animations when opening and closing the
           * dropdown.
           */
          noAnimations: {
            type: Boolean,
            value: false
          },

          /**
           * Set to true to disable automatically closing the dropdown after
           * a selection has been made.
           */
          ignoreSelect: {
            type: Boolean,
            value: false
          },

          /**
           * Set to true to enable automatically closing the dropdown after an
           * item has been activated, even if the selection did not change.
           */
          closeOnActivate: {
            type: Boolean,
            value: false
          },

          /**
           * An animation config. If provided, this will be used to animate the
           * opening of the dropdown.
           */
          openAnimationConfig: {
            type: Object,
            value: function() {
              return [{
                name: 'fade-in-animation',
                timing: {
                  delay: 100,
                  duration: 200
                }
              }, {
                name: 'paper-menu-grow-width-animation',
                timing: {
                  delay: 100,
                  duration: 150,
                  easing: config.ANIMATION_CUBIC_BEZIER
                }
              }, {
                name: 'paper-menu-grow-height-animation',
                timing: {
                  delay: 100,
                  duration: 275,
                  easing: config.ANIMATION_CUBIC_BEZIER
                }
              }];
            }
          },

          /**
           * An animation config. If provided, this will be used to animate the
           * closing of the dropdown.
           */
          closeAnimationConfig: {
            type: Object,
            value: function() {
              return [{
                name: 'fade-out-animation',
                timing: {
                  duration: 150
                }
              }, {
                name: 'paper-menu-shrink-width-animation',
                timing: {
                  delay: 100,
                  duration: 50,
                  easing: config.ANIMATION_CUBIC_BEZIER
                }
              }, {
                name: 'paper-menu-shrink-height-animation',
                timing: {
                  duration: 200,
                  easing: 'ease-in'
                }
              }];
            }
          },

          /**
           * By default, the dropdown will constrain scrolling on the page
           * to itself when opened.
           * Set to true in order to prevent scroll from being constrained
           * to the dropdown when it opens.
           */
          allowOutsideScroll: {
            type: Boolean,
            value: false
          },

          /**
           * Whether focus should be restored to the button when the menu closes.
           */
          restoreFocusOnClose: {
            type: Boolean,
            value: true
          },

          /**
           * This is the element intended to be bound as the focus target
           * for the `iron-dropdown` contained by `paper-menu-button`.
           */
          _dropdownContent: {
            type: Object
          }
        },

        hostAttributes: {
          role: 'group',
          'aria-haspopup': 'true'
        },

        listeners: {
          'iron-activate': '_onIronActivate',
          'iron-select': '_onIronSelect'
        },

        /**
         * The content element that is contained by the menu button, if any.
         */
        get contentElement() {
          return Polymer.dom(this.$.content).getDistributedNodes()[0];
        },

        /**
         * Toggles the drowpdown content between opened and closed.
         */
        toggle: function() {
          if (this.opened) {
            this.close();
          } else {
            this.open();
          }
        },

        /**
         * Make the dropdown content appear as an overlay positioned relative
         * to the dropdown trigger.
         */
        open: function() {
          if (this.disabled) {
            return;
          }

          this.$.dropdown.open();
        },

        /**
         * Hide the dropdown content.
         */
        close: function() {
          this.$.dropdown.close();
        },

        /**
         * When an `iron-select` event is received, the dropdown should
         * automatically close on the assumption that a value has been chosen.
         *
         * @param {CustomEvent} event A CustomEvent instance with type
         * set to `"iron-select"`.
         */
        _onIronSelect: function(event) {
          if (!this.ignoreSelect) {
            this.close();
          }
        },

        /**
         * Closes the dropdown when an `iron-activate` event is received if
         * `closeOnActivate` is true.
         *
         * @param {CustomEvent} event A CustomEvent of type 'iron-activate'.
         */
        _onIronActivate: function(event) {
          if (this.closeOnActivate) {
            this.close();
          }
        },

        /**
         * When the dropdown opens, the `paper-menu-button` fires `paper-open`.
         * When the dropdown closes, the `paper-menu-button` fires `paper-close`.
         *
         * @param {boolean} opened True if the dropdown is opened, otherwise false.
         * @param {boolean} oldOpened The previous value of `opened`.
         */
        _openedChanged: function(opened, oldOpened) {
          if (opened) {
            // TODO(cdata): Update this when we can measure changes in distributed
            // children in an idiomatic way.
            // We poke this property in case the element has changed. This will
            // cause the focus target for the `iron-dropdown` to be updated as
            // necessary:
            this._dropdownContent = this.contentElement;
            this.fire('paper-dropdown-open');
          } else if (oldOpened != null) {
            this.fire('paper-dropdown-close');
          }
        },

        /**
         * If the dropdown is open when disabled becomes true, close the
         * dropdown.
         *
         * @param {boolean} disabled True if disabled, otherwise false.
         */
        _disabledChanged: function(disabled) {
          Polymer.IronControlState._disabledChanged.apply(this, arguments);
          if (disabled && this.opened) {
            this.close();
          }
        },

        __onIronOverlayCanceled: function(event) {
          var uiEvent = event.detail;
          var target = Polymer.dom(uiEvent).rootTarget;
          var trigger = this.$.trigger;
          var path = Polymer.dom(uiEvent).path;

          if (path.indexOf(trigger) > -1) {
            event.preventDefault();
          }
        }
      });

      Object.keys(config).forEach(function (key) {
        PaperMenuButton[key] = config[key];
      });

      Polymer.PaperMenuButton = PaperMenuButton;
    })();
(function() {
      'use strict';

      Polymer({
        is: 'paper-dropdown-menu',

        behaviors: [
          Polymer.IronButtonState,
          Polymer.IronControlState,
          Polymer.IronFormElementBehavior,
          Polymer.IronValidatableBehavior
        ],

        properties: {
          /**
           * The derived "label" of the currently selected item. This value
           * is the `label` property on the selected item if set, or else the
           * trimmed text content of the selected item.
           */
          selectedItemLabel: {
            type: String,
            notify: true,
            readOnly: true
          },

          /**
           * The last selected item. An item is selected if the dropdown menu has
           * a child with class `dropdown-content`, and that child triggers an
           * `iron-select` event with the selected `item` in the `detail`.
           *
           * @type {?Object}
           */
          selectedItem: {
            type: Object,
            notify: true,
            readOnly: true
          },

          /**
           * The value for this element that will be used when submitting in
           * a form. It is read only, and will always have the same value
           * as `selectedItemLabel`.
           */
          value: {
            type: String,
            notify: true,
            readOnly: true
          },

          /**
           * The label for the dropdown.
           */
          label: {
            type: String
          },

          /**
           * The placeholder for the dropdown.
           */
          placeholder: {
            type: String
          },

          /**
           * The error message to display when invalid.
           */
          errorMessage: {
              type: String
          },

          /**
           * True if the dropdown is open. Otherwise, false.
           */
          opened: {
            type: Boolean,
            notify: true,
            value: false,
            observer: '_openedChanged'
          },

          /**
           * By default, the dropdown will constrain scrolling on the page
           * to itself when opened.
           * Set to true in order to prevent scroll from being constrained
           * to the dropdown when it opens.
           */
          allowOutsideScroll: {
            type: Boolean,
            value: false
          },

          /**
           * Set to true to disable the floating label. Bind this to the
           * `<paper-input-container>`'s `noLabelFloat` property.
           */
          noLabelFloat: {
              type: Boolean,
              value: false,
              reflectToAttribute: true
          },

          /**
           * Set to true to always float the label. Bind this to the
           * `<paper-input-container>`'s `alwaysFloatLabel` property.
           */
          alwaysFloatLabel: {
            type: Boolean,
            value: false
          },

          /**
           * Set to true to disable animations when opening and closing the
           * dropdown.
           */
          noAnimations: {
            type: Boolean,
            value: false
          },

          /**
           * The orientation against which to align the menu dropdown
           * horizontally relative to the dropdown trigger.
           */
          horizontalAlign: {
            type: String,
            value: 'right'
          },

          /**
           * The orientation against which to align the menu dropdown
           * vertically relative to the dropdown trigger.
           */
          verticalAlign: {
            type: String,
            value: 'top'
          },

          /**
           * If true, the `horizontalAlign` and `verticalAlign` properties will
           * be considered preferences instead of strict requirements when
           * positioning the dropdown and may be changed if doing so reduces
           * the area of the dropdown falling outside of `fitInto`.
           */
          dynamicAlign: {
            type: Boolean
          },
            
          /**
           * Whether focus should be restored to the dropdown when the menu closes.
           */
          restoreFocusOnClose: {
            type: Boolean,
            value: true
          },
        },

        listeners: {
          'tap': '_onTap'
        },

        keyBindings: {
          'up down': 'open',
          'esc': 'close'
        },

        hostAttributes: {
          role: 'combobox',
          'aria-autocomplete': 'none',
          'aria-haspopup': 'true'
        },

        observers: [
          '_selectedItemChanged(selectedItem)'
        ],

        attached: function() {
          // NOTE(cdata): Due to timing, a preselected value in a `IronSelectable`
          // child will cause an `iron-select` event to fire while the element is
          // still in a `DocumentFragment`. This has the effect of causing
          // handlers not to fire. So, we double check this value on attached:
          var contentElement = this.contentElement;
          if (contentElement && contentElement.selectedItem) {
            this._setSelectedItem(contentElement.selectedItem);
          }
        },

        /**
         * The content element that is contained by the dropdown menu, if any.
         */
        get contentElement() {
          return Polymer.dom(this.$.content).getDistributedNodes()[0];
        },

        /**
         * Show the dropdown content.
         */
        open: function() {
          this.$.menuButton.open();
        },

        /**
         * Hide the dropdown content.
         */
        close: function() {
          this.$.menuButton.close();
        },

        /**
         * A handler that is called when `iron-select` is fired.
         *
         * @param {CustomEvent} event An `iron-select` event.
         */
        _onIronSelect: function(event) {
          this._setSelectedItem(event.detail.item);
        },

        /**
         * A handler that is called when `iron-deselect` is fired.
         *
         * @param {CustomEvent} event An `iron-deselect` event.
         */
        _onIronDeselect: function(event) {
          this._setSelectedItem(null);
        },

        /**
         * A handler that is called when the dropdown is tapped.
         *
         * @param {CustomEvent} event A tap event.
         */
        _onTap: function(event) {
          if (Polymer.Gestures.findOriginalTarget(event) === this) {
            this.open();
          }
        },

        /**
         * Compute the label for the dropdown given a selected item.
         *
         * @param {Element} selectedItem A selected Element item, with an
         * optional `label` property.
         */
        _selectedItemChanged: function(selectedItem) {
          var value = '';
          if (!selectedItem) {
            value = '';
          } else {
            value = selectedItem.label || selectedItem.getAttribute('label') || selectedItem.textContent.trim();
          }

          this._setValue(value);
          this._setSelectedItemLabel(value);
        },

        /**
         * Compute the vertical offset of the menu based on the value of
         * `noLabelFloat`.
         *
         * @param {boolean} noLabelFloat True if the label should not float
         * above the input, otherwise false.
         */
        _computeMenuVerticalOffset: function(noLabelFloat) {
          // NOTE(cdata): These numbers are somewhat magical because they are
          // derived from the metrics of elements internal to `paper-input`'s
          // template. The metrics will change depending on whether or not the
          // input has a floating label.
          return noLabelFloat ? -4 : 8;
        },

        /**
         * Returns false if the element is required and does not have a selection,
         * and true otherwise.
         * @param {*=} _value Ignored.
         * @return {boolean} true if `required` is false, or if `required` is true
         * and the element has a valid selection.
         */
        _getValidity: function(_value) {
          return this.disabled || !this.required || (this.required && !!this.value);
        },

        _openedChanged: function() {
          var openState = this.opened ? 'true' : 'false';
          var e = this.contentElement;
          if (e) {
            e.setAttribute('aria-expanded', openState);
          }
        }
      });
    })();
Polymer({
      is: 'paper-toolbar',

      hostAttributes: {
        'role': 'toolbar'
      },

      properties: {
        /**
         * Controls how the items are aligned horizontally when they are placed
         * at the bottom.
         * Options are `start`, `center`, `end`, `justified` and `around`.
         */
        bottomJustify: {
          type: String,
          value: ''
        },

        /**
         * Controls how the items are aligned horizontally.
         * Options are `start`, `center`, `end`, `justified` and `around`.
         */
        justify: {
          type: String,
          value: ''
        },

        /**
         * Controls how the items are aligned horizontally when they are placed
         * in the middle.
         * Options are `start`, `center`, `end`, `justified` and `around`.
         */
        middleJustify: {
          type: String,
          value: ''
        }

      },

      attached: function() {
        this._observer = this._observe(this);
        this._updateAriaLabelledBy();
      },

      detached: function() {
        if (this._observer) {
          this._observer.disconnect();
        }
      },

      _observe: function(node) {
        var observer = new MutationObserver(function() {
          this._updateAriaLabelledBy();
        }.bind(this));
        observer.observe(node, {
          childList: true,
          subtree: true
        });
        return observer;
      },

      _updateAriaLabelledBy: function() {
        var labelledBy = [];
        var contents = Polymer.dom(this.root).querySelectorAll('content');
        for (var content, index = 0; content = contents[index]; index++) {
          var nodes = Polymer.dom(content).getDistributedNodes();
          for (var node, jndex = 0; node = nodes[jndex]; jndex++) {
            if (node.classList && node.classList.contains('title')) {
              if (node.id) {
                labelledBy.push(node.id);
              } else {
                var id = 'paper-toolbar-label-' + Math.floor(Math.random() * 10000);
                node.id = id;
                labelledBy.push(id);
              }
            }
          }
        }
        if (labelledBy.length > 0) {
          this.setAttribute('aria-labelledby', labelledBy.join(' '));
        }
      },

      _computeBarExtraClasses: function(barJustify) {
        if (!barJustify) return '';

        return barJustify + (barJustify === 'justified' ? '' : '-justified');
      }
    });
/**
   * `Polymer.IronMenuBehavior` implements accessible menu behavior.
   *
   * @demo demo/index.html
   * @polymerBehavior Polymer.IronMenuBehavior
   */
  Polymer.IronMenuBehaviorImpl = {

    properties: {

      /**
       * Returns the currently focused item.
       * @type {?Object}
       */
      focusedItem: {
        observer: '_focusedItemChanged',
        readOnly: true,
        type: Object
      },

      /**
       * The attribute to use on menu items to look up the item title. Typing the first
       * letter of an item when the menu is open focuses that item. If unset, `textContent`
       * will be used.
       */
      attrForItemTitle: {
        type: String
      }
    },

    _SEARCH_RESET_TIMEOUT_MS: 1000,

    hostAttributes: {
      'role': 'menu',
      'tabindex': '0'
    },

    observers: [
      '_updateMultiselectable(multi)'
    ],

    listeners: {
      'focus': '_onFocus',
      'keydown': '_onKeydown',
      'iron-items-changed': '_onIronItemsChanged'
    },

    keyBindings: {
      'up': '_onUpKey',
      'down': '_onDownKey',
      'esc': '_onEscKey',
      'shift+tab:keydown': '_onShiftTabDown'
    },

    attached: function() {
      this._resetTabindices();
    },

    /**
     * Selects the given value. If the `multi` property is true, then the selected state of the
     * `value` will be toggled; otherwise the `value` will be selected.
     *
     * @param {string|number} value the value to select.
     */
    select: function(value) {
      // Cancel automatically focusing a default item if the menu received focus
      // through a user action selecting a particular item.
      if (this._defaultFocusAsync) {
        this.cancelAsync(this._defaultFocusAsync);
        this._defaultFocusAsync = null;
      }
      var item = this._valueToItem(value);
      if (item && item.hasAttribute('disabled')) return;
      this._setFocusedItem(item);
      Polymer.IronMultiSelectableBehaviorImpl.select.apply(this, arguments);
    },

    /**
     * Resets all tabindex attributes to the appropriate value based on the
     * current selection state. The appropriate value is `0` (focusable) for
     * the default selected item, and `-1` (not keyboard focusable) for all
     * other items.
     */
    _resetTabindices: function() {
      var selectedItem = this.multi ? (this.selectedItems && this.selectedItems[0]) : this.selectedItem;

      this.items.forEach(function(item) {
        item.setAttribute('tabindex', item === selectedItem ? '0' : '-1');
      }, this);
    },

    /**
     * Sets appropriate ARIA based on whether or not the menu is meant to be
     * multi-selectable.
     *
     * @param {boolean} multi True if the menu should be multi-selectable.
     */
    _updateMultiselectable: function(multi) {
      if (multi) {
        this.setAttribute('aria-multiselectable', 'true');
      } else {
        this.removeAttribute('aria-multiselectable');
      }
    },

    /**
     * Given a KeyboardEvent, this method will focus the appropriate item in the
     * menu (if there is a relevant item, and it is possible to focus it).
     *
     * @param {KeyboardEvent} event A KeyboardEvent.
     */
    _focusWithKeyboardEvent: function(event) {
      this.cancelDebouncer('_clearSearchText');

      var searchText = this._searchText || '';
      var key = event.key && event.key.length == 1 ? event.key :
          String.fromCharCode(event.keyCode);
      searchText += key.toLocaleLowerCase();

      var searchLength = searchText.length;

      for (var i = 0, item; item = this.items[i]; i++) {
        if (item.hasAttribute('disabled')) {
          continue;
        }

        var attr = this.attrForItemTitle || 'textContent';
        var title = (item[attr] || item.getAttribute(attr) || '').trim();

        if (title.length < searchLength) {
          continue;
        }

        if (title.slice(0, searchLength).toLocaleLowerCase() == searchText) {
          this._setFocusedItem(item);
          break;
        }
      }

      this._searchText = searchText;
      this.debounce('_clearSearchText', this._clearSearchText,
                    this._SEARCH_RESET_TIMEOUT_MS);
    },

    _clearSearchText: function() {
      this._searchText = '';
    },

    /**
     * Focuses the previous item (relative to the currently focused item) in the
     * menu, disabled items will be skipped.
     * Loop until length + 1 to handle case of single item in menu.
     */
    _focusPrevious: function() {
      var length = this.items.length;
      var curFocusIndex = Number(this.indexOf(this.focusedItem));

      for (var i = 1; i < length + 1; i++) {
        var item = this.items[(curFocusIndex - i + length) % length];
        if (!item.hasAttribute('disabled')) {
          var owner = Polymer.dom(item).getOwnerRoot() || document;
          this._setFocusedItem(item);

          // Focus might not have worked, if the element was hidden or not
          // focusable. In that case, try again.
          if (Polymer.dom(owner).activeElement == item) {
            return;
          }
        }
      }
    },

    /**
     * Focuses the next item (relative to the currently focused item) in the
     * menu, disabled items will be skipped.
     * Loop until length + 1 to handle case of single item in menu.
     */
    _focusNext: function() {
      var length = this.items.length;
      var curFocusIndex = Number(this.indexOf(this.focusedItem));

      for (var i = 1; i < length + 1; i++) {
        var item = this.items[(curFocusIndex + i) % length];
        if (!item.hasAttribute('disabled')) {
          var owner = Polymer.dom(item).getOwnerRoot() || document;
          this._setFocusedItem(item);

          // Focus might not have worked, if the element was hidden or not
          // focusable. In that case, try again.
          if (Polymer.dom(owner).activeElement == item) {
            return;
          }
        }
      }
    },

    /**
     * Mutates items in the menu based on provided selection details, so that
     * all items correctly reflect selection state.
     *
     * @param {Element} item An item in the menu.
     * @param {boolean} isSelected True if the item should be shown in a
     * selected state, otherwise false.
     */
    _applySelection: function(item, isSelected) {
      if (isSelected) {
        item.setAttribute('aria-selected', 'true');
      } else {
        item.removeAttribute('aria-selected');
      }
      Polymer.IronSelectableBehavior._applySelection.apply(this, arguments);
    },

    /**
     * Discretely updates tabindex values among menu items as the focused item
     * changes.
     *
     * @param {Element} focusedItem The element that is currently focused.
     * @param {?Element} old The last element that was considered focused, if
     * applicable.
     */
    _focusedItemChanged: function(focusedItem, old) {
      old && old.setAttribute('tabindex', '-1');
      if (focusedItem) {
        focusedItem.setAttribute('tabindex', '0');
        focusedItem.focus();
      }
    },

    /**
     * A handler that responds to mutation changes related to the list of items
     * in the menu.
     *
     * @param {CustomEvent} event An event containing mutation records as its
     * detail.
     */
    _onIronItemsChanged: function(event) {
      if (event.detail.addedNodes.length) {
        this._resetTabindices();
      }
    },

    /**
     * Handler that is called when a shift+tab keypress is detected by the menu.
     *
     * @param {CustomEvent} event A key combination event.
     */
    _onShiftTabDown: function(event) {
      var oldTabIndex = this.getAttribute('tabindex');

      Polymer.IronMenuBehaviorImpl._shiftTabPressed = true;

      this._setFocusedItem(null);

      this.setAttribute('tabindex', '-1');

      this.async(function() {
        this.setAttribute('tabindex', oldTabIndex);
        Polymer.IronMenuBehaviorImpl._shiftTabPressed = false;
        // NOTE(cdata): polymer/polymer#1305
      }, 1);
    },

    /**
     * Handler that is called when the menu receives focus.
     *
     * @param {FocusEvent} event A focus event.
     */
    _onFocus: function(event) {
      if (Polymer.IronMenuBehaviorImpl._shiftTabPressed) {
        // do not focus the menu itself
        return;
      }

      // Do not focus the selected tab if the deepest target is part of the
      // menu element's local DOM and is focusable.
      var rootTarget = /** @type {?HTMLElement} */(
          Polymer.dom(event).rootTarget);
      if (rootTarget !== this && typeof rootTarget.tabIndex !== "undefined" && !this.isLightDescendant(rootTarget)) {
        return;
      }

      // clear the cached focus item
      this._defaultFocusAsync = this.async(function() {
        // focus the selected item when the menu receives focus, or the first item
        // if no item is selected
        var selectedItem = this.multi ? (this.selectedItems && this.selectedItems[0]) : this.selectedItem;

        this._setFocusedItem(null);

        if (selectedItem) {
          this._setFocusedItem(selectedItem);
        } else if (this.items[0]) {
          // We find the first none-disabled item (if one exists)
          this._focusNext();
        }
      });
    },

    /**
     * Handler that is called when the up key is pressed.
     *
     * @param {CustomEvent} event A key combination event.
     */
    _onUpKey: function(event) {
      // up and down arrows moves the focus
      this._focusPrevious();
      event.detail.keyboardEvent.preventDefault();
    },

    /**
     * Handler that is called when the down key is pressed.
     *
     * @param {CustomEvent} event A key combination event.
     */
    _onDownKey: function(event) {
      this._focusNext();
      event.detail.keyboardEvent.preventDefault();
    },

    /**
     * Handler that is called when the esc key is pressed.
     *
     * @param {CustomEvent} event A key combination event.
     */
    _onEscKey: function(event) {
      // esc blurs the control
      this.focusedItem.blur();
    },

    /**
     * Handler that is called when a keydown event is detected.
     *
     * @param {KeyboardEvent} event A keyboard event.
     */
    _onKeydown: function(event) {
      if (!this.keyboardEventMatchesKeys(event, 'up down esc')) {
        // all other keys focus the menu item starting with that character
        this._focusWithKeyboardEvent(event);
      }
      event.stopPropagation();
    },

    // override _activateHandler
    _activateHandler: function(event) {
      Polymer.IronSelectableBehavior._activateHandler.call(this, event);
      event.stopPropagation();
    }
  };

  Polymer.IronMenuBehaviorImpl._shiftTabPressed = false;

  /** @polymerBehavior Polymer.IronMenuBehavior */
  Polymer.IronMenuBehavior = [
    Polymer.IronMultiSelectableBehavior,
    Polymer.IronA11yKeysBehavior,
    Polymer.IronMenuBehaviorImpl
  ];
(function() {
      Polymer({
        is: 'paper-listbox',

        behaviors: [
          Polymer.IronMenuBehavior
        ],

        hostAttributes: {
          role: 'listbox'
        }
      });
    })();
/**
   * `Polymer.IronMenubarBehavior` implements accessible menubar behavior.
   *
   * @polymerBehavior Polymer.IronMenubarBehavior
   */
  Polymer.IronMenubarBehaviorImpl = {

    hostAttributes: {
      'role': 'menubar'
    },

    keyBindings: {
      'left': '_onLeftKey',
      'right': '_onRightKey'
    },

    _onUpKey: function(event) {
      this.focusedItem.click();
      event.detail.keyboardEvent.preventDefault();
    },

    _onDownKey: function(event) {
      this.focusedItem.click();
      event.detail.keyboardEvent.preventDefault();
    },

    get _isRTL() {
      return window.getComputedStyle(this)['direction'] === 'rtl';
    },

    _onLeftKey: function(event) {
      if (this._isRTL) {
        this._focusNext();
      } else {
        this._focusPrevious();
      }
      event.detail.keyboardEvent.preventDefault();
    },

    _onRightKey: function(event) {
      if (this._isRTL) {
        this._focusPrevious();
      } else {
        this._focusNext();
      }
      event.detail.keyboardEvent.preventDefault();
    },

    _onKeydown: function(event) {
      if (this.keyboardEventMatchesKeys(event, 'up down left right esc')) {
        return;
      }

      // all other keys focus the menu item starting with that character
      this._focusWithKeyboardEvent(event);
    }

  };

  /** @polymerBehavior Polymer.IronMenubarBehavior */
  Polymer.IronMenubarBehavior = [
    Polymer.IronMenuBehavior,
    Polymer.IronMenubarBehaviorImpl
  ];
Polymer({
      is: 'paper-tab',

      behaviors: [
        Polymer.IronControlState,
        Polymer.IronButtonState,
        Polymer.PaperRippleBehavior
      ],

      properties: {

        /**
         * If true, the tab will forward keyboard clicks (enter/space) to
         * the first anchor element found in its descendants
         */
        link: {
          type: Boolean,
          value: false,
          reflectToAttribute: true
        }

      },

      hostAttributes: {
        role: 'tab'
      },

      listeners: {
        down: '_updateNoink',
        tap: '_onTap'
      },

      attached: function() {
        this._updateNoink();
      },

      get _parentNoink () {
        var parent = Polymer.dom(this).parentNode;
        return !!parent && !!parent.noink;
      },

      _updateNoink: function() {
        this.noink = !!this.noink || !!this._parentNoink;
      },

      _onTap: function(event) {
        if (this.link) {
          var anchor = this.queryEffectiveChildren('a');

          if (!anchor) {
            return;
          }

          // Don't get stuck in a loop delegating
          // the listener from the child anchor
          if (event.target === anchor) {
            return;
          }

          anchor.click();
        }
      }

    });
Polymer({
      is: 'paper-tabs',

      behaviors: [
        Polymer.IronResizableBehavior,
        Polymer.IronMenubarBehavior
      ],

      properties: {
        /**
         * If true, ink ripple effect is disabled. When this property is changed,
         * all descendant `<paper-tab>` elements have their `noink` property
         * changed to the new value as well.
         */
        noink: {
          type: Boolean,
          value: false,
          observer: '_noinkChanged'
        },

        /**
         * If true, the bottom bar to indicate the selected tab will not be shown.
         */
        noBar: {
          type: Boolean,
          value: false
        },

        /**
         * If true, the slide effect for the bottom bar is disabled.
         */
        noSlide: {
          type: Boolean,
          value: false
        },

        /**
         * If true, tabs are scrollable and the tab width is based on the label width.
         */
        scrollable: {
          type: Boolean,
          value: false
        },

        /**
         * If true, tabs expand to fit their container. This currently only applies when
         * scrollable is true.
         */
        fitContainer: {
          type: Boolean,
          value: false
        },

        /**
         * If true, dragging on the tabs to scroll is disabled.
         */
        disableDrag: {
          type: Boolean,
          value: false
        },

        /**
         * If true, scroll buttons (left/right arrow) will be hidden for scrollable tabs.
         */
        hideScrollButtons: {
          type: Boolean,
          value: false
        },

        /**
         * If true, the tabs are aligned to bottom (the selection bar appears at the top).
         */
        alignBottom: {
          type: Boolean,
          value: false
        },

        selectable: {
          type: String,
          value: 'paper-tab'
        },

        /**
         * If true, tabs are automatically selected when focused using the
         * keyboard.
         */
        autoselect: {
          type: Boolean,
          value: false
        },

        /**
         * The delay (in milliseconds) between when the user stops interacting
         * with the tabs through the keyboard and when the focused item is
         * automatically selected (if `autoselect` is true).
         */
        autoselectDelay: {
          type: Number,
          value: 0
        },

        _step: {
          type: Number,
          value: 10
        },

        _holdDelay: {
          type: Number,
          value: 1
        },

        _leftHidden: {
          type: Boolean,
          value: false
        },

        _rightHidden: {
          type: Boolean,
          value: false
        },

        _previousTab: {
          type: Object
        }
      },

      hostAttributes: {
        role: 'tablist'
      },

      listeners: {
        'iron-resize': '_onTabSizingChanged',
        'iron-items-changed': '_onTabSizingChanged',
        'iron-select': '_onIronSelect',
        'iron-deselect': '_onIronDeselect'
      },

      keyBindings: {
        'left:keyup right:keyup': '_onArrowKeyup'
      },

      created: function() {
        this._holdJob = null;
        this._pendingActivationItem = undefined;
        this._pendingActivationTimeout = undefined;
        this._bindDelayedActivationHandler = this._delayedActivationHandler.bind(this);
        this.addEventListener('blur', this._onBlurCapture.bind(this), true);
      },

      ready: function() {
        this.setScrollDirection('y', this.$.tabsContainer);
      },

      detached: function() {
        this._cancelPendingActivation();
      },

      _noinkChanged: function(noink) {
        var childTabs = Polymer.dom(this).querySelectorAll('paper-tab');
        childTabs.forEach(noink ? this._setNoinkAttribute : this._removeNoinkAttribute);
      },

      _setNoinkAttribute: function(element) {
        element.setAttribute('noink', '');
      },

      _removeNoinkAttribute: function(element) {
        element.removeAttribute('noink');
      },

      _computeScrollButtonClass: function(hideThisButton, scrollable, hideScrollButtons) {
        if (!scrollable || hideScrollButtons) {
          return 'hidden';
        }

        if (hideThisButton) {
          return 'not-visible';
        }

        return '';
      },

      _computeTabsContentClass: function(scrollable, fitContainer) {
        return scrollable ? 'scrollable' + (fitContainer ? ' fit-container' : '') : ' fit-container';
      },

      _computeSelectionBarClass: function(noBar, alignBottom) {
        if (noBar) {
          return 'hidden';
        } else if (alignBottom) {
          return 'align-bottom';
        }

        return '';
      },

      // TODO(cdata): Add `track` response back in when gesture lands.

      _onTabSizingChanged: function() {
        this.debounce('_onTabSizingChanged', function() {
          this._scroll();
          this._tabChanged(this.selectedItem);
        }, 10);
      },

      _onIronSelect: function(event) {
        this._tabChanged(event.detail.item, this._previousTab);
        this._previousTab = event.detail.item;
        this.cancelDebouncer('tab-changed');
      },

      _onIronDeselect: function(event) {
        this.debounce('tab-changed', function() {
          this._tabChanged(null, this._previousTab);
          this._previousTab = null;
        // See polymer/polymer#1305
        }, 1);
      },

      _activateHandler: function() {
        // Cancel item activations scheduled by keyboard events when any other
        // action causes an item to be activated (e.g. clicks).
        this._cancelPendingActivation();

        Polymer.IronMenuBehaviorImpl._activateHandler.apply(this, arguments);
      },

      /**
       * Activates an item after a delay (in milliseconds).
       */
      _scheduleActivation: function(item, delay) {
        this._pendingActivationItem = item;
        this._pendingActivationTimeout = this.async(
            this._bindDelayedActivationHandler, delay);
      },

      /**
       * Activates the last item given to `_scheduleActivation`.
       */
      _delayedActivationHandler: function() {
        var item = this._pendingActivationItem;
        this._pendingActivationItem = undefined;
        this._pendingActivationTimeout = undefined;
        item.fire(this.activateEvent, null, {
          bubbles: true,
          cancelable: true
        });
      },

      /**
       * Cancels a previously scheduled item activation made with
       * `_scheduleActivation`.
       */
      _cancelPendingActivation: function() {
        if (this._pendingActivationTimeout !== undefined) {
          this.cancelAsync(this._pendingActivationTimeout);
          this._pendingActivationItem = undefined;
          this._pendingActivationTimeout = undefined;
        }
      },

      _onArrowKeyup: function(event) {
        if (this.autoselect) {
          this._scheduleActivation(this.focusedItem, this.autoselectDelay);
        }
      },

      _onBlurCapture: function(event) {
        // Cancel a scheduled item activation (if any) when that item is
        // blurred.
        if (event.target === this._pendingActivationItem) {
          this._cancelPendingActivation();
        }
      },

      get _tabContainerScrollSize () {
        return Math.max(
          0,
          this.$.tabsContainer.scrollWidth -
            this.$.tabsContainer.offsetWidth
        );
      },

      _scroll: function(e, detail) {
        if (!this.scrollable) {
          return;
        }

        var ddx = (detail && -detail.ddx) || 0;
        this._affectScroll(ddx);
      },

      _down: function(e) {
        // go one beat async to defeat IronMenuBehavior
        // autorefocus-on-no-selection timeout
        this.async(function() {
          if (this._defaultFocusAsync) {
            this.cancelAsync(this._defaultFocusAsync);
            this._defaultFocusAsync = null;
          }
        }, 1);
      },

      _affectScroll: function(dx) {
        this.$.tabsContainer.scrollLeft += dx;

        var scrollLeft = this.$.tabsContainer.scrollLeft;

        this._leftHidden = scrollLeft === 0;
        this._rightHidden = scrollLeft === this._tabContainerScrollSize;
      },

      _onLeftScrollButtonDown: function() {
        this._scrollToLeft();
        this._holdJob = setInterval(this._scrollToLeft.bind(this), this._holdDelay);
      },

      _onRightScrollButtonDown: function() {
        this._scrollToRight();
        this._holdJob = setInterval(this._scrollToRight.bind(this), this._holdDelay);
      },

      _onScrollButtonUp: function() {
        clearInterval(this._holdJob);
        this._holdJob = null;
      },

      _scrollToLeft: function() {
        this._affectScroll(-this._step);
      },

      _scrollToRight: function() {
        this._affectScroll(this._step);
      },

      _tabChanged: function(tab, old) {
        if (!tab) {
          // Remove the bar without animation.
          this.$.selectionBar.classList.remove('expand');
          this.$.selectionBar.classList.remove('contract');
          this._positionBar(0, 0);
          return;
        }

        var r = this.$.tabsContent.getBoundingClientRect();
        var w = r.width;
        var tabRect = tab.getBoundingClientRect();
        var tabOffsetLeft = tabRect.left - r.left;

        this._pos = {
          width: this._calcPercent(tabRect.width, w),
          left: this._calcPercent(tabOffsetLeft, w)
        };

        if (this.noSlide || old == null) {
          // Position the bar without animation.
          this.$.selectionBar.classList.remove('expand');
          this.$.selectionBar.classList.remove('contract');
          this._positionBar(this._pos.width, this._pos.left);
          return;
        }

        var oldRect = old.getBoundingClientRect();
        var oldIndex = this.items.indexOf(old);
        var index = this.items.indexOf(tab);
        var m = 5;

        // bar animation: expand
        this.$.selectionBar.classList.add('expand');

        var moveRight = oldIndex < index;
        var isRTL = this._isRTL;
        if (isRTL) {
          moveRight = !moveRight;
        }

        if (moveRight) {
          this._positionBar(this._calcPercent(tabRect.left + tabRect.width - oldRect.left, w) - m,
              this._left);
        } else {
          this._positionBar(this._calcPercent(oldRect.left + oldRect.width - tabRect.left, w) - m,
              this._calcPercent(tabOffsetLeft, w) + m);
        }

        if (this.scrollable) {
          this._scrollToSelectedIfNeeded(tabRect.width, tabOffsetLeft);
        }
      },

      _scrollToSelectedIfNeeded: function(tabWidth, tabOffsetLeft) {
        var l = tabOffsetLeft - this.$.tabsContainer.scrollLeft;
        if (l < 0) {
          this.$.tabsContainer.scrollLeft += l;
        } else {
          l += (tabWidth - this.$.tabsContainer.offsetWidth);
          if (l > 0) {
            this.$.tabsContainer.scrollLeft += l;
          }
        }
      },

      _calcPercent: function(w, w0) {
        return 100 * w / w0;
      },

      _positionBar: function(width, left) {
        width = width || 0;
        left = left || 0;

        this._width = width;
        this._left = left;
        this.transform(
            'translateX(' + left + '%) scaleX(' + (width / 100) + ')',
            this.$.selectionBar);
      },

      _onBarTransitionEnd: function(e) {
        var cl = this.$.selectionBar.classList;
        // bar animation: expand -> contract
        if (cl.contains('expand')) {
          cl.remove('expand');
          cl.add('contract');
          this._positionBar(this._pos.width, this._pos.left);
        // bar animation done
        } else if (cl.contains('contract')) {
          cl.remove('contract');
        }
      }
    });
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
Polymer({
    is: 'card-sorter',

    properties: {
      sorter: {
        type: Object,
        readOnly: true,
      }
    },

    ready: function() {
      this._setSorter(new CardSorter(this));
    },

    sort: function(o) {
      o = (o || '').trim().toLowerCase();
      this.sorter.sort(o);
    },

    filter: function(f) {
      this.sorter.filter(f);
    },

    filterByCategory: function(category) {
      this.sorter.filterByCategory(category);
    },

    filterByTags: function(tags) {
      this.sorter.filterByTags(tags);
    },

    filterByText: function(text) {
      this.sorter.filterByText(text);
    },

    clearFilters: function() {
      this.sorter.clearFilter();
    }
  });