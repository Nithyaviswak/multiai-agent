export const DESTINATIONS = [
  {
    city: 'Tokyo',
    country: 'Japan',
    note: 'A masterclass in transit',
    img: 'https://images.unsplash.com/photo-1540959733332-eab4deebeeaf?auto=format&fit=crop&w=1200&q=70',
    grad: 'from-[#1f2937] to-[#4b5563]',
  },
  {
    city: 'Bali',
    country: 'Indonesia',
    note: 'Island calm, real rhythm',
    img: 'https://images.unsplash.com/photo-1537996194471-e657df975ab4?auto=format&fit=crop&w=1200&q=70',
    grad: 'from-[#14532d] to-[#16a34a]',
  },
  {
    city: 'Paris',
    country: 'France',
    note: 'Culture at every corner',
    img: 'https://images.unsplash.com/photo-1502602898657-3e91760cbb34?auto=format&fit=crop&w=1200&q=70',
    grad: 'from-[#3b2f2a] to-[#8a6d5a]',
  },
  {
    city: 'Switzerland',
    country: 'Alps',
    note: 'Trains through the mountains',
    img: 'https://images.unsplash.com/photo-1530124566582-a618bc2615dc?auto=format&fit=crop&w=1200&q=70',
    grad: 'from-[#0f3b52] to-[#38bdf8]',
  },
  {
    city: 'Dubai',
    country: 'UAE',
    note: 'Desert to skyline in an hour',
    img: 'https://images.unsplash.com/photo-1512453979798-5ea266f8880c?auto=format&fit=crop&w=1200&q=70',
    grad: 'from-[#7c5c3d] to-[#e2b96b]',
  },
];

export const TRAVEL_STYLES = [
  { id: 'relaxed', label: 'Relaxed', hint: 'Steady pace, fewer stops' },
  { id: 'adventure', label: 'Adventure', hint: 'Bike or drive, stretch the legs' },
  { id: 'luxury', label: 'Luxury', hint: 'Comfortable private transit' },
  { id: 'budget', label: 'Budget', hint: 'The most affordable route' },
  { id: 'food', label: 'Food', hint: 'Meals are the priority' },
  { id: 'culture', label: 'Culture', hint: 'Museums, monuments and heritage' },
  { id: 'nature', label: 'Nature', hint: 'Parks, gardens and viewpoints' },
];

export const MEAL_OPTIONS = [
  { id: 'tiffin', label: 'Tiffin', hint: 'Morning ~06:00–11:00' },
  { id: 'lunch', label: 'Lunch', hint: 'Midday ~11:00–16:00' },
  { id: 'dinner', label: 'Dinner', hint: 'Evening ~16:00–23:00' },
];

export const MODE_OPTIONS = [
  { id: 'car', label: 'Car' },
  { id: 'bus', label: 'Bus' },
  { id: 'train', label: 'Train' },
  { id: 'bike', label: 'Bike' },
];

export const REFINE_SUGGESTIONS = [
  'Make this trip cheaper',
  'Add more food experiences',
  'Make the itinerary more relaxed',
  'Fewer, better places',
  'Swap to the train',
  'Keep mornings easy',
];

export const PROMPT_EXAMPLES = [
  ['Bengaluru → Mysuru', 'Car, lunch, places — 6 hours'],
  ['Chennai → Pondicherry', 'Bus, dinner, a little sightseeing'],
  ['Pune → Mumbai', 'Train, tiffin on the way'],
  ['Cochin → Alleppey', 'Bike, viewpoints, lunch + dinner'],
  ['Delhi → Jaipur', 'Fastest route under 90 minutes'],
];