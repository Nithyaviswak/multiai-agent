import { Car, Bus, TrainFront, Bike, UtensilsCrossed, Clock, MapPinned, Scale } from 'lucide-react';
import { fmtKm, fmtMin } from '../lib/format';

const MODE_ICONS = { car: Car, bus: Bus, train: TrainFront, bike: Bike };

const Row = ({ label, value }) => (
  <div className="flex items-center justify-between gap-3 py-2 border-b border-paper-line last:border-none text-[12.5px]">
    <span className="text-ink-mute">{label}</span>
    <span className="font-medium text-ink text-right">{value}</span>
  </div>
);

const Chip = ({ children }) => (
  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-paper-inset text-[11px] font-medium text-ink-soft capitalize">
    {children}
  </span>
);

const TripSummary = ({ data }) => {
  const plan = data.plan_data || {};
  const route = data.route_data || {};
  const restaurants = data.restaurants_data || {};
  const itinerary = data.itinerary_data || {};
  const prefs = plan.preferences || {};

  return (
    <div className="rounded-2xl border border-paper-line bg-paper-elevated p-4">
      <p className="text-[10.5px] font-semibold uppercase tracking-wider text-ink-mute flex items-center gap-1.5 mb-1">
        <Scale className="w-3 h-3 text-primary" /> Trip at a glance
      </p>

      <div className="divide-y divide-paper-line">
        <Row label="Route" value={`${plan.origin || '—'} → ${plan.destination || '—'}`} />
        <Row label="Best transport" value={route.best_label || '—'} />
        <Row label="Travel time" value={route.best_duration_min != null ? fmtMin(route.best_duration_min) : '—'} />
        <Row label="Distance" value={fmtKm(route.best_distance_km)} />
        <Row label="Time budget" value={prefs.days > 1 ? `${prefs.days} days` : itinerary.time_budget_minutes != null ? `${itinerary.time_budget_minutes} min` : '—'} />
        <Row label="Meals planned" value={plan.meal_types?.length ? plan.meal_types.map(m => m).join(', ') : '—'} />
        <Row label="Places covered" value={(itinerary.stops || []).filter(s => s.kind === 'place').length} />
        <Row label="Restaurants" value={restaurants.total ?? 0} />
      </div>

      <div className="mt-3 space-y-1.5">
        <p className="text-[10px] font-medium text-ink-mute uppercase tracking-wider flex items-center gap-1">
          <MapPinned className="w-3 h-3" /> Modes compared
        </p>
        <div className="flex flex-wrap gap-1.5">
          {(plan.travel_modes || route.modes?.map(m => m.mode) || []).map(mode => {
            const Icon = MODE_ICONS[mode];
            return (
              <Chip key={mode}>
                {Icon && <Icon className="w-3 h-3 text-ink-mute" />} {mode}
              </Chip>
            );
          })}
          {!(plan.travel_modes?.length) && <Chip>—</Chip>}
        </div>
      </div>

      <div className="mt-3 space-y-1.5">
        <p className="text-[10px] font-medium text-ink-mute uppercase tracking-wider flex items-center gap-1">
          <UtensilsCrossed className="w-3 h-3" /> Meals
        </p>
        <div className="flex flex-wrap gap-1.5">
          {(plan.meal_types || []).map(meal => (
            <Chip key={meal}>{meal}</Chip>
          ))}
          {!plan.meal_types?.length && <Chip>No meals requested</Chip>}
        </div>
      </div>

      <div className="mt-3 flex items-center gap-1.5 text-[11px] text-ink-faint">
        <Clock className="w-3 h-3" />
        {itinerary.start_time ? `Departs ${itinerary.start_time} · arrives ${itinerary.end_time || '—'}` : 'Day trip · timed itinerary'}
      </div>
    </div>
  );
};

export default TripSummary;