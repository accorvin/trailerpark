import { useState } from 'react';
import { useArchive } from '../hooks/useListings';
import ListingCard from '../components/ListingCard';
import Pagination from '../components/Pagination';

export default function ArchivePage() {
  const [page, setPage] = useState(1);
  const { data, loading } = useArchive(page);

  if (loading) return <p className="text-gray-500">Loading archive...</p>;
  if (!data || data.items.length === 0) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-semibold text-gray-900 mb-2">No archived listings</h2>
        <p className="text-gray-500">
          Listings are automatically archived after 20 days.
        </p>
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-xl font-semibold text-gray-900 mb-4">
        Archived Listings ({data.total})
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
