import { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { Globe2, CalendarDays, MapPinned, Wallet, UtensilsCrossed, Landmark } from 'lucide-react';
import TripHeader from './TripHeader';
import TripSummary from './TripSummary';
import TransportCompare from './TransportCompare';
import ItineraryTimeline from './ItineraryTimeline';
import MapPanel from './MapPanel';
import BudgetCard from './BudgetCard';
import RestaurantList from './RestaurantList';
import TeamRecap from './TeamRecap';
import RefineComposer from './RefineComposer';
import { fmtKm, fmtMin } from '../lib/format';

const PanelTitle = ({ icon: Icon, children, action }) => (
  <div className="flex items-center justify-between mb-3">
    <p className="text-[10.5px] font-semibold uppercase tracking-wider text-ink-mute flex items-center gap-1.5">
      <Icon className="w-3.5 h-3.5 text-secondary" /> {children}
    </p>
    {action}
  </div>
);

const TripView = ({
  data, currentStep, failedSteps = [], isSaved,
  onSave, onRefine, onEdit, isLoading, iteration,
}) => {
  const itinerary = data.itinerary_data || {};
  const knowledge = data.knowledge_data || {};
  const tripDays = data.plan_data?.preferences?.days || 1;

  const [stops, setStops] = useState([]);
  useEffect(() => {
    setStops(itinerary.stops || []);
  }, [data?.workflow_id]);

  const details = useMemo(() => {
    const plan = data.plan_data || {};
    const route = data.route_data || {};
    const restaurants = data.restaurants_data || {};
    const places = data.places_data || {};
    const map = {};
    if (plan.origin && plan.destination) map.plan = `Parsed ${plan.origin} → ${plan.destination}`;
    (route.modes || []).forEach(m => {
      map[`route_${m.mode}`] = `${m.mode} leg · ${fmtMin(m.duration_min)} over ${fmtKm(m.distance_km)}`;
    });
    if (route.modes?.length) map.route_compare = `Compared ${route.modes.length} transport options`;
    map.gather_knowledge = `${(knowledge.facts || []).length} local tips`;
    map.find_restaurants = `Found ${restaurants.total || 0} restaurants`;
    map.find_places = `${places.count || 0} places within budget`;
    map.build_itinerary = `${itinerary.stops?.length || 0} stops timed from ${itinerary.start_time || 'start'}`;
    map.generate_report = 'Final report ready';
    return map;
  }, [data, itinerary.stops, itinerary.start_time]);

  const hasRestaurants = (data.restaurants_data?.total || 0) > 0;
  const hasPlaces = (data.places_data?.places || []).length > 0;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0, y: -12 }}
      className="space-y-6"
    >
      <TripHeader
        data={data}
        isSaved={isSaved}
        onSave={onSave}
        onEdit={onEdit}
        onRegenerate={() => onRefine('Try a fresh variation of this trip, keeping the same origin and destination.')}
        iteration={iteration}
      />

      <div className="grid grid-cols-1 lg:grid-cols-[280px_minmax(0,1fr)_340px] gap-5 items-start">
        {/* Left — overview (below itinerary on mobile) */}
        <div className="order-2 lg:order-1 space-y-4">
          <TripSummary data={data} />

          <div className="rounded-2xl border border-paper-line bg-paper-elevated p-4">
            <PanelTitle icon={Globe2}>Transport comparison</PanelTitle>
            <TransportCompare route={data.route_data} />
          </div>
        </div>

        {/* Center — the day itinerary */}
        <div className="order-1 lg:order-2 min-w-0">
          <div className="rounded-2xl border border-paper-line bg-paper-elevated p-4 sm:p-5">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <div className="w-9 h-9 rounded-xl bg-secondary-soft flex items-center justify-center">
                  <CalendarDays className="w-[18px] h-[18px] text-secondary" />
                </div>
                <div>
                  <p className="text-[15px] font-semibold text-ink">{tripDays > 1 ? 'Itinerary' : 'Day itinerary'}</p>
                  <p className="text-[11px] text-ink-mute">
                    {itinerary.start_time ? `${itinerary.start_time} → ${itinerary.end_time || 'evening'}` : 'Timed plan'} · reorder or edit stops anytime
                  </p>
                </div>
              </div>
            </div>

            {stops.length ? (
              <ItineraryTimeline stops={stops} onStopsChange={setStops} />
            ) : (
              <div className="rounded-xl border border-dashed border-paper-line p-6 text-center">
                <p className="text-[12.5px] text-ink-mute">No itinerary stops were returned for this trip.</p>
              </div>
            )}
          </div>

          <div id="refine-composer" className="mt-5 scroll-mt-24">
            <RefineComposer
              onRefine={onRefine}
              onRegenerate={() => onRefine('Try a fresh variation of this trip, keeping the same origin and destination.')}
              isLoading={isLoading}
              iteration={iteration}
            />
          </div>
        </div>

        {/* Right — map, budget, restaurants, team (below itinerary on mobile) */}
        <div className="order-3 space-y-4">
          <div className="rounded-2xl border border-paper-line bg-paper-elevated p-4">
            <PanelTitle icon={MapPinned}>Route map</PanelTitle>
            <MapPanel
              route={data.route_data}
              places={data.places_data}
              restaurants={data.restaurants_data}
              itinerary={data.itinerary_data}
            />
          </div>

          <div className="rounded-2xl border border-paper-line bg-paper-elevated p-4">
            <PanelTitle icon={Wallet}>Budget</PanelTitle>
            <BudgetCard
              itinerary={data.itinerary_data}
              route={data.route_data}
              preferences={data.plan_data?.preferences || {}}
            />
          </div>

          {hasRestaurants && (
            <div className="rounded-2xl border border-paper-line bg-paper-elevated p-4">
              <PanelTitle icon={UtensilsCrossed}>Restaurants</PanelTitle>
              <RestaurantList restaurants={data.restaurants_data} />
            </div>
          )}

          {hasPlaces && (
            <div className="rounded-2xl border border-paper-line bg-paper-elevated p-4">
              <PanelTitle icon={Landmark}>Places considered</PanelTitle>
              <ul className="space-y-1.5">
                {data.places_data.places.slice(0, 6).map(p => (
                  <li key={p.place_id || p.name} className="flex items-center justify-between gap-2 text-[12px]">
                    <span className="text-ink-soft truncate">{p.name}</span>
                    <span className="text-[10.5px] text-ink-faint flex-shrink-0">{p.visit_minutes} min</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="rounded-2xl border border-paper-line bg-paper-elevated p-4">
            <TeamRecap currentStep={currentStep} failedSteps={failedSteps} details={details} />
          </div>

          {(knowledge.facts || []).length > 0 && (
            <div className="rounded-2xl border border-paper-line bg-paper-elevated p-4">
              <PanelTitle icon={Globe2}>Researcher notes</PanelTitle>
              <ul className="space-y-2">
                {knowledge.facts.slice(0, 6).map((f, i) => (
                  <li key={i} className="text-[12px] text-ink-soft leading-relaxed flex gap-2">
                    <span className="text-secondary mt-0.5">·</span> {f}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
};

export default TripView;