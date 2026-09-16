import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  MapPin, UtensilsCrossed, Landmark, ArrowUp, ArrowDown, Pencil, X,
  Clock, ChevronDown, Star, Plus, RotateCcw, StickyNote,
} from 'lucide-react';
import { fmtKm, fmtMin } from '../lib/format';
import { uid } from '../lib/format';

const KIND_META = {
  departure: { icon: MapPin, color: 'var(--color-primary)', label: 'Departure' },
  arrival: { icon: MapPin, color: 'var(--color-secondary)', label: 'Arrival' },
  place: { icon: Landmark, color: '#7C3AED', label: 'Activity' },
  meal: { icon: UtensilsCrossed, color: '#D97706', label: 'Meal' },
  custom: { icon: StickyNote, color: 'var(--color-ink-mute)', label: 'Custom' },
};

const ActivityContent = ({ stop }) => {
  const meta = KIND_META[stop.kind] || KIND_META.place;
  return (
    <div className="flex-1 min-w-0">
      <div className="flex items-center gap-2">
        <p className="text-[14px] font-semibold text-ink truncate">{stop.label}</p>
        {stop.kind === 'meal' && stop.restaurant_name && (
          <span className="px-1.5 py-0.5 rounded-md bg-paper-inset text-[10px] font-semibold text-ink-soft truncate max-w-[140px]">
            {stop.restaurant_name}
          </span>
        )}
      </div>
      {stop.description && <p className="text-[12px] text-ink-soft mt-0.5">{stop.description}</p>}

      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-1.5 text-[11px] text-ink-mute">
        {stop.duration_minutes > 0 && (
          <span className="inline-flex items-center gap-1"><Clock className="w-3 h-3" />{fmtMin(stop.duration_minutes)}</span>
        )}
        {stop.distance_km != null && <span>{fmtKm(stop.distance_km)}</span>}
        {stop.rating != null && (
          <span className="inline-flex items-center gap-1 text-warning"><Star className="w-3 h-3 fill-current" />{stop.rating}</span>
        )}
        {stop.kind === 'meal' && stop.restaurant_address && (
          <span className="truncate max-w-full">{stop.restaurant_address}</span>
        )}
        <span className="ml-auto inline-flex items-center gap-1 text-[10px] font-medium uppercase tracking-wider" style={{ color: meta.color }}>
          {meta.label}
        </span>
      </div>
    </div>
  );
};

const ActivityCard = ({ stop, index, total, onMove, onRemove, onRestore, removed, onChange }) => {
  const meta = KIND_META[stop.kind] || KIND_META.place;
  const Icon = meta.icon;
  const [expanded, setExpanded] = useState(false);
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(stop.description || '');

  return (
    <div className="relative flex gap-3 group">
      {/* icon + rail */}
      <div className="flex flex-col items-center flex-shrink-0">
        <div className="relative z-10 w-9 h-9 rounded-full flex items-center justify-center bg-paper-elevated border shadow-sm" style={{ borderColor: meta.color, color: meta.color }}>
          <Icon className="w-4 h-4" />
        </div>
        {index < total - 1 && <div className="w-px flex-1 min-h-6 bg-paper-line" />}
      </div>

      <div className="flex-1 pb-4 min-w-0">
        <motion.div
          layout
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25 }}
          className="rounded-2xl border border-paper-line bg-paper-elevated p-3.5 transition-colors group-hover:border-ink-faint"
        >
          <div className="flex items-start gap-3">
            <div className="text-center flex-shrink-0 w-12">
              <p className="text-[13px] font-bold text-ink tabular-nums leading-none pt-0.5">{stop.time}</p>
              <p className="text-[9.5px] text-ink-faint mt-1 uppercase tracking-wider">Day trip</p>
            </div>

            {editing ? (
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <input
                    value={stop.label}
                    readOnly
                    className="flex-1 text-[13px] font-semibold text-ink bg-paper-inset rounded-lg px-2 py-1.5 opacity-70 cursor-not-allowed"
                    aria-label="Activity title (fixed)"
                  />
                </div>
                <textarea
                  value={draft}
                  onChange={e => setDraft(e.target.value)}
                  rows={2}
                  className="input text-[12.5px] mt-2 bg-paper-elevated"
                  placeholder="Add a personal note for this stop"
                  aria-label="Activity note"
                />
                <div className="flex gap-1.5 mt-2">
                  <button onClick={() => { onChange({ ...stop, description: draft }); setEditing(false); }} className="btn btn-primary py-1.5 px-3 text-[11.5px]">
                    Save note
                  </button>
                  <button onClick={() => { setDraft(stop.description || ''); setEditing(false); }} className="btn btn-secondary py-1.5 px-3 text-[11.5px]">
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <>
                <ActivityContent stop={stop} />

                {/* actions */}
                <div className="flex items-center gap-1 mt-2.5 opacity-0 group-focus-within:opacity-100 group-hover:opacity-100 transition-opacity">
                  <button onClick={() => onMove(index, -1)} disabled={index === 0} className="w-7 h-7 rounded-lg flex items-center justify-center text-ink-mute hover:text-ink hover:bg-paper-inset disabled:opacity-30 transition-colors" title="Move earlier" aria-label="Move earlier">
                    <ArrowUp className="w-3.5 h-3.5" />
                  </button>
                  <button onClick={() => onMove(index, 1)} disabled={index === total - 1} className="w-7 h-7 rounded-lg flex items-center justify-center text-ink-mute hover:text-ink hover:bg-paper-inset disabled:opacity-30 transition-colors" title="Move later" aria-label="Move later">
                    <ArrowDown className="w-3.5 h-3.5" />
                  </button>
                  <button onClick={() => { setEditing(true); setDraft(stop.description || ''); }} className="w-7 h-7 rounded-lg flex items-center justify-center text-ink-mute hover:text-ink hover:bg-paper-inset transition-colors" title="Edit note" aria-label="Edit note">
                    <Pencil className="w-3.5 h-3.5" />
                  </button>
                  <button onClick={() => setExpanded(e => !e)} className="w-7 h-7 rounded-lg flex items-center justify-center text-ink-mute hover:text-ink hover:bg-paper-inset transition-colors" title="Details" aria-expanded={expanded} aria-label="Toggle details">
                    <ChevronDown className={`w-3.5 h-3.5 transition-transform duration-200 ${expanded ? 'rotate-180' : ''}`} />
                  </button>
                  <button onClick={() => onRemove(index)} className="w-7 h-7 rounded-lg flex items-center justify-center text-ink-mute hover:text-danger hover:bg-danger/10 transition-colors" title="Remove" aria-label="Remove activity">
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              </>
            )}
          </div>

          <AnimatePresence initial={false}>
            {expanded && !editing && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.22 }}
                className="overflow-hidden"
              >
                <div className="mt-3 pt-3 border-t border-paper-line grid grid-cols-2 gap-2 text-[11.5px]">
                  <div>
                    <p className="text-ink-faint">Time allocated</p>
                    <p className="text-ink-soft font-medium">{fmtMin(stop.duration_minutes)}</p>
                  </div>
                  <div>
                    <p className="text-ink-faint">Category</p>
                    <p className="text-ink-soft font-medium capitalize">{meta.label}</p>
                  </div>
                  {stop.distance_km != null && (
                    <div>
                      <p className="text-ink-faint">Distance from route</p>
                      <p className="text-ink-soft font-medium">{fmtKm(stop.distance_km)}</p>
                    </div>
                  )}
                  {stop.rating != null && (
                    <div>
                      <p className="text-ink-faint">Rating</p>
                      <p className="text-ink-soft font-medium">{stop.rating} ★</p>
                    </div>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>

        {removed && (
          <button onClick={onRestore} className="inline-flex items-center gap-1.5 text-[11px] font-medium text-primary hover:text-primary-deep mt-1 transition-colors">
            <RotateCcw className="w-3 h-3" /> Restore
          </button>
        )}
      </div>
    </div>
  );
};

