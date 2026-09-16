import { motion, AnimatePresence } from 'framer-motion';
import { Briefcase, Sparkles } from 'lucide-react';
import SavedTripCard from '../components/SavedTripCard';

const TripsPage = ({ trips, onOpen, onRemove, onNavigate }) => (
  <motion.div
    initial={{ opacity: 0, y: 10 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: -10 }}
    transition={{ duration: 0.35 }}
    className="max-w-3xl mx-auto pt-10 pb-10 px-4 sm:px-0"
  >
    <div className="mb-8">
      <div className="flex items-center gap-3">
        <div className="w-11 h-11 rounded-2xl bg-primary-soft flex items-center justify-center">
          <Briefcase className="w-5 h-5 text-primary" />
        </div>
        <div>
          <h1 className="font-serif text-[34px] leading-none tracking-tight">My trips</h1>
          <p className="text-[13px] text-ink-soft mt-1.5">
            {trips.length} saved plan{trips.length === 1 ? '' : 's'} · stored in this browser
          </p>
        </div>
      </div>
    </div>

    <AnimatePresence mode="popLayout">
      {trips.map((t, i) => (
        <div key={t.id} className="mb-3">
          <SavedTripCard
            trip={t}
            index={i}
            onOpen={() => onOpen(t)}
            onRemove={() => onRemove(t.id)}
          />
        </div>
      ))}
    </AnimatePresence>

    {!trips.length && (
      <div className="rounded-3xl border border-dashed border-paper-line bg-paper-elevated/60 p-10 text-center">
        <Sparkles className="w-6 h-6 mx-auto text-ink-faint mb-3" />
        <p className="font-serif text-[22px] text-ink">No trips saved yet</p>
        <p className="text-[13px] text-ink-soft mt-1.5 mb-5">
          When a plan looks right, tap Save and it'll live here for quick access.
        </p>
        <button onClick={() => onNavigate('explore')} className="btn btn-primary">
          Plan a trip <Sparkles className="w-4 h-4" />
        </button>
      </div>
    )}
  </motion.div>
);

export default TripsPage;