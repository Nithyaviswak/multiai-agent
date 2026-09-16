import { Car, Bus, TrainFront, Bike, MapPin, Clock, Scale } from 'lucide-react';
import { fmtMin, fmtKm } from '../lib/format';

const MODE_ICONS = { car: Car, bus: Bus, train: TrainFront, bike: Bike };

const TransportCompare = ({ route }) => {
  const modes = route?.modes || [];
  const best = route?.best_mode;

  if (!modes.length) {
    return (
      <div className="rounded-2xl border border-dashed border-paper-line bg-paper-inset/40 p-5 text-center">
        <Scale className="w-5 h-5 mx-auto text-ink-mute mb-2" />
        <p className="text-[12.5px] text-ink-mute">Transport comparison isn't available yet.</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {modes.map(m => {
        const Icon = MODE_ICONS[m.mode] || MapPin;
        const isBest = m.mode === best;
        return (
          <div key={m.mode} className={`rounded-xl p-3.5 border transition-colors ${isBest ? 'bg-primary-soft border-primary/40' : 'bg-paper-elevated border-paper-line'}`}>
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-2 text-[13px] font-semibold text-ink capitalize">
                <Icon className="w-4 h-4" style={{ color: isBest ? 'var(--color-primary)' : 'var(--color-ink-mute)' }} />
                {m.label || m.mode}
              </span>
              <div className="flex items-center gap-2">
                {isBest && <span className="px-2 py-0.5 rounded-full bg-primary/10 text-primary text-[10.5px] font-semibold">Best</span>}
                <span className={`px-2 py-0.5 rounded-full text-[10.5px] font-medium ${m.fits_budget ? 'bg-success/10 text-success' : 'bg-danger/10 text-danger'}`}>
                  {m.fits_budget ? 'Fits' : 'Over'}
                </span>
              </div>
            </div>
            <div className="flex items-center gap-3 mt-1.5 text-[11.5px] text-ink-soft">
              <span className="flex items-center gap-1"><Clock className="w-3 h-3 text-ink-mute" />{fmtMin(m.duration_min)}</span>
              <span>{fmtKm(m.distance_km)}</span>
            </div>
            {m.summary && <p className="text-[11px] text-ink-faint mt-1.5">{m.summary}</p>}
          </div>
        );
      })}

      <div className={`rounded-xl p-3 text-[11.5px] font-medium border ${route?.budget_fits ? 'bg-success/6 border-success/20 text-success' : 'bg-warning/6 border-warning/20 text-warning'}`}>
        {route?.budget_fits
          ? `The best route fits inside your ${route.time_budget_minutes}-minute budget.`
          : `No mode fits inside your ${route.time_budget_minutes}-minute budget — showing the fastest option.`}
      </div>
    </div>
  );
};

export default TransportCompare;