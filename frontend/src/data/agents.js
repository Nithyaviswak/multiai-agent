import {
  Map as MapIcon, Car, Bus, TrainFront, Bike, Scale, Globe2,
  UtensilsCrossed, Landmark, CalendarClock, ClipboardCheck, XCircle,
} from 'lucide-react';

/**
 * The AI travel team displayed during planning and in the trip recap.
 * `id` maps 1:1 to the backend workflow step names so statuses are driven by
 * the live `current_step` returned from GET /api/travel/{id}.
 */
export const AGENTS = [
  { id: 'plan', name: 'Trip Planner', role: 'Lead coordinator', task: 'Parsing your route, budget and preferences', icon: MapIcon },
  { id: 'route_car', name: 'Car Navigator', role: 'Route agent', task: 'Fetching the driving route and travel time', icon: Car },
  { id: 'route_bus', name: 'Bus Navigator', role: 'Route agent', task: 'Checking bus routes and schedules', icon: Bus },
  { id: 'route_train', name: 'Train Navigator', role: 'Route agent', task: 'Checking rail connections', icon: TrainFront },
  { id: 'route_bike', name: 'Bike Navigator', role: 'Route agent', task: 'Checking cycling routes', icon: Bike },
  { id: 'route_compare', name: 'Route Analyst', role: 'Evaluator', task: 'Comparing travel time across every mode', icon: Scale },
  { id: 'gather_knowledge', name: 'Destination Researcher', role: 'Researcher', task: 'Gathering practical tips for the trip', icon: Globe2 },
  { id: 'find_restaurants', name: 'Restaurant Scout', role: 'Researcher', task: 'Finding spots for every meal', icon: UtensilsCrossed },
  { id: 'find_places', name: 'Places Curator', role: 'Researcher', task: 'Shortlisting places that fit the time', icon: Landmark },
  { id: 'build_itinerary', name: 'Itinerary Optimizer', role: 'Optimizer', task: 'Sequencing the day into a timeline', icon: CalendarClock },
  { id: 'generate_report', name: 'Travel Reviewer', role: 'Reviewer', task: 'Reviewing the plan and writing your report', icon: ClipboardCheck },
];

export const stepName = (id) => AGENTS.find(a => a.id === id)?.name || id;

export const stepIndex = (id) => {
  const i = AGENTS.findIndex(a => a.id === id);
  return i === -1 ? 0 : i;
};

export const STATUS_META = {
  waiting: { label: 'Waiting', dot: 'bg-ink-faint', text: 'text-ink-mute', pulse: false },
  working: { label: 'Working', dot: 'bg-primary', text: 'text-primary', pulse: true },
  complete: { label: 'Complete', dot: 'bg-success', text: 'text-success', pulse: false },
  attention: { label: 'Needs attention', dot: 'bg-warning', text: 'text-warning', pulse: false },
};

export const ERROR_ICON = XCircle;