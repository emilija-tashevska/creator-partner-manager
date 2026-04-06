export interface Creator {
  id: string;
  agency_id: string;
  name: string;
  instagram_handle: string | null;
  tiktok_handle: string | null;
  youtube_handle: string | null;
  x_handle: string | null;
  content_links: string[] | null;
  niche: string | null;
  audience_size_approx: string | null;
  media_kit_url: string | null;
  media_kit_file_path: string | null;
  bio_summary: string | null;
  content_style: string | null;
  audience_demographics: Record<string, unknown> | null;
  tone_descriptors: string[] | null;
  collaboration_types: string[] | null;
  collaboration_verticals: string[] | null;
  enrichment_status: string;
  profile_status: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreatorListItem {
  id: string;
  name: string;
  niche: string | null;
  audience_size_approx: string | null;
  enrichment_status: string;
  profile_status: string;
  instagram_handle: string | null;
  created_at: string;
}

export interface CreatorCreate {
  name: string;
  instagram_handle?: string;
  tiktok_handle?: string;
  youtube_handle?: string;
  x_handle?: string;
  content_links?: string[];
  niche?: string;
  audience_size_approx?: string;
  media_kit_url?: string;
  notes?: string;
}

export interface CreatorUpdate {
  name?: string;
  instagram_handle?: string;
  tiktok_handle?: string;
  youtube_handle?: string;
  x_handle?: string;
  content_links?: string[];
  niche?: string;
  audience_size_approx?: string;
  media_kit_url?: string;
  bio_summary?: string;
  content_style?: string;
  audience_demographics?: Record<string, unknown>;
  tone_descriptors?: string[];
  collaboration_types?: string[];
  collaboration_verticals?: string[];
  notes?: string;
}
