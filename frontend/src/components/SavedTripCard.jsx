import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';
import { ArrowRight, Bookmark, Trash2, Clock, Route as RouteIcon, UtensilsCrossed } from 'lucide-react';
import { fmtDate, fmtMin } from '../lib/format';

const SavedTripCard = ({ trip, index, onOpen, onRemove }) => {
  const plan = trip.data?.plan_data || {};
  const route = trip.data?.route_data || {};
  const restaurants = trip.data?.restaurants_data || {};
  const [arming, setArming] = useState(false);

  // Auto-disarm the "confirm" state if the user walks away
  useEffect(() => {
    if (!arming) return undefined;
    const t = setTimeout(() => setArming(false), 4500);
    return () => clearTimeout(t);
  }, [arming]);

  const confirmRemove = () => {
    setArming(false);
    onRemove();
  };

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.97 }}
      transition={{ delay: index * 0.04, duration: 0.3 }}
      className="rounded-2xl border border-paper-line bg-paper-elevated p-4 sm:p-5 hover:border-ink-faint transition-colors group"
    >
      <div className="flex items-start justify-between gap-3">
        <button onClick={onOpen} className="text-left min-w-0 flex-1">
          <div className="flex items-center gap-2 mb-1.5 flex-wrap">
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-primary-soft text-primary text-[10px] font-semibold">
              <Bookmark className="w-3 h-3 fill-current" /> Saved
            </span>
            <span className="text-[10.5px] text-ink-faint">{fmtDate(trip.savedAt)}</span>
          </div>
          <h3 className="font-serif text-[22px] leading-tight text-ink group-hover:text-primary transition-colors">
            {plan.origin || trip.origin || 'Origin'} <span className="text-ink-mute">→</span> {plan.destination || trip.destination || 'Destination'}
          </h3>
          <p className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-2 text-[12px] text-ink-soft">
            <span className="inline-flex items-center gap-1">
              <Clock className="w-3.5 h-3.5 text-primary" />{fmtMin(route.best_duration_min)}
            </span>
            {route.best_label && (
              <span className="inline-flex items-center gap-1 capitalize"><RouteIcon className="w-3.5 h-3.5 text-secondary" />{route.best_label}</span>
            )}
            {restaurants.total > 0 && (
              <span className="inline-flex items-center gap-1"><UtensilsCrossed className="w-3.5 h-3.5 text-warning" />{restaurants.total} restaurants</span>
            )}
          </p>
        </button>

        <div className="flex items-center gap-1.5 flex-shrink-0">
          {arming && (
            <motion.button
              initial={{ opacity: 0, x: 6 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.15 }}
              onClick={() => setArming(false)}
              className="h-8 px-2.5 rounded-full text-[11.5px] font-semibold text-ink-soft hover:text-ink hover:bg-paper-inset transition-colors"
              aria-label="Keep this trip"
            >
              Keep
            </motion.button>
          )}
          <button
            onClick={() => (arming ? confirmRemove() : setArming(true))}
            onBlur={() => setArming(false)}
            className={`h-8 px-2.5 rounded-full flex items-center justify-center gap-1 text-[11.5px] font-semibold transition-all flex-shrink-0 ${
              arming
                ? 'bg-danger/10 text-danger shadow-sm'
                : 'text-ink-mute hover:text-danger hover:bg-danger/10'
            }`}
            aria-label={arming ? 'Confirm remove saved trip' : 'Remove saved trip'}
          >
            <Trash2 className="w-3.5 h-3.5" />
            {arming && 'Remove?'}
          </button>
        </div>
      </div>

      <button
        onClick={onOpen}
        className="mt-4 inline-flex items-center gap-1.5 text-[12.5px] font-semibold text-primary hover:text-primary-deep transition-colors"
      >
        Open trip <ArrowRight className="w-3.5 h-3.5" />
      </button>
    </motion.div>
  );
};

export default SavedTripCard;