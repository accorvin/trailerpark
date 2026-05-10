export interface Listing {
  id: number;
  email_id: string;
  vehicle_type: string | null;
  make: string | null;
  model: string | null;
  year: number | null;
  mileage: number | null;
  price: number | null;
  location: string | null;
  engine_type: string | null;
  condition: string | null;
  quantity: number | null;
  seller_name: string | null;
  seller_contact: string | null;
  description: string | null;
  is_deal: boolean;
  deal_savings: number | null;
  is_archived: boolean;
  archived_at: string | null;
  first_seen_at: string | null;
  last_seen_at: string | null;
  user_edited: boolean;
}

export interface FieldSourceMapping {
  field: string;
  snippet: string | null;
  listing_index: number;
}

export interface ListingDetail extends Listing {
  email: Email | null;
  attachments: Attachment[];
  source_mappings: FieldSourceMapping[];
  original_extracted_data: Record<string, unknown> | null;
}

export interface BuyerRequest {
  id: number;
  email_id: string;
  vehicle_type: string | null;
  make: string | null;
  model: string | null;
  year_min: number | null;
  year_max: number | null;
  mileage_max: number | null;
  price_min: number | null;
  price_max: number | null;
  location: string | null;
  engine_type: string | null;
  buyer_name: string | null;
  buyer_contact: string | null;
  description: string | null;
  is_archived: boolean;
  archived_at: string | null;
  first_seen_at: string | null;
}

export interface BuyerDetail extends BuyerRequest {
  matches: Match[];
}

export interface PriceBenchmark {
  id: number;
  vehicle_type: string | null;
  make: string | null;
  model: string | null;
  year_min: number | null;
  year_max: number | null;
  mileage_min: number | null;
  mileage_max: number | null;
  benchmark_price: number;
  notes: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface Email {
  id: string;
  from_address: string | null;
  from_name: string | null;
  subject: string | null;
  body_text: string | null;
  received_at: string | null;
  classification: string | null;
  processed_at: string | null;
}

export interface Attachment {
  id: number;
  email_id: string;
  filename: string;
  content_type: string | null;
  file_size: number | null;
  is_inline: boolean;
  created_at: string | null;
}

export interface Match {
  id: number;
  buyer_request_id: number;
  listing_id: number;
  score: number;
  matched_at: string | null;
  buyer_request: BuyerRequest | null;
  listing: Listing | null;
}

export interface Stats {
  active_listings: number;
  deals_count: number;
  buyers_count: number;
  matches_count: number;
  attachment_storage_bytes: number;
}

export interface SyncStatus {
  gmail_connected: boolean;
  last_sync_at: string | null;
  last_sync_status: string | null;
  last_sync_error: string | null;
  total_emails: number;
  seller_listings: number;
  buyer_requests: number;
  irrelevant: number;
  parse_errors: number;
  recent_emails: Email[];
}

export interface SyncResponse {
  processed: number;
  message: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface GlossaryEntry {
  id: number;
  abbreviation: string;
  expansion: string;
  category: string | null;
  source: string;
  is_deleted: boolean;
  usage_count: number;
  created_at: string | null;
  updated_at: string | null;
}

export interface FieldCorrection {
  id: number;
  entity_type: string;
  entity_id: number;
  field_name: string;
  original_value: string | null;
  corrected_value: string | null;
  created_at: string | null;
}
