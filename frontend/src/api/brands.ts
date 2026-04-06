import { api } from "./client";
import type { BrandTarget, BrandDiscoveryStatus } from "@/types/brand";
import type { ScoutStatus } from "@/types/contact";

export function triggerBrandDiscovery(creatorId: string) {
  return api.post<BrandDiscoveryStatus>(`/creators/${creatorId}/brands/discover`);
}

export function listBrandTargets(
  creatorId: string,
  params?: { status?: string; discovery_round?: number }
) {
  const query = new URLSearchParams();
  if (params?.status) query.set("status", params.status);
  if (params?.discovery_round) query.set("discovery_round", String(params.discovery_round));
  const qs = query.toString();
  return api.get<BrandTarget[]>(`/creators/${creatorId}/brands${qs ? `?${qs}` : ""}`);
}

export function approveBrand(brandId: string) {
  return api.patch<BrandTarget>(`/brands/${brandId}/approve`);
}

export function blacklistBrand(brandId: string) {
  return api.patch<BrandTarget>(`/brands/${brandId}/blacklist`);
}

export function unblacklistBrand(brandId: string) {
  return api.patch<BrandTarget>(`/brands/${brandId}/unblacklist`);
}

export function triggerScout(brandId: string) {
  return api.post<BrandTarget>(`/brands/${brandId}/scout`);
}

export function getScoutStatus(brandId: string) {
  return api.get<ScoutStatus>(`/brands/${brandId}/scout-status`);
}
