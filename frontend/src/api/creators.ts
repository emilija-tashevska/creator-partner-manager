import { api, ApiError } from "./client";
import type { Creator, CreatorListItem, CreatorCreate, CreatorUpdate } from "@/types/creator";

export function listCreators() {
  return api.get<CreatorListItem[]>("/creators");
}

export function getCreator(id: string) {
  return api.get<Creator>(`/creators/${id}`);
}

export function createCreator(data: CreatorCreate) {
  return api.post<Creator>("/creators", data);
}

export function updateCreator(id: string, data: CreatorUpdate) {
  return api.patch<Creator>(`/creators/${id}`, data);
}

export function updateCreatorStatus(id: string, profileStatus: string) {
  return api.patch<Creator>(`/creators/${id}/status`, { profile_status: profileStatus });
}

export function enrichCreator(id: string) {
  return api.post<Creator>(`/creators/${id}/enrich`);
}

export async function uploadMediaKit(creatorId: string, file: File): Promise<Creator> {
  const formData = new FormData();
  formData.append("file", file);

  const token = localStorage.getItem("token");
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const response = await fetch(`/api/creators/${creatorId}/media-kit`, {
    method: "POST",
    headers,
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Upload failed" }));
    throw new ApiError(response.status, error.detail || "Upload failed");
  }

  return response.json();
}
