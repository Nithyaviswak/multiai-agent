import { motion } from 'framer-motion';
import {
  Bookmark, Share2, PencilLine, Sparkles, Car, Bus, TrainFront, Bike,
  Clock, Users, Calendar,
} from 'lucide-react';
import { fmtMin, fmtDate, capitalize as capitalise } from '../lib/format';

const MODE_ICONS = { car: Car, bus: Bus, train: TrainFront, bike: Bike };
const MODE_LABELS = { car: 'Car', bus: 'Bus', train: 'Train', bike: 'Bike' };

const Chip = ({ icon: Icon, children }) => (
  <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-paper-elevated border border-paper-line text-[11.5px] font-medium text-ink-soft">
    {Icon && <Icon className="w-3.5 h-3.5 text-ink-mute" />}
    {children}
  </span>
);

const TripHeader = ({ data, isSaved, onSave, onShare, onEdit, onRegenerate, iteration }) => {
  const plan = data.plan_data || {};
  const route = data.route_data || {};
  const it = data.itinerary_data || {};
  const prefs = plan.preferences || {};
  const modeIcon = MODE_ICONS[route.best_mode] || Sparkles;

  const origin = plan.origin || data.origin || 'Origin';
  const destination = plan.destination || data.destination || 'Destination';

  const onShareClick = () => {
    if (navigator.share) {
      navigator.share({ title: `Trip: ${origin} → ${destination}`, text: `AI-planned trip from ${origin} to ${destination}` }).catch(() => {});
    } else if (navigator.clipboard) {
      navigator.clipboard.writeText(`${origin} → ${destination} — planned with Multi AI Agent`).catch(() => {});
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-5"
    >
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-primary-soft text-primary text-[11px] font-semibold">
              <Sparkles className="w-3 h-3" /> AI planned{iteration > 0 ? ` · v${iteration + 1}` : ''}
            </span>
          </div>
          <h1 className="font-serif text-4xl sm:text-[44px] leading-[1.05] tracking-tight text-balance">
            {capitalise(origin)} <span className="text-ink-mute">→</span> {capitalise(destination)}
          </h1>
          <p className="text-[14px] text-ink-soft mt-2">
            {fmtMin(route.best_duration_min)} · {it.places_covered?.length ?? 0} places · {it.stops?.length ?? 0} stops
          </p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <button onClick={onSave} className={`btn ${isSaved ? 'btn-success' : 'btn-ghost'} py-2 px-3.5 text-[12.5px]`}>
            <Bookmark className={`w-4 h-4 ${isSaved ? 'fill-current' : ''}`} />
            {isSaved ? 'Saved' : 'Save trip'}
          </button>
          <button onClick={onShareClick} className="btn btn-ghost py-2 px-3.5 text-[12.5px]">
            <Share2 className="w-4 h-4" /> Share
          </button>
          <button onClick={onEdit} className="btn btn-ghost py-2 px-3.5 text-[12.5px]">
            <PencilLine className="w-4 h-4" /> Edit
          </button>
          <button onClick={onRegenerate} className="btn btn-secondary py-2 px-3.5 text-[12.5px]">
            <Sparkles className="w-4 h-4 text-secondary" /> Regenerate
          </button>
        </div>
      </div>

      {/* hero band */}
      <div className="relative overflow-hidden rounded-3xl border border-paper-line bg-gradient-to-br from-primary/10 via-paper-elevated to-secondary/10 p-6 sm:p-8">
        <div className="relative z-10">
          <div className="flex flex-wrap items-center gap-2">
            <Chip icon={modeIcon}>{route.best_label || MODE_LABELS[route.best_mode] || 'Best route'}</Chip>
            <Chip icon={Clock}>{prefs.days > 1 ? `${prefs.days}-day plan` : `Day trip · ${fmtMin(it.time_budget_minutes)}`}</Chip>
            {prefs.travelers ? <Chip icon={Users}>{prefs.travelers} traveler{prefs.travelers > 1 ? 's' : ''}</Chip> : null}
            {prefs.date ? <Chip icon={Calendar}>{fmtDate(prefs.date)}</Chip> : <Chip icon={Calendar}>Day trip</Chip>}
            {prefs.style && <Chip>{capitalise(prefs.style)}</Chip>}
          </div>
          <p className="text-[13.5px] text-ink-soft mt-3 max-w-xl leading-relaxed">
            {it.feasibility === 'fits'
              ? 'Everything fits comfortably inside your time budget.'
              : 'The plan is tight — some activities were trimmed to respect your time budget.'}
            {' '}Your team compared {route.modes?.length ?? 0} transport options and picked the best for you.
          </p>
        </div>
      </div>
    </motion.div>
  );
};

export default TripHeader;