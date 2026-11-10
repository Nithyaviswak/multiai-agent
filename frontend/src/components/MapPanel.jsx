import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Map as MapLibreMap, NavigationControl } from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { motion } from 'framer-motion';
import { CircleDot, Globe2, Loader2, MapPin, Route as RouteIcon } from 'lucide-react';
import { useTheme } from '../hooks/useTheme';

const KIND_COLORS = {
  departure: '#2563EB',
  arrival: '#0EA5E9',
  place: '#8B5CF6',
  meal: '#D97706',
};

// OpenFreeMap styles — theme-awsare positron (light) / dark (dark).
const STYLES = {
  light: 'https://tiles.openfreemap.org/styles/positron',
  dark: 'https://tiles.openfreemap.org/styles/dark',
};

const PAD = 36;

const project = (points, w, h) => {
  const lats = points.map(p => p[0]);
  const lngs = points.map(p => p[1]);
  const minLat = Math.min(...lats), maxLat = Math.max(...lats);
  const minLng = Math.min(...lngs), maxLng = Math.max(...lngs);
  const latR = maxLat - minLat || 0.0001;
  const lngR = maxLng - minLng || 0.0001;
  return points.map(p => ({
    x: PAD + ((p[1] - minLng) / lngR) * (w - PAD * 2),
    y: PAD + ((maxLat - p[0]) / latR) * (h - PAD * 2),
  }));
};

const useItineraryPins = (itinerary, places, restaurants) => {
  return useMemo(() => {
    const pinByPlace = {};
    (places?.places || []).forEach((p, i) => {
      if (p.lat != null && p.lng != null) pinByPlace[p.name] = { ...p, index: i };
    });
    const restByName = {};
    Object.values(restaurants?.meals || {}).flat().forEach(r => {
      if (r.lat != null && r.lng != null) restByName[r.name] = r;
    });

    let counter = 0;
    const stops = (itinerary?.stops || []).map(s => {
      const src = pinByPlace[s.label] || restByName[s.label] || restByName[s.restaurant_name];
      if (src && src.lat != null && src.lng != null) {
        counter += 1;
        return { num: counter, kind: s.kind, label: s.label, time: s.time, lat: src.lat, lng: src.lng };
      }
      return null;
    }).filter(Boolean);
    return stops;
  }, [itinerary, places, restaurants]);
};

// Draws a numbered map-pin as raw pixel data for maplibre's icon registry.
const makePinImage = (num, color) => {
  const S = 72;
  const canvas = document.createElement('canvas');
  canvas.width = S;
  canvas.height = S;
  const ctx = canvas.getContext('2d');
  ctx.beginPath();
  ctx.moveTo(S / 2, S - 5);
  ctx.quadraticCurveTo(S / 2 - 16, S - 30, S / 2 - 16, S / 2);
  ctx.arc(S / 2, S / 2, 20, Math.PI, 0, false);
  ctx.quadraticCurveTo(S / 2 + 16, S - 30, S / 2, S - 5);
  ctx.closePath();
  ctx.fillStyle = color;
  ctx.fill();
  ctx.strokeStyle = '#FFFFFF';
  ctx.lineWidth = 4;
  ctx.lineJoin = 'round';
  ctx.stroke();
  ctx.fillStyle = '#FFFFFF';
  ctx.font = '700 25px Inter, system-ui, sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(String(num), S / 2, S / 2 + 1);
  return ctx.getImageData(0, 0, S, S);
};

