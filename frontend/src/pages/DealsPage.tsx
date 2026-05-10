import { useState } from 'react';
import { useDeals } from '../hooks/useDeals';
import ListingCard from '../components/ListingCard';
import Pagination from '../components/Pagination';

export default function DealsPage() {
  const [page, setPage] = useState(1);
  const { data, loading, error } = useDeals(page);

  if (loading) return <p className="text-gray-500">Loading deals...</p>;
  if (error) return <p className="text-red-500">{error}</p>;
  if (!data || data.items.length === 0) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-semibold text-gray-900 mb-2">No deals found</h2>
        <p className="text-gray-500">
          Deals appear when listings are priced significantly below market benchmarks.
        </p>
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-xl font-semibold text-gray-900 mb-4">
        Deals ({data.total})
      </h2>
      <div className="space-y-3">
        {data.items.map((listing) => (
          <ListingCard key={listing.id} listing={listing} />
        ))}
      </div>
      <Pagination page={page} pages={data.pages} onPageChange={setPage} />
    </div>
  );
}
