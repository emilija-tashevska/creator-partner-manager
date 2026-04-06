export interface BrandTarget {
  id: string;
  agency_id: string;
  creator_id: string;
  company_name: string;
  company_domain: string | null;
  reasoning: string | null;
  apollo_organization_id: string | null;
  status: "suggested" | "approved" | "blacklisted";
  scouting_status: string | null;
  discovery_round: number;
  created_at: string;
  updated_at: string;
}

export interface BrandDiscoveryStatus {
  status: string;
  discovery_round: number | null;
  brands_found: number | null;
}
