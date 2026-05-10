import { useParams, Link } from 'react-router-dom';
import { useBuyerDetail } from '../hooks/useBuyerDetail';

export default function BuyerDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: buyer, loading, error } = useBuyerDetail(id!);

  if (loading) return <p className="text-gray-500">Loading...</p>;
  if (error) return <p className="text-red-500">{error}</p>;
  if (!buyer) return <p className="text-gray-500">Buyer request not found</p>;

  const title = [buyer.make, buyer.model].filter(Boolean).join(' ') || 'Any Vehicle';

  const fields: Array<{ label: string; value: string | number | null }> = [
    { label: 'Vehicle Type', value: buyer.vehicle_type },
    { label: 'Make', value: buyer.make },
    { label: 'Model', value: buyer.model },
    { label: 'Year Range', value: buyer.year_min && buyer.year_max ? `${buyer.year_min}-${buyer.year_max}` : buyer.year_min || buyer.year_max },
    { label: 'Max Mileage', value: buyer.mileage_max ? `${buyer.mileage_max.toLocaleString()} miles` : null },
    { label: 'Price Range', value: formatPriceRange(buyer.price_min, buyer.price_max) },
    { label: 'Engine', value: buyer.engine_type },
    { label: 'Location', value: buyer.location },
    { label: 'Buyer', value: buyer.buyer_name },
    { label: 'Contact', value: buyer.buyer_contact },
  ];

  return (
    <div>
      <Link to="/buyers" className="text-sm text-blue-600 hover:underline">
        &larr; Back to buyers
      </Link>

      <div className="mt-4 space-y-6">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-2xl font-bold text-gray-900">{title}</h2>

          <dl className="mt-6 grid grid-cols-2 gap-4 text-sm">
            {fields.map(({ label, value }) => (
              <div key={label}>
                <dt className="text-gray-500">{label}</dt>
                <dd className="font-medium text-gray-900">{value ?? '—'}</dd>
              </div>
            ))}
          </dl>

          {buyer.description && (
            <div className="mt-4">
              <h3 className="text-sm font-medium text-gray-500">Description</h3>
              <p className="mt-1 text-gray-700 whitespace-pre-wrap">{buyer.description}</p>
            </div>
          )}
        </div>

        {buyer.email && (
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="font-semibold text-gray-900 mb-3">Original Email</h3>
            <dl className="text-sm space-y-2">
              <div>
                <dt className="text-gray-500 inline">From: </dt>
                <dd className="inline text-gray-900">
                  {buyer.email.from_name} ({buyer.email.from_address})
                </dd>
              </div>
              <div>
                <dt className="text-gray-500 inline">Subject: </dt>
                <dd className="inline text-gray-900">{buyer.email.subject}</dd>
              </div>
              {buyer.email.received_at && (
                <div>
                  <dt className="text-gray-500 inline">Received: </dt>
                  <dd className="inline text-gray-900">
                    {new Date(buyer.email.received_at).toLocaleString()}
                  </dd>
                </div>
              )}
            </dl>
            {buyer.email.body_text && (
              <pre className="mt-3 text-sm text-gray-600 whitespace-pre-wrap bg-gray-50 p-3 rounded">
                {buyer.email.body_text}
              </pre>
            )}
          </div>
        )}

        {buyer.matches.length > 0 && (
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="font-semibold text-gray-900 mb-3">
              Matches ({buyer.matches.length})
            </h3>
            <ul className="space-y-2">
              {buyer.matches.map((m) => (
                <li key={m.id} className="flex items-center justify-between text-sm">
                  <Link
                    to={`/listings/${m.listing_id}`}
                    className="text-blue-600 hover:underline"
                  >
                    {m.listing
                      ? [m.listing.year, m.listing.make, m.listing.model].filter(Boolean).join(' ')
                      : `Listing #${m.listing_id}`}
                  </Link>
                  <span className="text-gray-500">{Math.round(m.score * 100)}% match</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

function formatPriceRange(min: number | null, max: number | null): string | null {
  if (min && max) return `$${min.toLocaleString()} - $${max.toLocaleString()}`;
  if (min) return `From $${min.toLocaleString()}`;
  if (max) return `Up to $${max.toLocaleString()}`;
  return null;
}
