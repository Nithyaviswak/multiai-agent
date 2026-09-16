import { Compass } from 'lucide-react';

const Logo = ({ compact = false }) => (
  <div className="flex items-center gap-2.5 select-none">
    <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary to-secondary flex items-center justify-center shadow-sm">
      <Compass className="w-5 h-5 text-white" strokeWidth={2.2} />
    </div>
    {!compact && (
      <div className="leading-none">
        <p className="font-serif text-[17px] tracking-tight text-ink">Multi&nbsp;AI&nbsp;Agent</p>
        <p className="text-[10px] text-ink-mute mt-1">Your AI travel team</p>
      </div>
    )}
  </div>
);

export default Logo;