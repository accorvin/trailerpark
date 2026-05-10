import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useListingDetail } from '../hooks/useListings';
import { reparseEmail, reclassifyEmail } from '../hooks/useFeedback';
import ListingDetail from '../components/ListingDetail';
import type { ListingDetail as ListingDetailType } from '../types';

export default function ListingDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data, loading, error } = useListingDetail(id!);
  const [listing, setListing] = useState<ListingDetailType | null>(null);
  const [reparsing, setReparsing] = useState(false);
  const [reparseMsg, setReparseMsg] = useState<string | null>(null);

  const displayListing = listing || data;

  const handleReparse = async () => {
    if (!displayListing?.email) return;
    if (!confirm('Re-parse this email? Existing matches will be removed.')) return;
    setReparsing(true);
    setReparseMsg(null);
    try {
      const result = await reparseEmail(displayListing.email.id);
      setReparseMsg(
        result.matches_deleted
          ? `Re-parsed. ${result.matches_deleted} match(es) were removed.`
          : 'Re-parsed successfully.'
      );
      window.location.reload();
    } catch (err) {
      setReparseMsg(err instanceof Error ? err.message : 'Re-parse failed');
    } finally {
      setReparsing(false);
    }
  };

  const handleReclassify = async (classification: string) => {
    if (!displayListing?.email) return;
    if (!confirm(`Reclassify this email as "${classification}"? Existing data will be replaced.`)) return;
    try {
      await reclassifyEmail(displayListing.email.id, classification);
      window.location.reload();
    } catch {
      // ignore
    }
  };

  if (loading) return <p className="text-gray-500">Loading...</p>;
  if (error) return <p className="text-red-500">{error}</p>;
  if (!displayListing) return <p className="text-gray-500">Listing not found</p>;

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <Link to="/listings" className="text-sm text-blue-600 hover:underline">
          &larr; Back to listings
        </Link>
        {displayListing.email && (
          <div className="flex items-center gap-2">
            <select
              onChange={(e) => {
                if (e.target.value) handleReclassify(e.target.value);
                e.target.value = '';
              }}
              className="text-sm border border-gray-300 rounded px-2 py-1"
              defaultValue=""
            >
              <option value="" disabled>Reclassify...</option>
              <option value="seller_listing">Seller Listing</option>
              <option value="buyer_request">Buyer Request</option>
              <option value="irrelevant">Irrelevant</option>
            </select>
            <button
              onClick={handleReparse}
              disabled={reparsing}
              className="text-sm px-3 py-1 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50"
            >
              {reparsing ? 'Re-parsing...' : 'Re-parse'}
            </button>
          </div>
        )}
      </div>
      {reparseMsg && (
        <div className="mb-4 p-2 text-sm bg-blue-50 text-blue-700 rounded">{reparseMsg}</div>
      )}
      <ListingDetail listing={displayListing} onUpdate={setListing} />
    </div>
  );
}
