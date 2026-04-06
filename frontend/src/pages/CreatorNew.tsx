import { useState, useRef, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createCreator } from "@/api/creators";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { CreatorCreate } from "@/types/creator";

export default function CreatorNew() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [mediaKitFile, setMediaKitFile] = useState<File | null>(null);

  const [form, setForm] = useState<CreatorCreate>({
    name: "",
    instagram_handle: "",
    tiktok_handle: "",
    youtube_handle: "",
    x_handle: "",
    niche: "",
    audience_size_approx: "",
    notes: "",
  });

  const mutation = useMutation({
    mutationFn: createCreator,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["creators"] });
      navigate(`/creators/${data.id}`, {
        state: mediaKitFile ? { pendingMediaKit: true } : undefined,
      });
    },
  });

  function update(field: keyof CreatorCreate, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const cleaned: CreatorCreate = { name: form.name };
    if (form.instagram_handle) cleaned.instagram_handle = form.instagram_handle;
    if (form.tiktok_handle) cleaned.tiktok_handle = form.tiktok_handle;
    if (form.youtube_handle) cleaned.youtube_handle = form.youtube_handle;
    if (form.x_handle) cleaned.x_handle = form.x_handle;
    if (form.niche) cleaned.niche = form.niche;
    if (form.audience_size_approx) cleaned.audience_size_approx = form.audience_size_approx;
    if (form.notes) cleaned.notes = form.notes;
    mutation.mutate(cleaned);
  }

  return (
    <div className="max-w-2xl">
      <h2 className="text-2xl font-bold mb-6">Add Creator</h2>

      <form onSubmit={handleSubmit} className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Basic Info</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Name *</Label>
              <Input
                id="name"
                value={form.name}
                onChange={(e) => update("name", e.target.value)}
                placeholder="Creator's name"
                required
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="niche">Niche / Category</Label>
                <Input
                  id="niche"
                  value={form.niche || ""}
                  onChange={(e) => update("niche", e.target.value)}
                  placeholder="e.g. fitness, beauty, tech"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="audience">Approx. Audience Size</Label>
                <Input
                  id="audience"
                  value={form.audience_size_approx || ""}
                  onChange={(e) => update("audience_size_approx", e.target.value)}
                  placeholder="e.g. 250K"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Social Handles</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="instagram">Instagram</Label>
                <Input
                  id="instagram"
                  value={form.instagram_handle || ""}
                  onChange={(e) => update("instagram_handle", e.target.value)}
                  placeholder="@handle"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="tiktok">TikTok</Label>
                <Input
                  id="tiktok"
                  value={form.tiktok_handle || ""}
                  onChange={(e) => update("tiktok_handle", e.target.value)}
                  placeholder="@handle"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="youtube">YouTube</Label>
                <Input
                  id="youtube"
                  value={form.youtube_handle || ""}
                  onChange={(e) => update("youtube_handle", e.target.value)}
                  placeholder="@channel"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="x">X / Twitter</Label>
                <Input
                  id="x"
                  value={form.x_handle || ""}
                  onChange={(e) => update("x_handle", e.target.value)}
                  placeholder="@handle"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Additional</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="media_kit">Media Kit (PDF)</Label>
              <div className="flex items-center gap-3">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => fileInputRef.current?.click()}
                >
                  {mediaKitFile ? "Change file" : "Choose PDF"}
                </Button>
                {mediaKitFile && (
                  <span className="text-sm text-muted-foreground truncate max-w-xs">
                    {mediaKitFile.name}
                  </span>
                )}
                {mediaKitFile && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="text-destructive"
                    onClick={() => {
                      setMediaKitFile(null);
                      if (fileInputRef.current) fileInputRef.current.value = "";
                    }}
                  >
                    Remove
                  </Button>
                )}
              </div>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf"
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) setMediaKitFile(file);
                }}
              />
              <p className="text-xs text-muted-foreground">
                PDF only. You can also upload or replace this later.
              </p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="notes">Notes</Label>
              <Textarea
                id="notes"
                value={form.notes || ""}
                onChange={(e) => update("notes", e.target.value)}
                placeholder="Any additional notes about this creator..."
                rows={3}
              />
            </div>
          </CardContent>
        </Card>

        {mutation.error && (
          <div className="rounded-md bg-destructive/10 px-4 py-3 text-sm text-destructive">
            {(mutation.error as Error).message}
          </div>
        )}

        <div className="flex gap-3">
          <Button type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? "Creating..." : "Create Creator"}
          </Button>
          <Button type="button" variant="outline" onClick={() => navigate("/creators")}>
            Cancel
          </Button>
        </div>
      </form>
    </div>
  );
}
