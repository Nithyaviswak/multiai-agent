import { useMemo } from 'react';
import { MapPin, Route as RouteIcon, CircleDot } from 'lucide-react';

const KIND_COLORS = {
  departure: '#4F46E5',
  arrival: '#0F766E',
  place: '#7C3AED',
  meal: '#D97706',
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

const MapPanel = ({ route, places, restaurants, itinerary }) => {
  const pins = useItineraryPins(itinerary, places, restaurants);
  const via = (route?.via_points || []).filter(p => Array.isArray(p) && p.length === 2 && p.every(Number.isFinite));
  const hasPath = via.length >= 2;
  const hasPins = pins.length > 0;

  const W = 640, H = 360;

  const { routePts, pinPts } = useMemo(() => {
    const pts = [];
    if (hasPath) pts.push(...via);
    pins.forEach(p => pts.push([p.lat, p.lng]));
    if (pts.length === 0) return { routePts: [], pinPts: {} };
    const projected = project(pts, W, H);
    const byId = new Map(pins.map((p, i) => [i, projected[projected.length - pins.length + i]]));
    // note: projection order keeps appended pins last
    return { routePts: projected.slice(0, projected.length - pins.length), pinPts: byId };
  }, [via, pins, hasPath]);
  // eslint-disable-next-line no-unused-vars

  if (!hasPath && !hasPins) {
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

  return (
    <div>
      <div className="rounded-2xl overflow-hidden border border-paper-line bg-paper-elevated relative">
        <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto block" role="img" aria-label="Route map preview">
          {/* subtle grid */}
          <defs>
            <pattern id="mapgrid" width="48" height="48" patternUnits="userSpaceOnUse">
              <path d="M48 0H0V48" fill="none" stroke="var(--color-paper-line)" strokeOpacity="0.5" strokeWidth="1" />
            </pattern>
          </defs>
          <rect width={W} height={H} fill="var(--color-paper-inset)" opacity="0.35" />
          <rect width={W} height={H} fill="url(#mapgrid)" />

          {pathD && (
            <path d={pathD} fill="none" stroke="var(--color-primary)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" strokeDasharray="0" opacity="0.85" />
          )}

          {/* origin + destination */}
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

          {/* numbered pins */}
          {pins.map((pin, i) => {
            const pt = pinPts.get(i);
            if (!pt) return null;
            const color = KIND_COLORS[pin.kind] || '#4F46E5';
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

      {pins.length > 0 && (
        <ul className="mt-3 space-y-1" aria-label="Map markers">
          {pins.map(pin => (
            <li key={`${pin.label}-${pin.num}`} className="flex items-center gap-2.5 text-[12px] text-ink-soft">
              <span className="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold text-white flex-shrink-0" style={{ background: KIND_COLORS[pin.kind] || '#4F46E5' }}>
                {pin.num}
              </span>
              <span className="truncate">{pin.label}</span>
              <span className="ml-auto text-[10.5px] text-ink-faint">{pin.time}</span>
            </li>
          ))}
        </ul>
      )}

      {!hasPath && hasPins && (
        <p className="mt-2 text-[10.5px] text-ink-faint inline-flex items-center gap-1">
          <CircleDot className="w-3 h-3" /> Route line not available — showing points only.
        </p>
      )}
    </div>
  );
};

export default MapPanel;