const MapPanel = ({ route, places, restaurants, itinerary }) => {
  const pins = useItineraryPins(itinerary, places, restaurants);
  const via = (route?.via_points || []).filter(p => Array.isArray(p) && p.length === 2 && p.every(Number.isFinite));
  const hasPath = via.length >= 2;
  const hasPins = pins.length > 0;
  const hasData = hasPath || hasPins;

  const { isDark } = useTheme();
  const containerRef = useRef(null);
  const mapRef = useRef(null);
  const styleRef = useRef(STYLES.light);
  const [mapFailed, setMapFailed] = useState(false);
  const [mapLoaded, setMapLoaded] = useState(false);

  // GeoJSON forms of the route + markers (coordinates are [lng, lat] for GeoJSON).
  const routeGeo = useMemo(() => ({
    type: 'Feature',
    properties: {},
    geometry: { type: 'LineString', coordinates: via.map(p => [p[1], p[0]]) },
  }), [via]);

  const ends = useMemo(() => {
    if (via.length < 2) return { type: 'FeatureCollection', features: [] };
    const toPoint = p => [p[1], p[0]];
    return {
      type: 'FeatureCollection',
      features: [
        { type: 'Feature', properties: { kind: 'origin' }, geometry: { type: 'Point', coordinates: toPoint(via[0]) } },
        { type: 'Feature', properties: { kind: 'dest' }, geometry: { type: 'Point', coordinates: toPoint(via[via.length - 1]) } },
      ],
    };
  }, [via]);

  const pinFeatures = useMemo(() => ({
    type: 'FeatureCollection',
    features: pins.map((pin, i) => ({
      type: 'Feature',
      properties: { icon: `pin-${i + 1}` },
      geometry: { type: 'Point', coordinates: [pin.lng, pin.lat] },
    })),
  }), [pins]);

  const dataRef = useRef({ routeGeo, ends, pinFeatures, pins, isDark });
  dataRef.current = { routeGeo, ends, pinFeatures, pins, isDark };

  // (Re)builds sources + layers and re-registers numbered pin images. Safe to
  // call on every style.load (theme swap) and whenever route data changes.
  const syncData = useCallback((map) => {
    const { routeGeo: rg, ends: en, pinFeatures: pf, pins: ps, isDark: dark } = dataRef.current;
    const hasRoute = (rg.geometry.coordinates.length || 0) > 1;

    const dropLayer = id => { if (map.getLayer(id)) map.removeLayer(id); };
    const dropSource = id => { if (map.getSource(id)) map.removeSource(id); };

    if (!map.getSource('route-src')) {
      // Full rebuild — happens on mount and after every style swap.
      dropLayer('pin-layer'); dropLayer('dest-layer'); dropLayer('origin-layer');
      dropLayer('route-line'); dropLayer('route-casing');
      dropSource('pins-src'); dropSource('ends-src'); dropSource('route-src');

      ps.forEach((pin, i) => {
        const id = `pin-${i + 1}`;
        if (!map.hasImage(id)) map.addImage(id, makePinImage(i + 1, KIND_COLORS[pin.kind] || KIND_COLORS.place));
      });

      map.addSource('route-src', { type: 'geojson', data: rg });
      if (hasRoute) {
        map.addLayer({
          id: 'route-casing', type: 'line', source: 'route-src',
          paint: {
            'line-color': dark ? '#0F172A' : '#FFFFFF',
            'line-width': 7,
            'line-opacity': 0.95,
          },
        });
        map.addLayer({
          id: 'route-line', type: 'line', source: 'route-src',
          paint: { 'line-color': '#2563EB', 'line-width': 4, 'line-opacity': 0.9 },
        });
      }
      map.addSource('ends-src', { type: 'geojson', data: en });
      map.addLayer({
        id: 'origin-layer', type: 'circle', source: 'ends-src',
        filter: ['==', ['get', 'kind'], 'origin'],
        paint: {
          'circle-radius': 8, 'circle-color': '#2563EB',
          'circle-stroke-color': '#FFFFFF', 'circle-stroke-width': 2.5,
        },
      });
      map.addLayer({
        id: 'dest-layer', type: 'circle', source: 'ends-src',
        filter: ['==', ['get', 'kind'], 'dest'],
        paint: {
          'circle-radius': 8, 'circle-color': '#0EA5E9',
          'circle-stroke-color': '#FFFFFF', 'circle-stroke-width': 2.5,
        },
      });
      map.addSource('pins-src', { type: 'geojson', data: pf });
      map.addLayer({
        id: 'pin-layer', type: 'symbol', source: 'pins-src',
        layout: {
          'icon-image': ['get', 'icon'],
          'icon-size': 0.62,
          'icon-allow-overlap': true,
          'icon-anchor': 'bottom',
        },
      });
    } else {
      // Same style — stream the updated geometries into the existing sources.
      map.getSource('route-src').setData(rg);
      map.getSource('ends-src').setData(en);
      map.getSource('pins-src').setData(pf);
    }

    // Zoom to the whole route (single shot, resumed on theme swaps).
    const all = [];
    if (hasRoute) all.push(...rg.geometry.coordinates);
    en.features.forEach(f => all.push(f.geometry.coordinates));
    pf.features.forEach(f => all.push(f.geometry.coordinates));
    if (all.length >= 2) {
      const lngs = all.map(c => c[0]);
      const lats = all.map(c => c[1]);
      let minLng = Math.min(...lngs), minLat = Math.min(...lats);
      let maxLng = Math.max(...lngs), maxLat = Math.max(...lats);
      if (minLng === maxLng) { minLng -= 0.02; maxLng += 0.02; }
      if (minLat === maxLat) { minLat -= 0.02; maxLat += 0.02; }
      map.fitBounds([[minLng, minLat], [maxLng, maxLat]], { padding: 48, maxZoom: 13, duration: 350 });
    }
  }, []);

  // Create the map once data is available (WebGL required; fallback to SVG).
  useEffect(() => {
    if (!hasData || mapFailed) return;
    if (!containerRef.current || mapRef.current) return;

    let disposed = false;
    const map = new MapLibreMap({
      container: containerRef.current,
      style: styleRef.current,
      center: [77.59, 12.97],
      zoom: 5,
      attributionControl: { compact: true },
    });
    mapRef.current = map;
    map.addControl(new NavigationControl({ showCompass: false }), 'top-right');
    map.on('load', () => { if (!disposed) setMapLoaded(true); syncData(map); });
    map.on('style.load', () => syncData(map));
    map.on('error', (e) => {
      if (/webgl/i.test(e?.error?.message || '')) setMapFailed(true);
    });
    const ro = new ResizeObserver(() => map.resize());
    if (containerRef.current) ro.observe(containerRef.current);

    return () => {
      disposed = true;
      ro.disconnect();
      map.remove();
      mapRef.current = null;
    };
  }, [hasData, mapFailed, syncData]);

  // Swap the tile style when the app theme changes.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || mapFailed) return;
    const target = isDark ? STYLES.dark : STYLES.light;
    if (styleRef.current === target) return;
    styleRef.current = target;
    map.setStyle(target);
  }, [isDark, mapFailed]);

  // Push updated route/marker data into the map whenever it changes.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || mapFailed || !hasData) return;
    if (map.isStyleLoaded()) syncData(map);
  }, [routeGeo, ends, pinFeatures, mapFailed, hasData, syncData]);

  // ---- Schematic fallback (WebGL unavailable or no real map needed) ----
  const W = 640, H = 360;
  const { routePts, pinPts } = useMemo(() => {
    const pts = [];
    if (hasPath) pts.push(...via);
    pins.forEach(p => pts.push([p.lat, p.lng]));
    if (pts.length === 0) return { routePts: [], pinPts: {} };
    const projected = project(pts, W, H);
    const byId = new Map(pins.map((p, i) => [i, projected[projected.length - pins.length + i]]));
    return { routePts: projected.slice(0, projected.length - pins.length), pinPts: byId };
  }, [via, pins, hasPath]);

  if (!hasData) {
    return (
      <div className="rounded-2xl border border-dashed border-paper-line bg-paper-inset/40 p-6 text-center">
        <div className="w-10 h-10 mx-auto rounded-full bg-paper-inset flex items-center justify-center mb-3">
          <MapPin className="w-5 h-5 text-ink-mute" />
        </div>
        <p className="text-[13px] font-semibold text-ink">Map preview</p>
        <p className="text-[11.5px] text-ink-mute mt-1 max-w-xs mx-auto">
          Location coordinates aren't available for this trip yet, so we can't draw the route. It'll appear once the planner returns map data.
        </p>
      </div>
    );
  }

  const pathD = routePts.length >= 2
    ? routePts.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ')
    : '';

  const schematic = (
    <div className="rounded-2xl overflow-hidden border border-paper-line bg-paper-elevated relative">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto block" role="img" aria-label="Route map preview">
        <defs>
          <pattern id="mapgrid" width="48" height="48" patternUnits="userSpaceOnUse">
            <path d="M48 0H0V48" fill="none" stroke="var(--color-paper-line)" strokeOpacity="0.5" strokeWidth="1" />
          </pattern>
        </defs>
        <rect width={W} height={H} fill="var(--color-paper-inset)" opacity="0.35" />
        <rect width={W} height={H} fill="url(#mapgrid)" />

        {pathD && (
          <motion.path
            key={JSON.stringify(via)}
            d={pathD}
            fill="none"
            stroke="var(--color-primary)"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
            initial={{ strokeDashoffset: 3000, opacity: 0 }}
            animate={{ strokeDashoffset: 0, opacity: 0.85 }}
            transition={{ duration: 1.2, ease: 'easeOut' }}
            style={{ strokeDasharray: 3000 }}
          />
        )}

        {routePts.length > 0 && (
          <>
            <circle cx={routePts[0].x} cy={routePts[0].y} r="7" fill="#fff" stroke="var(--color-primary)" strokeWidth="2.5" />
            <circle cx={routePts[0].x} cy={routePts[0].y} r="2" fill="var(--color-primary)" />
          </>
        )}
        {routePts.length > 1 && (
          <>
            <circle cx={routePts[routePts.length - 1].x} cy={routePts[routePts.length - 1].y} r="7" fill="var(--color-secondary)" />
            <circle cx={routePts[routePts.length - 1].x} cy={routePts[routePts.length - 1].y} r="2.5" fill="#fff" />
          </>
        )}

        {pins.map((pin, i) => {
          const pt = pinPts.get(i);
          if (!pt) return null;
          const color = KIND_COLORS[pin.kind] || KIND_COLORS.place;
          return (
            <g key={`${pin.label}-${i}`}>
              <line x1={pt.x} y1={pt.y} x2={pt.x} y2={pt.y - 26} stroke={color} strokeWidth="1.5" />
              <circle cx={pt.x} cy={pt.y - 27} r="11" fill={color} stroke="#fff" strokeWidth="2" />
              <text x={pt.x} y={pt.y - 23} textAnchor="middle" fontSize="10" fontWeight="700" fill="#fff">{pin.num}</text>
            </g>
          );
        })}
      </svg>

      <div className="absolute top-2.5 left-2.5 flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-paper-elevated/90 backdrop-blur border border-paper-line text-[10px] font-semibold text-ink-soft">
        <RouteIcon className="w-3 h-3 text-primary" /> Schematic route preview
      </div>
    </div>
  );

  return (
    <div>
      {mapFailed
        ? schematic
        : (
          <div className="rounded-2xl overflow-hidden border border-paper-line bg-paper-elevated relative">
            <div className="relative w-full h-72 sm:h-80">
              <div ref={containerRef} className="absolute inset-0" role="img" aria-label="Interactive OpenStreetMap route map" />
              {!mapLoaded && (
                <div className="absolute inset-0 flex items-center justify-center bg-paper-elevated/60 backdrop-blur-sm">
                  <Loader2 className="w-5 h-5 text-primary animate-spin" />
                </div>
              )}
              <div className="absolute top-2.5 left-2.5 flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-paper-elevated/90 backdrop-blur border border-paper-line text-[10px] font-semibold text-ink-soft">
                <Globe2 className="w-3 h-3 text-primary" /> OpenStreetMap · OpenFreeMap
              </div>
              {!hasPath && hasPins && (
                <p className="absolute bottom-2.5 left-2.5 inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-paper-elevated/90 backdrop-blur border border-paper-line text-[10px] text-ink-faint">
                  <CircleDot className="w-3 h-3" /> Points only — no route line.
                </p>
              )}
            </div>
          </div>
        )}

      {pins.length > 0 && (
        <ul className="mt-3 space-y-1" aria-label="Map markers">
          {pins.map(pin => (
            <li key={`${pin.label}-${pin.num}`} className="flex items-center gap-2.5 text-[12px] text-ink-soft">
              <span className="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold text-white flex-shrink-0" style={{ background: KIND_COLORS[pin.kind] || KIND_COLORS.place }}>
                {pin.num}
              </span>
              <span className="truncate">{pin.label}</span>
              <span className="ml-auto text-[10.5px] text-ink-faint">{pin.time}</span>
            </li>
          ))}
        </ul>
      )}

      {!hasPath && hasPins && !mapFailed && (
        <p className="mt-2 text-[10.5px] text-ink-faint inline-flex items-center gap-1">
          <CircleDot className="w-3 h-3" /> Route line not available — showing points only.
        </p>
      )}
    </div>
  );
};

export default MapPanel;