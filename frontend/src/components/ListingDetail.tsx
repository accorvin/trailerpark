import { useState } from 'react';
import type { ListingDetail as ListingDetailType } from '../types';
import DealBadge from './DealBadge';
import EditableField from './EditableField';
import ParseTransparency from './ParseTransparency';
import { updateListing } from '../hooks/useFeedback';

interface Props {
  listing: ListingDetailType;
  onUpdate?: (updated: ListingDetailType) => void;
}

function formatPrice(price: number | null): string {
  if (price === null) return 'Call for pricing';
  return `$${price.toLocaleString()}`;
}

const EDITABLE_FIELDS: Array<{ label: string; key: string }> = [
  { label: 'Vehicle Type', key: 'vehicle_type' },
  { label: 'Make', key: 'make' },
  { label: 'Model', key: 'model' },
  { label: 'Year', key: 'year' },
  { label: 'Mileage', key: 'mileage' },
  { label: 'Engine', key: 'engine_type' },
  { label: 'Condition', key: 'condition' },
  { label: 'Location', key: 'location' },
  { label: 'Quantity', key: 'quantity' },
  { label: 'Seller', key: 'seller_name' },
  { label: 'Contact', key: 'seller_contact' },
];

export default function ListingDetail({ listing, onUpdate }: Props) {
  const title = [listing.year, listing.make, listing.model].filter(Boolean).join(' ') || 'Unknown Vehicle';
  const [editing, setEditing] = useState(false);
  const [changes, setChanges] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [showTransparency, setShowTransparency] = useState(false);

  const handleFieldChange = (fieldName: string, value: string) => {
    setChanges((prev) => ({ ...prev, [fieldName]: value }));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      // Convert numeric fields
      const payload: Record<string, unknown> = {};
      for (const [key, value] of Object.entries(changes)) {
        if (['year', 'mileage', 'quantity'].includes(key)) {
          payload[key] = value ? parseInt(value, 10) : null;
        } else if (key === 'price') {
          payload[key] = value ? parseFloat(value) : null;
        } else {
          payload[key] = value || null;
        }
      }
      const updated = await updateListing(listing.id, payload);
      onUpdate?.(updated);
      setEditing(false);
      setChanges({});
    } catch {
      // ignore
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    setEditing(false);
    setChanges({});
  };

  const extractedFields = EDITABLE_FIELDS.map(({ label, key }) => ({
    label,
    value: (listing as Record<string, unknown>)[key] as string | number | null,
  }));

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">
              {title}
              {listing.user_edited && (
                <span className="ml-2 text-xs px-2 py-0.5 rounded-full bg-amber-100 text-amber-700 align-middle">
                  edited
                </span>
              )}
            </h2>
            {listing.is_deal && <DealBadge savings={listing.deal_savings} />}
          </div>
          <div className="flex items-center gap-3">
            <p className="text-3xl font-bold text-gray-900">{formatPrice(listing.price)}</p>
            {!editing ? (
              <button onClick={() => setEditing(true)} className="px-3 py-1.5 text-sm border border-gray-300 rounded hover:bg-gray-50">
                Edit
              </button>
            ) : (
              <div className="flex gap-2">
                <button onClick={handleCancel} className="px-3 py-1.5 text-sm border border-gray-300 rounded hover:bg-gray-50">
                  Cancel
                </button>
                <button
                  onClick={handleSave}
                  disabled={saving || Object.keys(changes).length === 0}
                  className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                >
                  {saving ? 'Saving...' : 'Save'}
                </button>
              </div>
            )}
          </div>
        </div>

        <dl className="mt-6 grid grid-cols-2 gap-4 text-sm">
          {EDITABLE_FIELDS.map(({ label, key }) => {
            const value = (listing as Record<string, unknown>)[key] as string | number | null;
            if (key === 'mileage' && value && !editing) {
              return (
                <div key={key}>
                  <dt className="text-gray-500">{label}</dt>
                  <dd className="font-medium text-gray-900">{(value as number).toLocaleString()} miles</dd>
                </div>
              );
            }
            return (
              <EditableField
                key={key}
                label={label}
                value={value}
                fieldName={key}
                editing={editing}
                onChange={handleFieldChange}
              />
            );
          })}
        </dl>

        {listing.description && (
          <div className="mt-4">
            <h3 className="text-sm font-medium text-gray-500">Description</h3>
            <p className="mt-1 text-gray-700 whitespace-pre-wrap">{listing.description}</p>
          </div>
        )}
      </div>

      {/* Parse Transparency */}
      {listing.email?.body_text && (listing.source_mappings?.length > 0) && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <button
            onClick={() => setShowTransparency(!showTransparency)}
            className="flex items-center gap-2 font-semibold text-gray-900"
          >
            <span className={`transform transition-transform ${showTransparency ? 'rotate-90' : ''}`}>&#9654;</span>
            View Parse Details
          </button>
          {showTransparency && (
            <div className="mt-4">
              <ParseTransparency
                emailText={listing.email.body_text}
                sourceMappings={listing.source_mappings}
                extractedFields={extractedFields}
              />
            </div>
          )}
        </div>
      )}

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
