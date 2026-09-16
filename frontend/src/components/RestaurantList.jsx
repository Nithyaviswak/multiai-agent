import { UtensilsCrossed, Star, MapPin, Mail } from 'lucide-react';
import { fmtKm } from '../lib/format';

const RestaurantList = ({ restaurants }) => {
  const meals = restaurants?.meals || {};
  const entries = Object.entries(meals).filter(([, list]) => (list || []).length > 0);
  const total = restaurants?.total ?? entries.reduce((n, [, l]) => n + l.length, 0);

  if (!entries.length) {
    return (
      <div className="rounded-2xl border border-dashed border-paper-line bg-paper-inset/40 p-5 text-center">
        <UtensilsCrossed className="w-5 h-5 mx-auto text-ink-mute mb-2" />
        <p className="text-[12.5px] text-ink-mute">No restaurants found near the route.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {entries.map(([meal, list]) => (
        <div key={meal}>
          <p className="text-[10.5px] font-semibold uppercase tracking-wider text-ink-mute mb-1.5 flex items-center gap-1.5 capitalize">
            <Mail className="w-3 h-3 text-secondary" /> {meal}
            <span className="text-ink-faint font-normal">({list.length})</span>
          </p>
          <ul className="space-y-1.5">
            {list.map(r => (
              <li key={r.place_id || r.name} className="rounded-xl border border-paper-line bg-paper-elevated p-3">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-[13px] font-semibold text-ink truncate">{r.name}</p>
                  <span className="text-[11px] text-ink-faint flex-shrink-0">{fmtKm(r.distance_km)}</span>
                </div>
                <div className="flex items-center gap-2.5 mt-1 text-[11px] text-ink-soft">
                  {r.rating != null && (
                    <span className="inline-flex items-center gap-1 text-warning font-medium">
                      <Star className="w-3 h-3 fill-current" /> {r.rating}
                    </span>
                  )}
                  {r.user_ratings_total ? <span className="text-ink-faint">({r.user_ratings_total})</span> : null}
                </div>
                {r.vicinity && (
                  <p className="flex items-start gap-1 text-[11px] text-ink-mute mt-1">
                    <MapPin className="w-3 h-3 mt-0.5 flex-shrink-0" /> {r.vicinity}
                  </p>
                )}
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
};

export default RestaurantList;