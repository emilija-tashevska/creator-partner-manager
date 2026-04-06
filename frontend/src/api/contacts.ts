import { api } from "./client";
import type { Contact, ContactWithBrands, ContactUpdate } from "@/types/contact";

export function listCreatorContacts(creatorId: string) {
  return api.get<ContactWithBrands[]>(`/creators/${creatorId}/contacts`);
}

export function listBrandContacts(brandId: string) {
  return api.get<Contact[]>(`/brands/${brandId}/contacts`);
}

export function getContact(contactId: string) {
  return api.get<ContactWithBrands>(`/contacts/${contactId}`);
}

export function updateContact(contactId: string, data: ContactUpdate) {
  return api.patch<Contact>(`/contacts/${contactId}`, data);
}

export function listConflictContacts() {
  return api.get<Contact[]>("/contacts/duplicates");
}
