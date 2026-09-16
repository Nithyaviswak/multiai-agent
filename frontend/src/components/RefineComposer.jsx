import { useState } from 'react';
import { motion } from 'framer-motion';
import { Wand2, ArrowRight, Sparkles } from 'lucide-react';
import { REFINE_SUGGESTIONS } from '../data/travelOptions';

const RefineComposer = ({ onRefine, onRegenerate, isLoading, iteration = 0 }) => {
  const [text, setText] = useState('');
  const [activeChip, setActiveChip] = useState(null);

  const submit = (value) => {
    const v = (value ?? text).trim();
    if (!v || isLoading) return;
    onRefine(v);
    setText('');
    setActiveChip(null);
  };

  return (
    <div className="card p-4 sm:p-5">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-primary-soft flex items-center justify-center">
            <Wand2 className="w-4 h-4 text-primary" />
          </div>
          <div>
            <p className="text-[13.5px] font-semibold text-ink">Refine this trip</p>
            <p className="text-[11px] text-ink-mute">
              {iteration > 0 ? `Trip v${iteration + 1} — this will replan without starting over.` : 'Tell the team what to change.'}
            </p>
          </div>
        </div>
        <button
          onClick={onRegenerate}
          disabled={isLoading}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-paper-inset text-[11.5px] font-medium text-ink-soft hover:text-ink transition-colors disabled:opacity-40"
          title="Plan a fresh variation of the same trip"
        >
          <Sparkles className="w-3.5 h-3.5 text-secondary" /> Regenerate
        </button>
      </div>

      <div className="flex flex-wrap gap-1.5 mb-3">
        {REFINE_SUGGESTIONS.map(s => (
          <button
            key={s}
            onClick={() => { if (!isLoading) { setActiveChip(s); submit(s); } }}
            className={`px-3 py-1.5 rounded-full text-[11.5px] font-medium border transition-colors ${
              activeChip === s
                ? 'bg-primary-soft border-primary/40 text-primary'
                : 'bg-paper-elevated border-paper-line text-ink-soft hover:border-ink-faint hover:text-ink'
            } ${isLoading ? 'opacity-50' : ''}`}
          >
            {s}
          </button>
        ))}
      </div>

      <form
        onSubmit={e => { e.preventDefault(); submit(); }}
        className="flex gap-2"
      >
        <input
          value={text}
          onChange={e => setText(e.target.value)}
          placeholder="Change something about your trip…"
          maxLength={800}
          disabled={isLoading}
          className="input bg-paper-elevated text-[13.5px]"
          aria-label="Refinement request"
        />
        <motion.button
          whileTap={{ scale: 0.96 }}
          type="submit"
          disabled={!text.trim() || isLoading}
          aria-label="Apply refinement"
          className="w-11 h-11 rounded-xl bg-primary text-white flex items-center justify-center disabled:opacity-40 disabled:cursor-not-allowed transition-colors hover:bg-primary-deep flex-shrink-0"
        >
          <ArrowRight className="w-5 h-5" />
        </motion.button>
      </form>
    </div>
  );
};

export default RefineComposer;