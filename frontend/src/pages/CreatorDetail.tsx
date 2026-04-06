import { useState, useRef, useEffect } from "react";
import { useParams, useNavigate, useLocation } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getCreator, updateCreator, updateCreatorStatus, enrichCreator, uploadMediaKit } from "@/api/creators";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import type { CreatorUpdate } from "@/types/creator";

const statusColors: Record<string, string> = {
  draft: "bg-yellow-100 text-yellow-800",
  reviewed: "bg-blue-100 text-blue-800",
  active: "bg-green-100 text-green-800",
};

const statusFlow = ["draft", "reviewed", "active"];

export default function CreatorDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState(false);
  const [editForm, setEditForm] = useState<CreatorUpdate>({});
  const pendingMediaKit = (location.state as { pendingMediaKit?: boolean })?.pendingMediaKit;

  const { data: creator, isLoading } = useQuery({
    queryKey: ["creator", id],
    queryFn: () => getCreator(id!),
    enabled: !!id,
    refetchInterval: (query) => {
      const status = query.state.data?.enrichment_status;
      return status === "pending" || status === "processing" ? 2000 : false;
    },
  });

  const updateMutation = useMutation({
    mutationFn: (data: CreatorUpdate) => updateCreator(id!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["creator", id] });
      queryClient.invalidateQueries({ queryKey: ["creators"] });
      setEditing(false);
    },
  });

  const statusMutation = useMutation({
    mutationFn: (status: string) => updateCreatorStatus(id!, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["creator", id] });
      queryClient.invalidateQueries({ queryKey: ["creators"] });
    },
  });

  const enrichMutation = useMutation({
    mutationFn: () => enrichCreator(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["creator", id] });
      queryClient.invalidateQueries({ queryKey: ["creators"] });
    },
  });

  const mediaKitInputRef = useRef<HTMLInputElement>(null);
  const hasPrompted = useRef(false);

  useEffect(() => {
    if (pendingMediaKit && creator && !hasPrompted.current) {
      hasPrompted.current = true;
      setTimeout(() => mediaKitInputRef.current?.click(), 300);
    }
  }, [pendingMediaKit, creator]);

  const mediaKitMutation = useMutation({
    mutationFn: (file: File) => uploadMediaKit(id!, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["creator", id] });
      if (mediaKitInputRef.current) mediaKitInputRef.current.value = "";
    },
  });

  function startEditing() {
    if (!creator) return;
    setEditForm({
      name: creator.name,
      instagram_handle: creator.instagram_handle || "",
      tiktok_handle: creator.tiktok_handle || "",
      youtube_handle: creator.youtube_handle || "",
      x_handle: creator.x_handle || "",
      niche: creator.niche || "",
      audience_size_approx: creator.audience_size_approx || "",
      bio_summary: creator.bio_summary || "",
      content_style: creator.content_style || "",
      notes: creator.notes || "",
    });
    setEditing(true);
  }

  function updateField(field: keyof CreatorUpdate, value: string) {
    setEditForm((prev) => ({ ...prev, [field]: value }));
  }

  if (isLoading) {
    return <div className="text-muted-foreground">Loading...</div>;
  }

  if (!creator) {
    return <div className="text-destructive">Creator not found</div>;
  }

  const nextStatus = statusFlow[statusFlow.indexOf(creator.profile_status) + 1];

  return (
    <div className="max-w-3xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <Button variant="ghost" className="mb-2 -ml-3" onClick={() => navigate("/creators")}>
            &larr; Back to Creators
          </Button>
          <h2 className="text-2xl font-bold">{creator.name}</h2>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className={statusColors[creator.profile_status] || ""}>
            {creator.profile_status}
          </Badge>
          {nextStatus && (
            <Button
              size="sm"
              variant="outline"
              onClick={() => statusMutation.mutate(nextStatus)}
              disabled={statusMutation.isPending}
            >
              Mark as {nextStatus}
            </Button>
          )}
          {!editing && (
            <Button size="sm" onClick={startEditing}>Edit</Button>
          )}
        </div>
      </div>

      {editing ? (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            updateMutation.mutate(editForm);
          }}
          className="space-y-6"
        >
          <Card>
            <CardHeader><CardTitle className="text-lg">Basic Info</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Name</Label>
                <Input value={editForm.name || ""} onChange={(e) => updateField("name", e.target.value)} />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Niche</Label>
                  <Input value={editForm.niche || ""} onChange={(e) => updateField("niche", e.target.value)} />
                </div>
                <div className="space-y-2">
                  <Label>Audience Size</Label>
                  <Input value={editForm.audience_size_approx || ""} onChange={(e) => updateField("audience_size_approx", e.target.value)} />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Instagram</Label>
                  <Input value={editForm.instagram_handle || ""} onChange={(e) => updateField("instagram_handle", e.target.value)} />
                </div>
                <div className="space-y-2">
                  <Label>TikTok</Label>
                  <Input value={editForm.tiktok_handle || ""} onChange={(e) => updateField("tiktok_handle", e.target.value)} />
                </div>
                <div className="space-y-2">
                  <Label>YouTube</Label>
                  <Input value={editForm.youtube_handle || ""} onChange={(e) => updateField("youtube_handle", e.target.value)} />
                </div>
                <div className="space-y-2">
                  <Label>X / Twitter</Label>
                  <Input value={editForm.x_handle || ""} onChange={(e) => updateField("x_handle", e.target.value)} />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle className="text-lg">AI-Enriched Profile</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Bio Summary</Label>
                <Textarea value={editForm.bio_summary || ""} onChange={(e) => updateField("bio_summary", e.target.value)} rows={3} />
              </div>
              <div className="space-y-2">
                <Label>Content Style</Label>
                <Textarea value={editForm.content_style || ""} onChange={(e) => updateField("content_style", e.target.value)} rows={3} />
              </div>
              <div className="space-y-2">
                <Label>Notes</Label>
                <Textarea value={editForm.notes || ""} onChange={(e) => updateField("notes", e.target.value)} rows={3} />
              </div>
            </CardContent>
          </Card>

          <div className="flex gap-3">
            <Button type="submit" disabled={updateMutation.isPending}>
              {updateMutation.isPending ? "Saving..." : "Save Changes"}
            </Button>
            <Button type="button" variant="outline" onClick={() => setEditing(false)}>Cancel</Button>
          </div>
        </form>
      ) : (
        <div className="space-y-6">
          <Card>
            <CardHeader><CardTitle className="text-lg">Basic Info</CardTitle></CardHeader>
            <CardContent>
              <dl className="grid grid-cols-2 gap-x-6 gap-y-4 text-sm">
                <Field label="Niche" value={creator.niche} />
                <Field label="Audience Size" value={creator.audience_size_approx} />
                <Field label="Instagram" value={creator.instagram_handle} />
                <Field label="TikTok" value={creator.tiktok_handle} />
                <Field label="YouTube" value={creator.youtube_handle} />
                <Field label="X / Twitter" value={creator.x_handle} />
                <div className="col-span-2">
                  <dt className="text-muted-foreground mb-1">Media Kit</dt>
                  <dd className="flex items-center gap-3">
                    {creator.media_kit_file_path ? (
                      <>
                        <Badge variant="secondary" className="gap-1.5">
                          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/></svg>
                          PDF uploaded
                        </Badge>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => mediaKitInputRef.current?.click()}
                          disabled={mediaKitMutation.isPending}
                        >
                          Replace
                        </Button>
                      </>
                    ) : (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => mediaKitInputRef.current?.click()}
                        disabled={mediaKitMutation.isPending}
                      >
                        {mediaKitMutation.isPending ? "Uploading..." : "Upload PDF"}
                      </Button>
                    )}
                    <input
                      ref={mediaKitInputRef}
                      type="file"
                      accept=".pdf"
                      className="hidden"
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) mediaKitMutation.mutate(file);
                      }}
                    />
                    {mediaKitMutation.isPending && (
                      <span className="text-xs text-muted-foreground">Uploading...</span>
                    )}
                  </dd>
                </div>
              </dl>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">AI-Enriched Profile</CardTitle>
                <div className="flex items-center gap-2">
                  <Badge variant="outline">
                    enrichment: {creator.enrichment_status}
                  </Badge>
                  {creator.enrichment_status !== "processing" && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => enrichMutation.mutate()}
                      disabled={enrichMutation.isPending}
                    >
                      {enrichMutation.isPending ? "Queuing..." : "Re-enrich"}
                    </Button>
                  )}
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {creator.enrichment_status === "completed" ? (
                <div className="space-y-4 text-sm">
                  {creator.bio_summary && (
                    <div>
                      <dt className="text-muted-foreground mb-1 font-medium">Bio Summary</dt>
                      <dd>{creator.bio_summary}</dd>
                    </div>
                  )}
                  {creator.content_style && (
                    <div>
                      <dt className="text-muted-foreground mb-1 font-medium">Content Style</dt>
                      <dd>{creator.content_style}</dd>
                    </div>
                  )}
                  {creator.tone_descriptors?.length ? (
                    <div>
                      <dt className="text-muted-foreground mb-1 font-medium">Tone</dt>
                      <dd className="flex gap-2 flex-wrap">
                        {creator.tone_descriptors.map((t) => (
                          <Badge key={t} variant="secondary">{t}</Badge>
                        ))}
                      </dd>
                    </div>
                  ) : null}
                  {creator.collaboration_types?.length ? (
                    <div>
                      <dt className="text-muted-foreground mb-1 font-medium">Collaboration Types</dt>
                      <dd className="flex gap-2 flex-wrap">
                        {creator.collaboration_types.map((t) => (
                          <Badge key={t} variant="outline">{t}</Badge>
                        ))}
                      </dd>
                    </div>
                  ) : null}
                  {creator.collaboration_verticals?.length ? (
                    <div>
                      <dt className="text-muted-foreground mb-1 font-medium">Verticals</dt>
                      <dd className="flex gap-2 flex-wrap">
                        {creator.collaboration_verticals.map((v) => (
                          <Badge key={v} variant="outline">{v}</Badge>
                        ))}
                      </dd>
                    </div>
                  ) : null}
                </div>
              ) : creator.enrichment_status === "processing" || creator.enrichment_status === "pending" ? (
                <div className="flex items-center gap-3 text-muted-foreground">
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
                  <p>AI enrichment in progress — usually takes 10-30 seconds. This page updates automatically.</p>
                </div>
              ) : creator.enrichment_status === "failed" ? (
                <p className="text-destructive">Enrichment failed. Click "Re-enrich" to try again.</p>
              ) : (
                <p className="text-muted-foreground">
                  Enrichment will start automatically when a creator is added.
                </p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Outreach Workflow</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <button
                  type="button"
                  onClick={() => navigate(`/creators/${id}/brands`)}
                  className="group text-left rounded-lg border p-4 transition-colors hover:border-primary hover:bg-primary/5"
                >
                  <div className="flex items-center gap-2 mb-2">
                    <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-xs font-bold text-primary-foreground">1</span>
                    <span className="font-semibold">Brand Discovery</span>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Find and approve ideal brand partners using AI.
                  </p>
                </button>

                <button
                  type="button"
                  onClick={() => navigate(`/creators/${id}/contacts`)}
                  className="group text-left rounded-lg border p-4 transition-colors hover:border-primary hover:bg-primary/5"
                >
                  <div className="flex items-center gap-2 mb-2">
                    <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-xs font-bold text-primary-foreground">2</span>
                    <span className="font-semibold">Scouted Contacts</span>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Review contacts found at your approved brands.
                  </p>
                </button>

                <button
                  type="button"
                  onClick={() => navigate(`/creators/${id}/emails`)}
                  className="group text-left rounded-lg border p-4 transition-colors hover:border-primary hover:bg-primary/5"
                >
                  <div className="flex items-center gap-2 mb-2">
                    <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-xs font-bold text-primary-foreground">3</span>
                    <span className="font-semibold">Email Outreach</span>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Draft, review, and send outreach emails.
                  </p>
                </button>
              </div>
            </CardContent>
          </Card>

          <Separator />

          {creator.notes && (
            <Card>
              <CardHeader><CardTitle className="text-lg">Notes</CardTitle></CardHeader>
              <CardContent>
                <p className="text-sm whitespace-pre-wrap">{creator.notes}</p>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}

function Field({ label, value }: { label: string; value: string | null | undefined }) {
  if (!value) return null;
  return (
    <div>
      <dt className="text-muted-foreground mb-1">{label}</dt>
      <dd className="font-medium">{value}</dd>
    </div>
  );
}
