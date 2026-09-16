import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  MapPin, ArrowRight, Calendar, Users, IndianRupee, Clock,
  ChevronDown, Sparkles, Minus, Plus, Wand2,
} from 'lucide-react';
import { TRAVEL_STYLES, MEAL_OPTIONS } from '../data/travelOptions';
import { inr } from '../lib/format';

const STYLE_MODES = {
  relaxed: ['car', 'train', 'bus'],
  adventure: ['bike', 'car'],
  luxury: ['car', 'train'],
  budget: ['bus', 'bike'],
  food: null,
  culture: null,
  nature: null,
};

const DAYS = [1, 2, 3, 4, 5];

const Chip = ({ selected, onClick, children, className = '' }) => (
  <button
    type="button"
    onClick={onClick}
    aria-pressed={selected}
    className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[12.5px] font-medium transition-colors border ${
      selected
        ? 'bg-primary-soft border-primary/40 text-primary'
        : 'bg-paper-elevated border-paper-line text-ink-soft hover:border-ink-faint hover:text-ink'
    } ${className}`}
  >
    {children}
  </button>
);

const Field = ({ label, icon: Icon, children }) => (
  <label className="block">
    <span className="flex items-center gap-1.5 text-[10.5px] font-semibold uppercase tracking-wider text-ink-mute mb-1.5">
      {Icon && <Icon className="w-3 h-3" />} {label}
    </span>
    {children}
  </label>
);

const Stepper = ({ value, onChange, min = 1, max = 9, suffix }) => (
  <div className="flex items-center gap-1">
    <button
      type="button"
      onClick={() => onChange(Math.max(min, value - 1))}
      className="w-9 h-9 rounded-full bg-paper-inset text-ink-soft hover:text-ink hover:bg-paper-line transition-colors flex items-center justify-center"
      aria-label="Decrease"
    >
      <Minus className="w-4 h-4" />
    </button>
    <span className="w-20 text-center text-[13.5px] font-medium text-ink">
      {value} <span className="text-ink-mute text-[11px]">{suffix}</span>
    </span>
    <button
      type="button"
      onClick={() => onChange(Math.min(max, value + 1))}
      className="w-9 h-9 rounded-full bg-paper-inset text-ink-soft hover:text-ink hover:bg-paper-line transition-colors flex items-center justify-center"
      aria-label="Increase"
    >
      <Plus className="w-4 h-4" />
    </button>
  </div>
);

const TravelComposer = ({ onStart, isLoading, presetDestination, presetOrigin, presetDays }) => {
  const [destination, setDestination] = useState('');
  const [origin, setOrigin] = useState('');
  const [date, setDate] = useState('');
  const [travelers, setTravelers] = useState(2);
  const [budget, setBudget] = useState(100000);
  const [budgetOpen, setBudgetOpen] = useState(false);
  const [style, setStyle] = useState(null);
  const [meals, setMeals] = useState([]);
  const [days, setDays] = useState(1);
  const [dayPlans, setDayPlans] = useState({ 1: '' });
  const [describe, setDescribe] = useState(false);
  const [intentText, setIntentText] = useState('');

  useEffect(() => {
    if (presetDestination) setDestination(presetDestination);
  }, [presetDestination]);
  useEffect(() => {
    if (presetOrigin) setOrigin(presetOrigin);
  }, [presetOrigin]);
  useEffect(() => {
    const d = Number(presetDays);
    if (d >= 1 && d <= 5) setDays(d);
  }, [presetDays]);

  const toggleMeal = (id) =>
    setMeals(prev => prev.includes(id) ? prev.filter(m => m !== id) : [...prev, id]);

  const ready = Boolean(destination.trim() && origin.trim());

  const changeDays = (d) => {
    setDays(d);
    setDayPlans(prev => {
      const next = {};
      for (let i = 1; i <= d; i++) next[i] = prev[i] || '';
      return next;
    });
  };

  const setDayPlan = (day, value) => setDayPlans(prev => ({ ...prev, [day]: value }));

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!ready || isLoading) return;
    if (describe && intentText.trim()) {
      onStart(intentText.trim(), { preferences: { budget: Number(budget) || 0, days } });
      return;
    }
    const modes = style ? STYLE_MODES[style] : null;
    const filledDayPlans = Object.entries(dayPlans)
      .filter(([, v]) => (v || '').trim())
      .map(([d, v]) => `Day ${d}: ${v.trim()}`);
    const options = {
      origin: origin.trim(),
      destination: destination.trim(),
      travel_modes: modes,
      meal_types: meals.length ? [...meals] : null,
      time_budget_minutes: days * 8 * 60,
      preferences: {
        budget: Number(budget) || 0,
        travelers,
        date: date || null,
        style: style || 'balanced',
        days,
        day_plan: filledDayPlans.length ? Object.fromEntries(Object.entries(dayPlans).filter(([, v]) => (v || '').trim())) : null,
        notes: describe ? intentText.trim() : '',
      },
    };
    const mealPhrase = meals.length ? `, covering ${meals.join(', ')}` : '';
    const dayPhrase = days > 1 ? `across ${days} days` : 'within 1 day';
    const planPhrase = filledDayPlans.length ? ` Plan details: ${filledDayPlans.join('; ')}.` : '';
    const intent = `Plan a trip from ${origin.trim()} to ${destination.trim()}${mealPhrase} ${dayPhrase}.${planPhrase}`;
    onStart(intent, options);
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="glass rounded-[1.75rem] border border-paper-line shadow-composer p-4 sm:p-5 space-y-4"
      aria-label="Trip planner"
    >
      {/* Destinations */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <Field label="Destination" icon={MapPin}>
          <input
            value={destination}
            onChange={e => setDestination(e.target.value)}
            placeholder="Where do you want to go?"
            className="input bg-paper-elevated"
            autoComplete="off"
            aria-label="Destination"
          />
        </Field>
        <Field label="Starting from" icon={MapPin}>
          <input
            value={origin}
            onChange={e => setOrigin(e.target.value)}
            placeholder="Origin city or landmark"
            className="input bg-paper-elevated"
            autoComplete="off"
            aria-label="Origin"
          />
        </Field>
      </div>

      {/* Details row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <Field label="When" icon={Calendar}>
          <input
            type="date"
            value={date}
            onChange={e => setDate(e.target.value)}
            className="input bg-paper-elevated text-[13px]"
            aria-label="Trip date"
          />
        </Field>
        <Field label="Travelers" icon={Users}>
          <Stepper value={travelers} onChange={setTravelers} min={1} max={9} suffix="adults" />
        </Field>
        <Field label="Budget" icon={IndianRupee}>
          <div className="relative">
            <input
              type="text"
              inputMode="numeric"
              value={Number(budget) ? budget : ''}
              onChange={e => setBudget(Number(e.target.value.replace(/[^\d]/g, '')) || 0)}
              onFocus={() => setBudgetOpen(true)}
              onBlur={() => setBudgetOpen(false)}
              placeholder="Target budget"
              className="input bg-paper-elevated pr-3"
              aria-label="Budget in rupees"
            />
            {budgetOpen && !Number(budget) && (
              <div className="absolute inset-x-0 top-full mt-1.5 z-20">
                <div className="flex gap-1.5 flex-wrap p-2 rounded-xl bg-paper-elevated border border-paper-line shadow-elevated">
                  {[50000, 100000, 200000, 500000].map(v => (
                    <button
                      key={v}
                      type="button"
                      onMouseDown={e => { e.preventDefault(); setBudget(v); }}
                      className="px-2 py-1 rounded-lg bg-paper-inset text-[11px] font-medium text-ink-soft hover:text-ink transition-colors"
                    >
                      {inr(v)}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </Field>
        <Field label="Duration (days)" icon={Clock}>
          <div className="flex gap-1.5 flex-wrap pt-0.5">
            {DAYS.map(d => (
              <Chip key={d} selected={days === d} onClick={() => changeDays(d)}>
                {d} {d === 1 ? 'day' : 'days'}
              </Chip>
            ))}
          </div>
        </Field>
      </div>

      {/* Plan each day */}
      <div>
        <p className="flex items-center gap-1.5 text-[10.5px] font-semibold uppercase tracking-wider text-ink-mute mb-1.5">
          <Sparkles className="w-3 h-3" /> Plan your {days} day{days > 1 ? 's' : ''}
        </p>
        <div className={`grid gap-1.5 ${days > 1 ? 'sm:grid-cols-2' : 'grid-cols-1'}`}>
          {Array.from({ length: days }, (_, i) => i + 1).map(d => (
            <input
              key={d}
              value={dayPlans[d] || ''}
              onChange={e => setDayPlan(d, e.target.value)}
              placeholder={`Day ${d} — e.g. Old town in the morning, lakeside dinner`}
              maxLength={200}
              className="input bg-paper-elevated text-[12.5px]"
              aria-label={`Plan for day ${d}`}
            />
          ))}
        </div>
      </div>

      {/* Style + meals */}
      <div className="space-y-2.5">
        <div className="flex flex-wrap gap-1.5">
          {TRAVEL_STYLES.map(s => (
            <Chip key={s.id} selected={style === s.id} onClick={() => setStyle(style === s.id ? null : s.id)} title={s.hint}>
              {s.label}
            </Chip>
          ))}
        </div>
        <div className="flex flex-wrap gap-1.5">
          <span className="inline-flex items-center gap-1.5 text-[10.5px] font-semibold uppercase tracking-wider text-ink-mute pr-1">
            <Sparkles className="w-3 h-3" /> Meals
          </span>
          {MEAL_OPTIONS.map(m => (
            <Chip key={m.id} selected={meals.includes(m.id)} onClick={() => toggleMeal(m.id)} title={m.hint}>
              {m.label}
            </Chip>
          ))}
        </div>
      </div>

      {/* Describe instead */}
      <div>
        <button
          type="button"
          onClick={() => setDescribe(d => !d)}
          className="inline-flex items-center gap-1.5 text-[12px] font-medium text-primary hover:text-primary-deep transition-colors"
          aria-expanded={describe}
        >
          <Wand2 className="w-3.5 h-3.5" />
          {describe ? 'Hide description' : 'or describe the trip in your own words'}
          <ChevronDown className={`w-3.5 h-3.5 transition-transform ${describe ? 'rotate-180' : ''}`} />
        </button>
        <AnimatePresence initial={false}>
          {describe && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.25 }}
              className="overflow-hidden"
            >
              <textarea
                value={intentText}
                onChange={e => setIntentText(e.target.value)}
                placeholder="e.g. From Kolkata to Darjeeling by train, tiffin + lunch along the way, cover a viewpoint, within 8 hours"
                rows={2}
                maxLength={1600}
                className="input mt-2 text-[13.5px]"
                aria-label="Describe your trip"
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* CTA */}
      <div className="pt-1">
        <motion.button
          whileTap={{ scale: ready ? 0.985 : 1 }}
          type="submit"
          disabled={!ready || isLoading}
          className="w-full py-3 rounded-2xl bg-primary text-white font-semibold text-[15px] flex items-center justify-center gap-2
                     disabled:opacity-40 disabled:cursor-not-allowed transition-colors hover:bg-primary-deep shadow-sm"
        >
          {isLoading ? (
            <>
              <span className="w-4 h-4 border-2 border-white/60 border-t-white rounded-full animate-spin" />
              Planning…
            </>
          ) : (
            <>
              Plan my trip
              <ArrowRight className="w-4.5 h-4.5" />
            </>
          )}
        </motion.button>
        <p className="text-center text-[11px] text-ink-faint mt-2">
          A team of AI agents compares routes, finds restaurants &amp; places, and builds your {days}-day itinerary
          {style && STYLE_MODES[style] && ` — comparing ${STYLE_MODES[style].join(', ')}`}.
        </p>
      </div>
    </form>
  );
};

export default TravelComposer;