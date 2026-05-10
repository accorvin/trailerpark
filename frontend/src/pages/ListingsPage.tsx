import { useState } from 'react';
import { useListings } from '../hooks/useListings';
import ListingCard from '../components/ListingCard';
import FilterBar from '../components/FilterBar';
import SearchInput from '../components/SearchInput';
import Pagination from '../components/Pagination';

const emptyFilters = {
  vehicle_type: '',
  make: '',
  model: '',
  year_min: '',
  year_max: '',
  price_min: '',
  price_max: '',
  mileage_max: '',
  engine_type: '',
  location: '',
};

export default function ListingsPage() {
  const [filters, setFilters] = useState(emptyFilters);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);

  const apiFilters: Record<string, string | number | undefined> = { page };
  Object.entries(filters).forEach(([key, value]) => {
    if (value) apiFilters[key] = value;
  });
  if (search) apiFilters.search = search;

  const { data, loading, error } = useListings(apiFilters);

  return (
    <div>
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Active Listings</h2>
      <div className="mb-4">
        <SearchInput value={search} onChange={(v) => { setSearch(v); setPage(1); }} placeholder="Search listings..." />
      </div>
      <FilterBar filters={filters} onChange={(f) => { setFilters(f); setPage(1); }} />

      {loading && <p className="text-gray-500">Loading...</p>}
      {error && <p className="text-red-500">{error}</p>}
      {data && (
        <>
          <p className="text-sm text-gray-500 mb-3">{data.total} listings</p>
          <div className="space-y-3">
            {data.items.map((listing) => (
              <ListingCard key={listing.id} listing={listing} />
            ))}
          </div>
          <Pagination page={page} pages={data.pages} onPageChange={setPage} />
        </>
      )}
    </div>
  );
}
