import { useParams, Link } from 'react-router-dom';
import { useListingDetail } from '../hooks/useListings';
import ListingDetail from '../components/ListingDetail';

export default function ListingDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data, loading, error } = useListingDetail(id!);

  if (loading) return <p className="text-gray-500">Loading...</p>;
  if (error) return <p className="text-red-500">{error}</p>;
  if (!data) return <p className="text-gray-500">Listing not found</p>;

  return (
    <div>
      <Link to="/listings" className="text-sm text-blue-600 hover:underline mb-4 inline-block">
        &larr; Back to listings
      </Link>
      <ListingDetail listing={data} />
    </div>
  );
}
