export interface Contact {
  id: string;
  agency_id: string;
  full_name: string;
  title: string | null;
  company_name: string | null;
  email: string;
  linkedin_url: string | null;
  apollo_person_id: string | null;
  has_conflict: boolean;
  created_at: string;
  updated_at: string;
}

export interface ContactWithBrands extends Contact {
  brand_names: string[];
}

export interface ContactUpdate {
  full_name?: string;
  title?: string;
  company_name?: string;
  email?: string;
  linkedin_url?: string;
}

export interface ScoutStatus {
  scouting_status: string;
  contacts_found: number;
  has_conflicts: boolean;
}