const ItineraryTimeline = ({ stops, onStopsChange }) => {
  const [removed, setRemoved] = useState(new Set());
  const [newLabel, setNewLabel] = useState('');

  const move = (i, dir) => {
    const next = [...stops];
    const j = i + dir;
    if (j < 0 || j >= next.length) return;
    [next[i], next[j]] = [next[j], next[i]];
    onStopsChange(next);
  };

  const remove = (i) => {
    setRemoved(prev => new Set(prev).add(i));
  };

  const restore = (i) => {
    setRemoved(prev => { const n = new Set(prev); n.delete(i); return n; });
  };

  const editStop = (updated) => {
    onStopsChange(stops.map(s => (s.id === updated.id ? updated : s)));
  };

  const addStop = () => {
    if (!newLabel.trim()) return;
    const last = stops[stops.length - 1];
    const t = last?.time || '18:00';
    onStopsChange([...stops, {
      id: uid(),
      kind: 'custom',
      label: newLabel.trim(),
      description: 'Personal stop added while reviewing the plan.',
      time: t,
      duration_minutes: 0,
    }]);
    setNewLabel('');
  };

  const visible = stops.filter((_, i) => !removed.has(i));

  return (
    <div>
      <div>
        {visible.map((s, vi) => {
          // map visible index back to original index
          const origIndex = stops.findIndex(st => st.id === s.id);
          return (
            <ActivityCard
              key={s.id}
              stop={s}
              index={vi}
              total={visible.length}
              onMove={move}
              onRemove={() => remove(origIndex)}
              onRestore={() => restore(origIndex)}
              removed={removed.has(origIndex)}
              onChange={editStop}
            />
          );
        })}
      </div>

      {/* add stop */}
      <div className="flex items-center gap-2 pl-12 pt-1">
        <div className="relative flex-1">
          <input
            value={newLabel}
            onChange={e => setNewLabel(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); addStop(); } }}
            placeholder="Add a personal stop (e.g. coffee at CMH Road)"
            className="input input-sm py-2 text-[12.5px] bg-paper-elevated"
            aria-label="Add a stop"
          />
        </div>
        <button onClick={addStop} disabled={!newLabel.trim()} className="btn btn-secondary py-2 px-3 text-[12px] disabled:opacity-40">
          <Plus className="w-3.5 h-3.5" /> Add
        </button>
      </div>
    </div>
  );
};

export default ItineraryTimeline;