import type { ListingDetail as ListingDetailType } from '../types';
import DealBadge from './DealBadge';

interface Props {
  listing: ListingDetailType;
}

function formatPrice(price: number | null): string {
  if (price === null) return 'Call for pricing';
  return `$${price.toLocaleString()}`;
}

export default function ListingDetail({ listing }: Props) {
  const title = [listing.year, listing.make, listing.model].filter(Boolean).join(' ') || 'Unknown Vehicle';

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">{title}</h2>
            {listing.is_deal && <DealBadge savings={listing.deal_savings} />}
          </div>
          <p className="text-3xl font-bold text-gray-900">{formatPrice(listing.price)}</p>
        </div>

        <dl className="mt-6 grid grid-cols-2 gap-4 text-sm">
          {[
            ['Vehicle Type', listing.vehicle_type],
            ['Make', listing.make],
            ['Model', listing.model],
            ['Year', listing.year],
            ['Mileage', listing.mileage ? `${listing.mileage.toLocaleString()} miles` : null],
            ['Engine', listing.engine_type],
            ['Condition', listing.condition],
            ['Location', listing.location],
            ['Quantity', listing.quantity],
            ['Seller', listing.seller_name],
            ['Contact', listing.seller_contact],
          ].map(([label, value]) => (
            value != null && (
              <div key={label as string}>
                <dt className="text-gray-500">{label as string}</dt>
                <dd className="font-medium text-gray-900">{String(value)}</dd>
              </div>
            )
          ))}
        </dl>

        {listing.description && (
          <div className="mt-4">
            <h3 className="text-sm font-medium text-gray-500">Description</h3>
            <p className="mt-1 text-gray-700 whitespace-pre-wrap">{listing.description}</p>
          </div>
        )}
      </div>

      {/* Original Email */}
      {listing.email && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="font-semibold text-gray-900 mb-3">Original Email</h3>
          <dl className="text-sm space-y-2">
            <div>
              <dt className="text-gray-500 inline">From: </dt>
              <dd className="inline text-gray-900">
                {listing.email.from_name} ({listing.email.from_address})
              </dd>
            </div>
            <div>
              <dt className="text-gray-500 inline">Subject: </dt>
              <dd className="inline text-gray-900">{listing.email.subject}</dd>
            </div>
            {listing.email.received_at && (
              <div>
                <dt className="text-gray-500 inline">Received: </dt>
                <dd className="inline text-gray-900">
                  {new Date(listing.email.received_at).toLocaleString()}
                </dd>
              </div>
            )}
          </dl>
          {listing.email.body_text && (
            <pre className="mt-3 text-sm text-gray-600 whitespace-pre-wrap bg-gray-50 p-3 rounded">
              {listing.email.body_text}
            </pre>
          )}
        </div>
      )}

      {/* Attachments */}
      {listing.attachments.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="font-semibold text-gray-900 mb-3">Attachments</h3>
          <ul className="space-y-2">
            {listing.attachments.map((att) => (
              <li key={att.id} className="flex items-center gap-2 text-sm">
                <a
                  href={`/api/attachments/${att.id}/file`}
                  className="text-blue-600 hover:underline"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {att.filename}
                </a>
                {att.file_size && (
                  <span className="text-gray-400">
                    ({(att.file_size / 1024).toFixed(1)} KB)
                  </span>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
