import { motion } from 'framer-motion';
import { ArrowRight, Bookmark, Trash2, Clock, Route as RouteIcon, UtensilsCrossed } from 'lucide-react';
import { fmtDate, fmtMin } from '../lib/format';

const SavedTripCard = ({ trip, index, onOpen, onRemove }) => {
  const plan = trip.data?.plan_data || {};
  const route = trip.data?.route_data || {};
  const restaurants = trip.data?.restaurants_data || {};

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

        <button
          onClick={onRemove}
          className="w-8 h-8 rounded-full flex items-center justify-center text-ink-mute hover:text-danger hover:bg-danger/10 transition-colors flex-shrink-0"
          aria-label="Remove saved trip"
        >
          <Trash2 className="w-4 h-4" />
        </button>
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