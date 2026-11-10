import { useState } from 'react';
import { motion } from 'framer-motion';
import { Sparkles, MapPin, UtensilsCrossed, Landmark, CalendarClock, ArrowRight } from 'lucide-react';
import TravelComposer from '../components/TravelComposer';
import DestinationsRail from '../components/DestinationsRail';
import { PROMPT_EXAMPLES } from '../data/travelOptions';

const parseExample = ([routePart, blurb = '']) => {
  const [dest, orig] = routePart.split('→').map(s => s.trim());
  const h = blurb.match(/(\d+)\s*hours?/);
  const days = h ? Math.max(1, Math.min(5, Math.ceil(Number(h[1]) / 8))) : null;
  return { destination: dest || '', origin: orig || '', days };
};

const STEPS = [
  { icon: MapPin, title: 'Tell us the plan', copy: 'Origin, destination, style and budget — in words or fields.' },
  { icon: Sparkles, title: 'Agents compare routes', copy: 'A team checks car, bus, train and bike options and picks the best.' },
  { icon: UtensilsCrossed, title: 'Meals & places', copy: 'Restaurant scouts and a places curator fit stops to your time.' },
  { icon: CalendarClock, title: 'Timed itinerary', copy: 'One optimizer sequences everything into a minute-by-minute day.' },
];

const ExplorePage = ({ onStart, isLoading }) => {
  const [example, setExample] = useState(null);

  const pickExample = (ex) => {
    const p = parseExample(ex);
    setExample(p);
    document.getElementById('composer-card')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  const pickDestination = (d) => {
    setExample(prev => ({ ...(prev || {}), destination: d.city }));
    document.getElementById('composer-card')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.35 }}
    >
      {/* Hero */}
      <section className="relative text-center pt-10 sm:pt-20 pb-4 overflow-hidden">
        {/* animated aurora blobs behind the headline */}
        <div className="hero-blob w-[340px] h-[340px] bg-primary -top-20 -left-40" style={{ animationDelay: '0s' }} />
        <div className="hero-blob w-[280px] h-[280px] bg-secondary top-8 -right-24" style={{ animationDelay: '-3s', animationDuration: '11s' }} />
        <div className="hero-blob w-[220px] h-[220px] bg-[#7C3AED] bottom-0 left-1/3" style={{ animationDelay: '-6s', animationDuration: '13s' }} />

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, ease: "easeOut" }}
          className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-primary-soft text-primary text-[12.5px] font-medium mb-5 relative"
        >
          <Sparkles className="w-3.5 h-3.5" /> Eleven specialists, one itinerary
        </motion.div>
        <h1 className="font-serif text-[40px] sm:text-[58px] leading-[1.04] tracking-tight text-balance max-w-3xl mx-auto relative">
          Plan a trip you'll <em className="gradient-text not-italic">actually</em> want to take
        </h1>
        <p className="text-[14.5px] text-ink-soft mt-4 max-w-xl mx-auto leading-relaxed relative">
          Describe a day — from your doorstep to a viewpoint — and a team of AI agents
          compares real routes, books nothing, and hands you a timed plan you can refine.
        </p>
      </section>

      {/* Composer */}
      <div id="composer-card" className="max-w-3xl mx-auto scroll-mt-24 glass-hero gradient-border">
        <TravelComposer
          onStart={onStart}
          isLoading={isLoading}
          presetDestination={example?.destination}
          presetOrigin={example?.origin}
          presetDays={example?.days}
        />
      </div>

      {/* Prompt examples */}
      <div className="max-w-3xl mx-auto mt-6">
        <p className="text-[11px] font-semibold uppercase tracking-wider text-ink-mute mb-2.5">Try one of these</p>
        <div className="flex flex-wrap gap-2">
          {PROMPT_EXAMPLES.map(ex => {
            const p = parseExample(ex);
            const active = example && example.destination === p.destination && example.origin === p.origin;
            return (
              <button
                key={ex}
                onClick={() => pickExample(ex)}
                className={`group hover-lift px-3 py-2 rounded-xl border text-left transition-all ${
                  active
                    ? 'bg-gradient-to-r from-primary-soft via-[#F5F3FF] to-secondary-soft border-primary/40 shadow-sm'
                    : 'bg-paper-elevated border-paper-line hover:border-ink-faint hover:shadow-sm'
                }`}
              >
                <span className="block text-[12.5px] font-semibold text-ink">{p.destination} <ArrowRight className="w-3 h-3 inline text-primary -mt-0.5" /> {p.origin}</span>
                <span className="block text-[10.5px] text-ink-mute mt-0.5">{ex[1]}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Destinations rail */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <DestinationsRail onPick={pickDestination} disabled={isLoading} />
      </div>

      {/* How it works */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6 mt-14 pb-10">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {STEPS.map((s, i) => (
            <motion.div
              key={s.title}
              initial={{ opacity: 0, y: 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-40px' }}
              transition={{ delay: i * 0.06, duration: 0.4, ease: "easeOut" }}
              className="hover-lift rounded-2xl border border-paper-line bg-paper-elevated p-4 sm:p-5"
            >
              <div className="w-10 h-10 rounded-xl bg-secondary-soft flex items-center justify-center mb-3">
                <s.icon className="w-5 h-5 text-secondary" />
              </div>
              <p className="text-[10px] font-semibold uppercase tracking-wider text-ink-faint mb-1">Step {i + 1}</p>
              <p className="text-[13.5px] font-semibold text-ink">{s.title}</p>
              <p className="text-[12px] text-ink-soft mt-1 leading-relaxed">{s.copy}</p>
            </motion.div>
          ))}
        </div>
      </section>
    </motion.div>
  );
};

export default ExplorePage;