import { Link } from 'react-router-dom';
import type { Match } from '../types';

interface Props {
  match: Match;
}

export default function MatchCard({ match }: Props) {
  const buyer = match.buyer_request;
  const listing = match.listing;
  const scorePercent = Math.round(match.score * 100);

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className="flex items-center gap-2 mb-3">
        <span
          className={`px-2 py-0.5 text-xs font-medium rounded-full ${
            scorePercent >= 80
              ? 'bg-green-100 text-green-800'
              : scorePercent >= 60
              ? 'bg-yellow-100 text-yellow-800'
              : 'bg-gray-100 text-gray-800'
          }`}
        >
          {scorePercent}% match
        </span>
        {match.matched_at && (
          <span className="text-xs text-gray-400">
            {new Date(match.matched_at).toLocaleDateString()}
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4">
        {/* Buyer side */}
        <div className="border-r border-gray-100 pr-4">
          <p className="text-xs font-medium text-gray-400 uppercase mb-1">Buyer Request</p>
          {buyer && (
            <>
              <Link
                to={`/buyers/${buyer.id}`}
                className="font-medium text-blue-600 hover:underline"
              >
                {[buyer.make, buyer.model].filter(Boolean).join(' ') || 'Any'}
              </Link>
              <p className="text-sm text-gray-500">
                {buyer.year_min && buyer.year_max
                  ? `${buyer.year_min}-${buyer.year_max}`
                  : 'Any year'}
                {buyer.price_max && ` | Up to $${buyer.price_max.toLocaleString()}`}
              </p>
              {buyer.buyer_name && (
                <p className="text-xs text-gray-400 mt-1">{buyer.buyer_name}</p>
              )}
            </>
          )}
        </div>

        {/* Listing side */}
        <div className="pl-4">
          <p className="text-xs font-medium text-gray-400 uppercase mb-1">Listing</p>
          {listing && (
            <>
              <Link
                to={`/listings/${listing.id}`}
                className="font-medium text-blue-600 hover:underline"
              >
                {[listing.year, listing.make, listing.model].filter(Boolean).join(' ')}
              </Link>
              <p className="text-sm text-gray-500">
                {listing.price ? `$${listing.price.toLocaleString()}` : 'Call'}
                {listing.mileage && ` | ${(listing.mileage / 1000).toFixed(0)}k mi`}
              </p>
              {listing.seller_name && (
                <p className="text-xs text-gray-400 mt-1">{listing.seller_name}</p>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
