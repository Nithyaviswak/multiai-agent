import { useCallback, useEffect, useState } from 'react';
import { uid } from '../lib/format';

const KEY = 'multiai.savedTrips';

const load = () => {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
};

const persist = (trips) => {
  try { localStorage.setItem(KEY, JSON.stringify(trips)); } catch {}
};

export const useSavedTrips = () => {
  const [trips, setTrips] = useState(load);

  useEffect(() => { persist(trips); }, [trips]);

  const saveTrip = useCallback((trip) => {
    setTrips(prev => {
      const next = [{ id: uid(), savedAt: new Date().toISOString(), ...trip }, ...prev];
      return next.slice(0, 50);
    });
  }, []);

  const removeTrip = useCallback((id) => {
    setTrips(prev => prev.filter(t => t.id !== id));
  }, []);

  const isSaved = useCallback((workflowId) => {
    return trips.some(t => t.workflowId === workflowId);
  }, [trips]);

  return { trips, saveTrip, removeTrip, isSaved };
};