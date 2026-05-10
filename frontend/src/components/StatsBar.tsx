import { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { Stats } from '../types';

export default function StatsBar() {
  const [stats, setStats] = useState<Stats | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await api.get<Stats>('/stats');
        setStats(data);
      } catch {
        // ignore
      }
    };
    load();
    const interval = setInterval(load, 30000);
    return () => clearInterval(interval);
  }, []);

  if (!stats) return null;

  const items = [
    { label: 'Active Listings', value: stats.active_listings },
    { label: 'Deals', value: stats.deals_count },
    { label: 'Buyers', value: stats.buyers_count },
    { label: 'Matches', value: stats.matches_count },
  ];

  return (
    <div className="bg-white border-b border-gray-200 px-6 py-3 flex gap-6">
      {items.map(({ label, value }) => (
        <div key={label} className="text-sm">
          <span className="text-gray-500">{label}: </span>
          <span className="font-semibold text-gray-900">{value}</span>
        </div>
      ))}
    </div>
  );
}
