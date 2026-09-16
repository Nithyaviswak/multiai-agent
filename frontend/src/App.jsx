import { useEffect, useState } from 'react';
import { AnimatePresence } from 'framer-motion';
import { Toaster } from 'react-hot-toast';
import toast from 'react-hot-toast';
import { AlertTriangle, ArrowLeft, RefreshCw } from 'lucide-react';
import './styles/globals.css';
import Header from './components/Header';
import BottomNav from './components/BottomNav';
import SettingsPanel from './components/SettingsPanel';
import ExplorePage from './pages/ExplorePage';
import TripsPage from './pages/TripsPage';
import ProfilePage from './pages/ProfilePage';
import PlanningView from './components/PlanningView';
import TripView from './components/TripView';
import { useTravelPlanner } from './hooks/useResearch';
import { useSavedTrips } from './hooks/useSavedTrips';
import { useTheme } from './hooks/useTheme';
import { travelAPI } from './services/api';

const ErrorScreen = ({ message, onRetry, onBack }) => (
  <div className="max-w-lg mx-auto px-4 pt-16 pb-10">
    <div className="card p-6 sm:p-8 text-center">
      <div className="w-12 h-12 mx-auto rounded-2xl bg-danger/12 flex items-center justify-center mb-4">
        <AlertTriangle className="w-6 h-6 text-danger" />
      </div>
      <h2 className="font-serif text-[26px] text-ink">This trip didn't come together</h2>
      <p className="text-[13.5px] text-ink-soft mt-2 leading-relaxed">{message}</p>
      <div className="flex items-center justify-center gap-2 mt-6">
        <button onClick={onRetry} className="btn btn-primary">
          <RefreshCw className="w-4 h-4" /> Retry
        </button>
        <button onClick={onBack} className="btn btn-ghost">
          <ArrowLeft className="w-4 h-4" /> Back
        </button>
      </div>
    </div>
  </div>
);

function App() {
  const { phase, data, error, workflowId, currentStep, iterations, startWorkflow, refine, resetWorkflow } = useTravelPlanner();
  const { trips, saveTrip, removeTrip, isSaved } = useSavedTrips();
  const { theme, toggle: toggleTheme } = useTheme();

  const [view, setView] = useState('explore'); // explore | trips | profile
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [savedOpen, setSavedOpen] = useState(null); // snapshot rehydrated from My Trips
  const [currentModel, setCurrentModel] = useState(null);

  const loadCurrentModel = () => {
    travelAPI.getCurrentModel().then(r => {
      if (r.success) setCurrentModel(r.model || null);
    }).catch(() => {});
  };
  useEffect(() => { loadCurrentModel(); }, []);

  const navigate = (next) => {
    setView(next);
    setSavedOpen(null);
    window.scrollTo({ top: 0 });
  };

  const handlePlan = () => navigate('explore');

  const activeWorkflowId = savedOpen?.workflow_id || workflowId;
  const savedId = activeWorkflowId && trips.find(t => t.workflowId === activeWorkflowId)?.id;
  const savedStatus = savedId ? true : false;

  const toggleSave = () => {
    if (!activeWorkflowId) return;
    if (savedId) {
      removeTrip(savedId);
      toast.success('Removed from My Trips');
    } else {
      const snapshot = savedOpen || data;
      const plan = snapshot?.plan_data || {};
      saveTrip({
        workflowId: activeWorkflowId,
        origin: plan.origin || snapshot?.origin || 'Origin',
        destination: plan.destination || snapshot?.destination || 'Destination',
        data: snapshot,
      });
      toast.success('Saved to My Trips');
    }
  };

  const openSaved = (t) => {
    setView('trips');
    setSavedOpen(t.data || null);
    window.scrollTo({ top: 0 });
  };

  const handleRefine = (text) => {
    setSavedOpen(null);
    refine(text);
    window.scrollTo({ top: 0 });
  };

  const handleEdit = () => {
    document.getElementById('refine-composer')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  };

  const tripData = savedOpen || (phase === 'complete' ? data : null);
  const failedSteps = data?.errors || (error && !data ? ['generate_report'] : []);

  return (
    <div className="min-h-screen bg-paper text-ink flex flex-col">
      <Toaster
        position="top-center"
        toastOptions={{
          style: {
            background: 'var(--color-paper-elevated)',
            color: 'var(--color-ink)',
            border: '1px solid var(--color-paper-line)',
            borderRadius: '1rem',
            fontFamily: 'var(--font-sans)',
            fontSize: '13px',
          },
        }}
      />

      <Header
        view={view}
        onNavigate={navigate}
        theme={theme}
        onToggleTheme={toggleTheme}
        onOpenSettings={() => setSettingsOpen(true)}
        currentModel={currentModel}
      />

      <main className="flex-1 w-full max-w-6xl mx-auto px-0 sm:px-6 pb-24 md:pb-10">
        <AnimatePresence mode="wait">
          {phase === 'planning' && (
            <PlanningView
              key="planning"
              request={{ origin: data?.plan_data?.origin, destination: data?.plan_data?.destination }}
              currentStep={currentStep}
              failedSteps={failedSteps}
              onStop={resetWorkflow}
            />
          )}

          {phase === 'error' && !tripData && (
            <ErrorScreen
              key="error"
              message={error || 'Something went wrong while planning your trip.'}
              onRetry={resetWorkflow}
              onBack={() => navigate('explore')}
            />
          )}

          {view === 'explore' && phase !== 'planning' && phase !== 'error' && tripData && (
            <TripView
              key={savedOpen ? `saved-${savedOpen.workflow_id}` : `trip-${data.workflow_id}-${iterations}`}
              data={tripData}
              currentStep={tripData.current_step || 'complete'}
              failedSteps={failedSteps}
              isSaved={savedStatus}
              onSave={toggleSave}
              onRefine={handleRefine}
              onEdit={handleEdit}
              isLoading={false}
              iteration={iterations}
            />
          )}

          {view === 'explore' && phase === 'idle' && !tripData && (
            <ExplorePage
              key="explore"
              onStart={(intent, opts) => { setSavedOpen(null); startWorkflow(intent, opts); }}
              isLoading={false}
            />
          )}

          {view === 'trips' && phase === 'idle' && (
            <TripsPage key="trips" trips={trips} onOpen={openSaved} onRemove={removeTrip} onNavigate={navigate} />
          )}

          {view === 'profile' && phase === 'idle' && (
            <ProfilePage
              key="profile"
              currentModel={currentModel}
              onOpenSettings={() => setSettingsOpen(true)}
              theme={theme}
              onToggleTheme={toggleTheme}
              workflowId={activeWorkflowId}
            />
          )}
        </AnimatePresence>
      </main>

      {savedOpen && (
        <button
          onClick={() => { setSavedOpen(null); setView('trips'); }}
          className="fixed bottom-24 md:bottom-6 right-4 z-30 inline-flex items-center gap-1.5 px-3.5 py-2 rounded-full glass border border-paper-line text-[12.5px] font-medium text-ink-soft hover:text-ink transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to trips
        </button>
      )}

      <BottomNav view={view} onNavigate={navigate} onPlan={handlePlan} onSettings={() => setView('profile')} />

      <SettingsPanel open={settingsOpen} onClose={() => setSettingsOpen(false)} onChanged={loadCurrentModel} />
    </div>
  );
}

export default App;