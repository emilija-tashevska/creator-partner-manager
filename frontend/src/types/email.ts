export interface OutreachEmail {
  id: string;
  agency_id: string;
  contact_id: string;
  creator_id: string;
  brand_target_id: string;
  drafted_by_user_id: string;
  subject: string;
  body: string;
  attach_media_kit: boolean;
  status: string;
  gmail_draft_id: string | null;
  sent_at: string | null;
  opened_at: string | null;
  replied_at: string | null;
  created_at: string;
  updated_at: string;
  contact_name: string | null;
  contact_email: string | null;
  contact_title: string | null;
  brand_name: string | null;
}

export interface EmailDraftRequest {
  contact_ids: string[];
  creator_id: string;
  brand_target_id: string;
}

export interface EmailUpdate {
  subject?: string;
  body?: string;
  attach_media_kit?: boolean;
}

export interface EmailDraftStatus {
  status: string;
  emails_drafted: number;
}

export interface EmailPushResult {
  id: string;
  status: string;
  gmail_draft_id: string | null;
}

export interface EmailBulkPushResult {
  pushed: number;
  failed: number;
  results: EmailPushResult[];
}
