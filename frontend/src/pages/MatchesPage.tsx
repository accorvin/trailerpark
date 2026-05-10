import { useState } from 'react';
import { useMatches } from '../hooks/useMatches';
import MatchCard from '../components/MatchCard';
import Pagination from '../components/Pagination';

export default function MatchesPage() {
  const [page, setPage] = useState(1);
  const { data, loading, error } = useMatches(page);

  if (loading) return <p className="text-gray-500">Loading matches...</p>;
  if (error) return <p className="text-red-500">{error}</p>;
  if (!data || data.items.length === 0) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-semibold text-gray-900 mb-2">No matches found</h2>
        <p className="text-gray-500">
          Matches appear when buyer requests align with active listings.
        </p>
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-xl font-semibold text-gray-900 mb-4">
        Buyer-Seller Matches ({data.total})
      </h2>
      <div className="space-y-3">
        {data.items.map((match) => (
          <MatchCard key={match.id} match={match} />
        ))}
      </div>
      <Pagination page={page} pages={data.pages} onPageChange={setPage} />
    </div>
  );
}
