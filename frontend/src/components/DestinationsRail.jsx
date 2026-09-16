import { motion } from 'framer-motion';
import { ArrowUpRight } from 'lucide-react';
import { useState } from 'react';
import { DESTINATIONS } from '../data/travelOptions';

const DestinationsRail = ({ onPick, disabled }) => {
  const [picked, setPicked] = useState(null);

  return (
    <div className="mt-10">
      <div className="flex items-end justify-between mb-3">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-wider text-ink-mute">Popular for a day trip</p>
          <p className="text-[13px] text-ink-soft mt-0.5">Pick a destination and tell us where you start from.</p>
        </div>
        <span className="hidden sm:block text-[11px] text-ink-faint">Tap to choose</span>
      </div>

      <div className="flex gap-3 overflow-x-auto pb-2 -mx-4 px-4 sm:mx-0 sm:px-0 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
        {DESTINATIONS.map((d, i) => {
          const active = picked === d.city;
          return (
            <motion.button
              key={d.city}
              initial={{ opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.08 + i * 0.05 }}
              whileTap={{ scale: 0.97 }}
              onClick={() => {
                if (disabled) return;
                setPicked(d.city);
                onPick?.(d);
              }}
              className={`group relative w-40 sm:w-48 shrink-0 rounded-2xl overflow-hidden text-left
                border transition-all ${active
                  ? 'ring-2 ring-primary border-transparent'
                  : 'border-paper-line hover:border-ink-faint'}`}
              aria-pressed={active}
            >
              <div className="relative h-44 sm:h-48 w-full overflow-hidden bg-paper-inset">
                <img
                  src={d.img}
                  alt={`${d.city}, ${d.country}`}
                  loading="lazy"
                  className="absolute inset-0 w-full h-full object-cover transition-transform duration-500 group-hover:scale-[1.04]"
                  onError={e => { e.currentTarget.style.visibility = 'hidden'; }}
                />
                <div className={`absolute inset-0 bg-gradient-to-t ${d.grad} opacity-60`} />
                <div className="absolute bottom-0 inset-x-0 p-3">
                  <p className="font-serif text-[19px] leading-none text-white">{d.city}</p>
                  <p className="text-[11px] text-white/80 mt-1">{d.country} · {d.city === picked ? 'Selected' : d.note}</p>
                </div>
                <span className="absolute top-2.5 right-2.5 w-7 h-7 rounded-full bg-white/25 backdrop-blur flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                  <ArrowUpRight className="w-3.5 h-3.5 text-white" />
                </span>
              </div>
            </motion.button>
          );
        })}
      </div>
    </div>
  );
};

export default DestinationsRail;