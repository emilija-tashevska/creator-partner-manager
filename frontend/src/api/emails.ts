import { api } from "./client";
import type {
  OutreachEmail,
  EmailDraftRequest,
  EmailDraftStatus,
  EmailUpdate,
  EmailPushResult,
  EmailBulkPushResult,
} from "@/types/email";

export function triggerDraftEmails(data: EmailDraftRequest) {
  return api.post<EmailDraftStatus>("/emails/draft", data);
}

export function listCreatorEmails(creatorId: string) {
  return api.get<OutreachEmail[]>(`/creators/${creatorId}/emails`);
}

export function getEmail(emailId: string) {
  return api.get<OutreachEmail>(`/emails/${emailId}`);
}

export function updateEmail(emailId: string, data: EmailUpdate) {
  return api.patch<OutreachEmail>(`/emails/${emailId}`, data);
}

export function pushToGmail(emailId: string) {
  return api.post<EmailPushResult>(`/emails/${emailId}/push-to-gmail`);
}

export function bulkPushToGmail(emailIds: string[]) {
  return api.post<EmailBulkPushResult>("/emails/bulk-push", { email_ids: emailIds });
}
