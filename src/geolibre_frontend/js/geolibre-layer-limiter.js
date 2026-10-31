/**
 * GeoLibre Area-Priority Viewport Feature Limiter (geolibre-layer-limiter)
 * Upstream Target: opengeos/GeoLibre
 * Contributing Org: GetBack2Basics Spatial AI Engineering / AURA Siting Crafter
 * License: Apache-2.0 / MIT
 *
 * Prevents WebGL draw call saturation and visual canvas clutter when rendering
 * large vector layers (>10k - 50k+ features) by prioritizing features with largest
 * surface area and capping rendering to the top N features in the active viewport.
 */

(function (root, factory) {
  if (typeof define === 'function' && define.amd) {
    define([], factory);
  } else if (typeof module === 'object' && module.exports) {
    module.exports = factory();
  } else {
    const exports = factory();
    root.GeoLibreLayerLimiter = exports;
    root.AreaPriorityLimiter = exports.AreaPriorityLimiter;
  }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  /**
   * High-Performance Binary Min-Heap for O(M log K) Top-K Selection
   */
  class MinHeap {
    constructor(comparator) {
      this.heap = [];
      this.compare = comparator || ((a, b) => a.score - b.score);
    }

    size() {
      return this.heap.length;
    }

    peek() {
      return this.heap[0] || null;
    }

    push(item) {
      this.heap.push(item);
      this._siftUp(this.heap.length - 1);
    }

    pop() {
      if (this.heap.length === 0) return null;
      const top = this.heap[0];
      const bottom = this.heap.pop();
      if (this.heap.length > 0) {
        this.heap[0] = bottom;
        this._siftDown(0);
      }
      return top;
    }

    _siftUp(idx) {
      while (idx > 0) {
        const parentIdx = (idx - 1) >> 1;
        if (this.compare(this.heap[idx], this.heap[parentIdx]) < 0) {
          const temp = this.heap[idx];
          this.heap[idx] = this.heap[parentIdx];
          this.heap[parentIdx] = temp;
          idx = parentIdx;
        } else {
          break;
        }
      }
    }

    _siftDown(idx) {
      const length = this.heap.length;
      while ((idx << 1) + 1 < length) {
        let left = (idx << 1) + 1;
        let right = left + 1;
        let smallest = idx;

        if (this.compare(this.heap[left], this.heap[smallest]) < 0) {
          smallest = left;
        }
        if (right < length && this.compare(this.heap[right], this.heap[smallest]) < 0) {
          smallest = right;
        }
        if (smallest !== idx) {
          const temp = this.heap[idx];
          this.heap[idx] = this.heap[smallest];
          this.heap[smallest] = temp;
          idx = smallest;
        } else {
          break;
        }
      }
    }

    toArraySortedDescending() {
      const arr = [];
      while (this.size() > 0) {
        arr.push(this.pop());
      }
      return arr.reverse();
    }
  }

  /**
   * Fast Planar Geodesic Shoelace Approximation for Ring Coordinates
   * Converts (lng, lat) vertices to estimated square meters / hectares.
   */
  function computeRingAreaHectares(coords) {
    if (!coords || coords.length < 3) return 0.0;
    let sum = 0.0;
    const n = coords.length;

    let centerLat = 0.0;
    for (let i = 0; i < n; i++) {
      centerLat += coords[i][1];
    }
    centerLat = (centerLat / n) * (Math.PI / 180.0);

    const mPerDegLat = 111132.92 - 559.82 * Math.cos(2 * centerLat) + 1.175 * Math.cos(4 * centerLat);
    const mPerDegLng = 111412.84 * Math.cos(centerLat) - 93.5 * Math.cos(3 * centerLat);

    for (let i = 0; i < n - 1; i++) {
      const x1 = coords[i][0] * mPerDegLng;
      const y1 = coords[i][1] * mPerDegLat;
      const x2 = coords[i + 1][0] * mPerDegLng;
      const y2 = coords[i + 1][1] * mPerDegLat;
      sum += (x1 * y2) - (x2 * y1);
    }

    const areaSqMeters = Math.abs(sum) / 2.0;
    return areaSqMeters / 10000.0; // In hectares
  }

  /**
   * Compute or extract polygon surface area (in hectares).
   */
  function getFeatureArea(feature, sortProperty = 'area_ha') {
    if (!feature) return 0.0;

    if (feature.properties) {
      const propCandidates = [sortProperty, 'area_ha', 'area', 'st_area', 'shape_area', 'AREA_HA', 'Shape__Area'];
      for (const prop of propCandidates) {
        if (prop in feature.properties && feature.properties[prop] !== null && feature.properties[prop] !== undefined) {
          const val = parseFloat(feature.properties[prop]);
          if (!isNaN(val) && val > 0) {
            if (prop === 'shape_area' || prop === 'Shape__Area' || prop === 'st_area') {
              return val > 100000000 ? val / 10000.0 : (val > 1000 ? val / 10000.0 : val);
            }
            return val;
          }
        }
      }
    }

    const geom = feature.geometry;
    if (!geom || !geom.coordinates) return 0.0;

    let totalHa = 0.0;
    if (geom.type === 'Polygon') {
      totalHa += computeRingAreaHectares(geom.coordinates[0]);
    } else if (geom.type === 'MultiPolygon') {
      for (let i = 0; i < geom.coordinates.length; i++) {
        totalHa += computeRingAreaHectares(geom.coordinates[i][0]);
      }
    }
    return totalHa;
  }

  /**
   * Quick Bounding Box Intersection Test between Feature and Viewport
   */
  function isFeatureInBBox(feature, bbox) {
    if (!bbox) return true;
    const [minX, minY, maxX, maxY] = bbox;
    const geom = feature.geometry;
    if (!geom || !geom.coordinates) return false;

    let fMinX = Infinity, fMinY = Infinity, fMaxX = -Infinity, fMaxY = -Infinity;

    function expand(c) {
      if (typeof c[0] === 'number') {
        if (c[0] < fMinX) fMinX = c[0];
        if (c[0] > fMaxX) fMaxX = c[0];
        if (c[1] < fMinY) fMinY = c[1];
        if (c[1] > fMaxY) fMaxY = c[1];
      } else {
        for (let i = 0; i < c.length; i++) expand(c[i]);
      }
    }

    expand(geom.coordinates);
    return !(fMaxX < minX || fMinX > maxX || fMaxY < minY || fMinY > maxY);
  }

  /**
   * Core Area-Priority Optimizer: Selects Top K features by surface area
   */
  function optimizeFeatureCollection(geojson, options = {}) {
    const startTime = (typeof performance !== 'undefined' && performance.now) ? performance.now() : Date.now();
    const maxFeatures = options.maxFeatures || 500;
    const sortProperty = options.sortProperty || 'area_ha';
    const sortOrder = options.sortOrder || 'desc';
    const minAreaThreshold = options.minAreaThreshold || 0.0;
    const bbox = options.bbox || null;

    if (!geojson || !geojson.features || !Array.isArray(geojson.features)) {
      return {
        optimizedGeoJSON: { type: 'FeatureCollection', features: [] },
        stats: {
          totalInViewport: 0,
          renderedCount: 0,
          isCapped: false,
          maxFeatures,
          sortProperty,
          executionTimeMs: 0
        }
      };
    }

    const allFeatures = geojson.features;
    const inViewportFeatures = [];

    for (let i = 0; i < allFeatures.length; i++) {
      const feat = allFeatures[i];
      if (bbox && !isFeatureInBBox(feat, bbox)) {
        continue;
      }
      const area = getFeatureArea(feat, sortProperty);
      if (area >= minAreaThreshold) {
        inViewportFeatures.push({ feature: feat, area });
      }
    }

    const totalInViewport = inViewportFeatures.length;
    let finalFeatures = [];
    const isCapped = totalInViewport > maxFeatures;

    if (!isCapped) {
      inViewportFeatures.sort((a, b) => sortOrder === 'desc' ? (b.area - a.area) : (a.area - b.area));
      finalFeatures = inViewportFeatures.map(item => item.feature);
    } else {
      if (sortOrder === 'desc') {
        const heap = new MinHeap((a, b) => a.area - b.area);
        for (let i = 0; i < inViewportFeatures.length; i++) {
          const item = inViewportFeatures[i];
          if (heap.size() < maxFeatures) {
            heap.push(item);
          } else if (item.area > heap.peek().area) {
            heap.pop();
            heap.push(item);
          }
        }
        finalFeatures = heap.toArraySortedDescending().map(item => item.feature);
      } else {
        const heap = new MinHeap((a, b) => b.area - a.area);
        for (let i = 0; i < inViewportFeatures.length; i++) {
          const item = inViewportFeatures[i];
          if (heap.size() < maxFeatures) {
            heap.push(item);
          } else if (item.area < heap.peek().area) {
            heap.pop();
            heap.push(item);
          }
        }
        finalFeatures = heap.toArraySortedDescending().map(item => item.feature);
      }
    }

    const endTime = (typeof performance !== 'undefined' && performance.now) ? performance.now() : Date.now();
    const stats = {
      totalInViewport,
      renderedCount: finalFeatures.length,
      isCapped,
      maxFeatures,
      sortProperty,
      executionTimeMs: +(endTime - startTime).toFixed(2)
    };

    return {
      optimizedGeoJSON: {
        type: 'FeatureCollection',
        features: finalFeatures
      },
      stats
    };
  }

  /**
   * AreaPriorityLimiter Controller for MapLibre GL JS & GeoLibre
   */
  class AreaPriorityLimiter {
    constructor(map, options = {}) {
      this.map = map;
      this.sourceId = options.sourceId || null;
      this.layerId = options.layerId || null;
      this.options = {
        maxFeatures: options.maxFeatures || 500,
        sortProperty: options.sortProperty || 'area_ha',
        sortOrder: options.sortOrder || 'desc',
        minAreaThreshold: options.minAreaThreshold || 0.0,
        debounceMs: options.debounceMs || 200,
        onLimitApplied: options.onLimitApplied || null,
        ...options
      };

      this._rawGeoJSON = options.data || null;
      this._timer = null;
      this._boundOnMoveEnd = this._onMoveEnd.bind(this);
      this._enabled = false;
    }

    setData(geojson) {
      this._rawGeoJSON = geojson;
      if (this._enabled) {
        this.apply();
      }
    }

    setMaxFeatures(count) {
      this.options.maxFeatures = parseInt(count, 10) || 500;
      if (this._enabled) {
        this.apply();
      }
    }

    enable() {
      if (this._enabled) return;
      this._enabled = true;
      if (this.map) {
        this.map.on('moveend', this._boundOnMoveEnd);
        this.map.on('zoomend', this._boundOnMoveEnd);
      }
      this.apply();
    }

    disable() {
      if (!this._enabled) return;
      this._enabled = false;
      if (this.map) {
        this.map.off('moveend', this._boundOnMoveEnd);
        this.map.off('zoomend', this._boundOnMoveEnd);
      }
      if (this.sourceId && this.map && this._rawGeoJSON) {
        const src = this.map.getSource(this.sourceId);
        if (src && src.setData) {
          src.setData(this._rawGeoJSON);
        }
      }
    }

    _onMoveEnd() {
      if (!this._enabled) return;
      clearTimeout(this._timer);
      this._timer = setTimeout(() => this.apply(), this.options.debounceMs);
    }

    apply() {
      if (!this._rawGeoJSON || !this.map) return null;

      const bounds = this.map.getBounds();
      const bbox = [bounds.getWest(), bounds.getSouth(), bounds.getEast(), bounds.getNorth()];

      const result = optimizeFeatureCollection(this._rawGeoJSON, {
        ...this.options,
        bbox
      });

      if (this.sourceId) {
        const src = this.map.getSource(this.sourceId);
        if (src && src.setData) {
          src.setData(result.optimizedGeoJSON);
        }
      }

      if (typeof this.options.onLimitApplied === 'function') {
        this.options.onLimitApplied({
          layerId: this.layerId || this.sourceId,
          ...result.stats
        });
      }

      return result;
    }
  }

  return {
    MinHeap,
    computeRingAreaHectares,
    getFeatureArea,
    isFeatureInBBox,
    optimizeFeatureCollection,
    AreaPriorityLimiter
  };
});

