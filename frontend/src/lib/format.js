export const inr = (n) => {
  if (n === null || n === undefined || isNaN(n)) return '₹—';
  return '₹' + Number(n).toLocaleString('en-IN');
};

export const fmtMin = (min) => {
  const m = Number(min) || 0;
  if (m <= 0) return '—';
  const h = Math.floor(m / 60);
  const rem = m % 60;
  if (h && rem) return `${h} h ${rem} min`;
  if (h) return `${h} h`;
  return `${rem} min`;
};

export const fmtKm = (km) => {
  if (km === null || km === undefined || isNaN(km)) return '—';
  return `${Number(km).toFixed(Number(km) < 10 ? 1 : 0)} km`;
};

export const fmtDate = (iso) => {
  if (!iso) return '';
  try {
    const d = new Date(iso + (iso.length === 10 ? 'T00:00:00' : ''));
    return d.toLocaleDateString('en-IN', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' });
  } catch {
    return iso;
  }
};

export const capitalize = (s = '') => s.charAt(0).toUpperCase() + s.slice(1);

export const uid = () =>
  'id-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 7);

export const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));