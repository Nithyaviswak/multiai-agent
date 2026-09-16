import { IndianRupee, Clock, Route as RouteIcon, UtensilsCrossed, Landmark, Coffee } from 'lucide-react';

const TIME_COLORS = {
  route: 'var(--color-primary)',
  meals: '#D97706',
  activities: '#7C3AED',
  buffer: 'var(--color-paper-line)',
};

const Legend = ({ icon: Icon, label, min, color, total }) => (
  <div className="flex items-center gap-2 text-[12.5px]">
    <span className="w-2.5 h-2.5 rounded-sm flex-shrink-0" style={{ background: color }} />
    <Icon className="w-3.5 h-3.5 flex-shrink-0" style={{ color }} />
    <span className="flex-1 text-ink-soft">{label}</span>
    <span className="font-medium text-ink text-[12px] tabular-nums">{min} min</span>
    {total > 0 && <span className="text-[10.5px] text-ink-faint w-12 text-right">{Math.round(min / total * 100)}%</span>}
  </div>
);

const BudgetCard = ({ itinerary, route, preferences }) => {
  const total = itinerary?.time_budget_minutes || route?.time_budget_minutes || 0;
  const routeMin = itinerary?.route_minutes || 0;
  const mealMin = itinerary?.meal_minutes || 0;
  const placesMin = itinerary?.places_minutes || 0;
  const bufferMin = Math.max(0, total - routeMin - mealMin - placesMin);
  const segments = [
    { label: 'Travel', min: routeMin, color: TIME_COLORS.route, icon: RouteIcon },
    { label: 'Meals', min: mealMin, color: TIME_COLORS.meals, icon: UtensilsCrossed },
    { label: 'Activities', min: placesMin, color: TIME_COLORS.activities, icon: Landmark },
    { label: 'Buffer', min: bufferMin, color: TIME_COLORS.buffer, icon: Coffee },
  ];
  const degs = segments.map(s => total ? s.min / total * 360 : 90);
  const conic = `conic-gradient(${segments.map((s, i) => `${s.color} ${degs.slice(0, i).reduce((a, b) => a + b, 0)}deg ${degs.slice(0, i + 1).reduce((a, b) => a + b, 0)}deg`).join(', ')})`;

  const feasibility = itinerary?.feasibility;
  const fits = feasibility === 'fits';
  const budget = Number(preferences?.budget);

  return (
    <div className="space-y-5">
      {/* Money budget — clearly marked as target only */}
      {budget > 0 && (
        <div className="rounded-2xl border border-paper-line bg-paper-elevated p-4">
          <div className="flex items-start gap-2 mb-3">
            <div className="w-8 h-8 rounded-xl bg-primary-soft flex items-center justify-center">
              <IndianRupee className="w-4 h-4 text-primary" />
            </div>
            <div>
              <p className="text-[10.5px] font-semibold uppercase tracking-wider text-ink-mute">Target budget</p>
              <p className="font-serif text-2xl text-ink leading-tight">
                ₹{budget.toLocaleString('en-IN')}
              </p>
            </div>
          </div>
          <div className="flex flex-wrap gap-2 text-[11px] text-ink-soft">
            {[
              ['Flights', '—'],
              ['Hotels', '—'],
              ['Food', '—'],
              ['Activities', '—'],
            ].map(([label, val]) => (
              <div key={label} className="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-paper-inset" title="Trip costs aren't estimated by this planner">
                <span className="text-ink-faint">{label}</span>
                <span className="font-medium text-ink-faint">{val}</span>
              </div>
            ))}
          </div>
          <p className="text-[10.5px] text-ink-faint mt-2">Trip costs aren't calculated — this planner budgets time, not money.</p>
        </div>
      )}

      {/* Time budget donut */}
      <div className="rounded-2xl border border-paper-line bg-paper-elevated p-4">
        <div className="flex items-start gap-2 mb-4">
          <div className="w-8 h-8 rounded-xl bg-secondary-soft flex items-center justify-center">
            <Clock className="w-4 h-4 text-secondary" />
          </div>
          <div>
            <p className="text-[10.5px] font-semibold uppercase tracking-wider text-ink-mute">Time budget</p>
            <p className="text-[18px] font-bold text-ink leading-tight">
              {total ? `${total} min` : '—'}
              {fits != null && (
                <span className={`ml-2 inline-flex items-center text-[11px] font-medium px-2 py-0.5 rounded-full ${fits ? 'bg-success/10 text-success' : 'bg-danger/10 text-danger'}`}>
                  {fits ? 'Within budget ✓' : 'Over budget'}
                </span>
              )}
            </p>
          </div>
        </div>

        {total > 0 && (
          <div className="flex items-center gap-5">
            <div className="relative w-28 h-28 flex-shrink-0">
              <div className="absolute inset-0 rounded-full" style={{ background: conic }} />
              <div className="absolute inset-[12%] rounded-full bg-paper-elevated flex items-center justify-center">
                <span className="text-[14px] font-bold text-ink">{Math.round(total / 60 * 10) / 10} h</span>
              </div>
            </div>
            <div className="space-y-1.5 min-w-0 w-full">
              {segments.map(s => (
                <Legend key={s.label} icon={s.icon} label={s.label} min={s.min} color={s.color} total={total} />
              ))}
            </div>
          </div>
        )}

        {!total && (
          <p className="text-[12px] text-ink-faint">No time budget provided for this trip.</p>
        )}
      </div>
    </div>
  );
};

export default BudgetCard;