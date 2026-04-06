import { useState, useEffect, useRef } from "react";
import { useParams, useNavigate, useLocation } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getCreator } from "@/api/creators";
import { listCreatorEmails, updateEmail, pushToGmail, bulkPushToGmail } from "@/api/emails";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import type { OutreachEmail } from "@/types/email";

interface PendingDraft {
  contactName: string;
  contactEmail: string;
  brandName: string | null;
}

const statusConfig: Record<string, { label: string; className: string }> = {
  draft: { label: "Draft", className: "bg-yellow-100 text-yellow-800" },
  reviewed: { label: "Reviewed", className: "bg-blue-100 text-blue-800" },
  pushed_to_gmail: { label: "In Gmail", className: "bg-purple-100 text-purple-800" },
  sent: { label: "Sent", className: "bg-green-100 text-green-800" },
  opened: { label: "Opened", className: "bg-emerald-100 text-emerald-700" },
  replied: { label: "Replied", className: "bg-teal-100 text-teal-700" },
};

export default function EmailDrafts() {
  const { id: creatorId } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();

  const incomingDrafts = (location.state as { pendingDrafts?: PendingDraft[] })?.pendingDrafts;
  const [pendingDrafts, setPendingDrafts] = useState<PendingDraft[]>(incomingDrafts ?? []);
  const emailCountAtStart = useRef<number | null>(null);

  const { data: creator } = useQuery({
    queryKey: ["creator", creatorId],
    queryFn: () => getCreator(creatorId!),
    enabled: !!creatorId,
  });

  const { data: emails = [], isLoading } = useQuery({
    queryKey: ["emails", creatorId],
    queryFn: () => listCreatorEmails(creatorId!),
    enabled: !!creatorId,
    refetchInterval: () => {
      if (pendingDrafts.length > 0) return 2000;
      return false;
    },
  });

  useEffect(() => {
    if (pendingDrafts.length === 0) return;
    if (emailCountAtStart.current === null) {
      emailCountAtStart.current = emails.length;
      return;
    }
    const newEmailCount = emails.length - emailCountAtStart.current;
    if (newEmailCount >= pendingDrafts.length) {
      setPendingDrafts([]);
      emailCountAtStart.current = null;
    }
  }, [emails.length, pendingDrafts.length]);

  const [editingId, setEditingId] = useState<string | null>(null);
  const [editSubject, setEditSubject] = useState("");
  const [editBody, setEditBody] = useState("");

  const updateMutation = useMutation({
    mutationFn: ({ id, subject, body }: { id: string; subject: string; body: string }) =>
      updateEmail(id, { subject, body }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["emails", creatorId] });
      setEditingId(null);
    },
  });

  const pushMutation = useMutation({
    mutationFn: pushToGmail,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["emails", creatorId] });
    },
  });

  const bulkPushMutation = useMutation({
    mutationFn: bulkPushToGmail,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["emails", creatorId] });
    },
  });

  function startEditing(email: OutreachEmail) {
    setEditingId(email.id);
    setEditSubject(email.subject);
    setEditBody(email.body);
  }

  function cancelEditing() {
    setEditingId(null);
    setEditSubject("");
    setEditBody("");
  }

  const pushableEmails = emails.filter(
    (e) => e.status === "draft" || e.status === "reviewed"
  );

  function handleBulkPush() {
    bulkPushMutation.mutate(pushableEmails.map((e) => e.id));
  }

  return (
    <div className="max-w-4xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <Button
            variant="ghost"
            className="mb-2 -ml-3"
            onClick={() => navigate(`/creators/${creatorId}`)}
          >
            &larr; Back to {creator?.name || "Creator"}
          </Button>
          <h2 className="text-2xl font-bold">Outreach Emails</h2>
          {creator && (
            <p className="text-muted-foreground mt-1">
              Email drafts for {creator.name}
            </p>
          )}
        </div>
        {pushableEmails.length > 0 && (
          <Button
            onClick={handleBulkPush}
            disabled={bulkPushMutation.isPending}
          >
            {bulkPushMutation.isPending ? (
              <span className="flex items-center gap-2">
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                Pushing...
              </span>
            ) : (
              `Push All to Gmail (${pushableEmails.length})`
            )}
          </Button>
        )}
      </div>

      {bulkPushMutation.isSuccess && (
        <Card className="mb-6 border-green-200 bg-green-50">
          <CardContent className="pt-6">
            <p className="text-sm text-green-800">
              Pushed {bulkPushMutation.data.pushed} email{bulkPushMutation.data.pushed !== 1 ? "s" : ""} to Gmail.
              {bulkPushMutation.data.failed > 0 &&
                ` ${bulkPushMutation.data.failed} failed.`}
            </p>
          </CardContent>
        </Card>
      )}

      {pendingDrafts.length > 0 && (
        <div className="space-y-3 mb-6">
          {pendingDrafts.map((draft, i) => (
            <Card key={i} className="border-dashed border-primary/40 bg-primary/5">
              <CardHeader className="pb-2">
                <div className="flex items-center gap-3">
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent shrink-0" />
                  <div>
                    <p className="text-sm font-medium">
                      Drafting email to{" "}
                      <span className="text-foreground">{draft.contactName}</span>
                      {draft.brandName && (
                        <span className="text-muted-foreground"> at {draft.brandName}</span>
                      )}
                    </p>
                    <p className="text-xs text-muted-foreground">{draft.contactEmail}</p>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="pt-0">
                <div className="space-y-2">
                  <div className="h-4 w-2/3 animate-pulse rounded bg-muted" />
                  <div className="h-3 w-full animate-pulse rounded bg-muted" />
                  <div className="h-3 w-5/6 animate-pulse rounded bg-muted" />
                  <div className="h-3 w-4/6 animate-pulse rounded bg-muted" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {isLoading && pendingDrafts.length === 0 ? (
        <div className="flex items-center gap-3 text-muted-foreground">
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          <p>Loading emails...</p>
        </div>
      ) : emails.length === 0 && pendingDrafts.length === 0 ? (
        <Card>
          <CardContent className="pt-6 text-center">
            <p className="text-muted-foreground mb-2">No email drafts yet.</p>
            <p className="text-sm text-muted-foreground">
              Select contacts from Scouted Contacts and click "Draft Emails" to generate
              personalized outreach.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {emails.map((email) => (
            <EmailCard
              key={email.id}
              email={email}
              isEditing={editingId === email.id}
              editSubject={editSubject}
              editBody={editBody}
              onEditSubject={setEditSubject}
              onEditBody={setEditBody}
              onStartEdit={() => startEditing(email)}
              onCancel={cancelEditing}
              onSave={() =>
                updateMutation.mutate({
                  id: email.id,
                  subject: editSubject,
                  body: editBody,
                })
              }
              onPush={() => pushMutation.mutate(email.id)}
              isSaving={updateMutation.isPending}
              isPushing={pushMutation.isPending}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function EmailCard({
  email,
  isEditing,
  editSubject,
  editBody,
  onEditSubject,
  onEditBody,
  onStartEdit,
  onCancel,
  onSave,
  onPush,
  isSaving,
  isPushing,
}: {
  email: OutreachEmail;
  isEditing: boolean;
  editSubject: string;
  editBody: string;
  onEditSubject: (v: string) => void;
  onEditBody: (v: string) => void;
  onStartEdit: () => void;
  onCancel: () => void;
  onSave: () => void;
  onPush: () => void;
  isSaving: boolean;
  isPushing: boolean;
}) {
  const cfg = statusConfig[email.status] || statusConfig.draft;
  const canEdit = email.status === "draft" || email.status === "reviewed";
  const canPush = email.status === "draft" || email.status === "reviewed";

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-1 flex-wrap">
              <Badge variant="outline" className={cfg.className}>
                {cfg.label}
              </Badge>
              {email.brand_name && (
                <Badge variant="secondary">{email.brand_name}</Badge>
              )}
              {email.attach_media_kit && (
                <Badge variant="outline" className="text-xs">
                  Media Kit
                </Badge>
              )}
              {email.gmail_draft_id && (
                <Badge variant="outline" className="text-xs bg-purple-50 text-purple-600">
                  Gmail ID: {email.gmail_draft_id.slice(0, 8)}...
                </Badge>
              )}
            </div>
            <div className="text-sm text-muted-foreground">
              To: <span className="text-foreground">{email.contact_name}</span>
              {email.contact_title && ` (${email.contact_title})`}
              {email.contact_email && (
                <span className="ml-1">— {email.contact_email}</span>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2">
            {canPush && !isEditing && (
              <Button
                size="sm"
                onClick={onPush}
                disabled={isPushing}
              >
                {isPushing ? "Pushing..." : "Push to Gmail"}
              </Button>
            )}
            {canEdit && !isEditing && (
              <Button size="sm" variant="outline" onClick={onStartEdit}>
                Edit
              </Button>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        {isEditing ? (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Subject</Label>
              <Input
                value={editSubject}
                onChange={(e) => onEditSubject(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label>Body</Label>
              <Textarea
                value={editBody}
                onChange={(e) => onEditBody(e.target.value)}
                rows={10}
              />
            </div>
            <div className="flex gap-3">
              <Button onClick={onSave} disabled={isSaving}>
                {isSaving ? "Saving..." : "Save"}
              </Button>
              <Button variant="outline" onClick={onCancel}>
                Cancel
              </Button>
            </div>
          </div>
        ) : (
          <div>
            <p className="font-medium mb-3">{email.subject}</p>
            <p className="text-sm whitespace-pre-wrap text-muted-foreground">
              {email.body}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
