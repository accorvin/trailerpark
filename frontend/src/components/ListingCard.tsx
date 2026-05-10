import { Link } from 'react-router-dom';
import type { Listing } from '../types';
import DealBadge from './DealBadge';

interface Props {
  listing: Listing;
}

function formatPrice(price: number | null): string {
  if (price === null) return 'Call for pricing';
  return `$${price.toLocaleString()}`;
}

function formatMileage(mileage: number | null): string {
  if (mileage === null) return 'N/A';
  return `${(mileage / 1000).toFixed(0)}k mi`;
}

export default function ListingCard({ listing }: Props) {
  const title = [listing.year, listing.make, listing.model].filter(Boolean).join(' ') || 'Unknown Vehicle';

  return (
    <Link
      to={`/listings/${listing.id}`}
      className="block bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow"
    >
      <div className="flex justify-between items-start">
        <div>
          <h3 className="font-semibold text-gray-900">{title}</h3>
          <p className="text-sm text-gray-500 mt-1">
            {listing.vehicle_type && <span className="capitalize">{listing.vehicle_type}</span>}
            {listing.engine_type && <span> &middot; {listing.engine_type}</span>}
          </p>
        </div>
        <div className="text-right">
          <p className="font-bold text-lg text-gray-900">{formatPrice(listing.price)}</p>
          {listing.is_deal && <DealBadge savings={listing.deal_savings} />}
          {listing.user_edited && (
            <span className="text-xs px-1.5 py-0.5 rounded-full bg-amber-100 text-amber-700">edited</span>
          )}
        </div>
      </div>
      <div className="mt-3 flex flex-wrap gap-3 text-sm text-gray-600">
        {listing.mileage !== null && <span>{formatMileage(listing.mileage)}</span>}
        {listing.location && <span>{listing.location}</span>}
        {listing.condition && <span>{listing.condition}</span>}
        {listing.quantity && listing.quantity > 1 && (
          <span className="text-blue-600 font-medium">{listing.quantity} units</span>
        )}
      </div>
      <div className="mt-2 flex justify-between items-center">
        {listing.seller_name && (
          <p className="text-xs text-gray-400">Seller: {listing.seller_name}</p>
        )}
        <span className="text-xs text-blue-500 hover:underline">View source</span>
      </div>
    </Link>
  );
}
