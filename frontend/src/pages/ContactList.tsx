import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
import { getCreator } from "@/api/creators";
import { listBrandContacts } from "@/api/contacts";
import { listBrandTargets } from "@/api/brands";
import { triggerDraftEmails } from "@/api/emails";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Contact } from "@/types/contact";

export default function ContactList() {
  const { id: creatorId, brandId } = useParams<{ id: string; brandId: string }>();
  const navigate = useNavigate();
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const { data: creator } = useQuery({
    queryKey: ["creator", creatorId],
    queryFn: () => getCreator(creatorId!),
    enabled: !!creatorId,
  });

  const { data: brands = [] } = useQuery({
    queryKey: ["brands", creatorId],
    queryFn: () => listBrandTargets(creatorId!),
    enabled: !!creatorId,
  });

  const brand = brands.find((b) => b.id === brandId);

  const { data: contacts = [], isLoading } = useQuery({
    queryKey: ["contacts", brandId],
    queryFn: () => listBrandContacts(brandId!),
    enabled: !!brandId,
  });

  const draftMutation = useMutation({
    mutationFn: () =>
      triggerDraftEmails({
        contact_ids: Array.from(selected),
        creator_id: creatorId!,
        brand_target_id: brandId!,
      }),
    onSuccess: () => {
      const pendingDrafts = contacts
        .filter((c) => selected.has(c.id))
        .map((c) => ({
          contactName: c.full_name,
          contactEmail: c.email,
          brandName: brand?.company_name ?? null,
        }));
      navigate(`/creators/${creatorId}/emails`, {
        state: { pendingDrafts },
      });
    },
  });

  function toggleContact(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function toggleAll() {
    if (selected.size === contacts.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(contacts.map((c) => c.id)));
    }
  }

  return (
    <div className="max-w-4xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <Button
            variant="ghost"
            className="mb-2 -ml-3"
            onClick={() => navigate(`/creators/${creatorId}/brands`)}
          >
            &larr; Back to Brand Discovery
          </Button>
          <h2 className="text-2xl font-bold">
            Contacts{brand ? ` at ${brand.company_name}` : ""}
          </h2>
          {creator && (
            <p className="text-muted-foreground mt-1">
              Scouted contacts for {creator.name}
            </p>
          )}
        </div>
        {contacts.length > 0 && (
          <Button
            onClick={() => draftMutation.mutate()}
            disabled={selected.size === 0 || draftMutation.isPending}
          >
            {draftMutation.isPending ? (
              <span className="flex items-center gap-2">
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                Drafting...
              </span>
            ) : (
              `Draft Emails (${selected.size})`
            )}
          </Button>
        )}
      </div>

      {isLoading ? (
        <p className="text-muted-foreground">Loading contacts...</p>
      ) : contacts.length === 0 ? (
        <Card>
          <CardContent className="pt-6 text-center">
            <p className="text-muted-foreground">
              No contacts found for this brand. Try scouting again or check that
              the brand has a valid domain.
            </p>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="flex items-center gap-3 mb-4">
            <button
              type="button"
              onClick={toggleAll}
              className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              <span
                className={`h-4 w-4 rounded border flex items-center justify-center text-xs ${
                  selected.size === contacts.length
                    ? "bg-primary border-primary text-primary-foreground"
                    : "border-muted-foreground"
                }`}
              >
                {selected.size === contacts.length && "✓"}
              </span>
              {selected.size === contacts.length ? "Deselect all" : "Select all"}
            </button>
            {selected.size > 0 && (
              <span className="text-sm text-muted-foreground">
                {selected.size} of {contacts.length} selected
              </span>
            )}
          </div>
          <div className="space-y-3">
            {contacts.map((contact) => (
              <ContactCard
                key={contact.id}
                contact={contact}
                isSelected={selected.has(contact.id)}
                onToggle={() => toggleContact(contact.id)}
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
}

function ContactCard({
  contact,
  isSelected,
  onToggle,
}: {
  contact: Contact;
  isSelected: boolean;
  onToggle: () => void;
}) {
  return (
    <Card
      className={`cursor-pointer transition-colors ${
        contact.has_conflict
          ? "border-yellow-300"
          : isSelected
            ? "border-primary ring-1 ring-primary"
            : "hover:border-muted-foreground/30"
      }`}
      onClick={onToggle}
    >
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span
              className={`h-5 w-5 rounded border flex items-center justify-center text-xs shrink-0 ${
                isSelected
                  ? "bg-primary border-primary text-primary-foreground"
                  : "border-muted-foreground"
              }`}
            >
              {isSelected && "✓"}
            </span>
            <div>
              <CardTitle className="text-base">{contact.full_name}</CardTitle>
              {contact.title && (
                <p className="text-sm text-muted-foreground">{contact.title}</p>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2">
            {contact.has_conflict && (
              <Badge variant="outline" className="bg-yellow-100 text-yellow-800">
                Conflict
              </Badge>
            )}
            {contact.company_name && (
              <Badge variant="secondary">{contact.company_name}</Badge>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-0 pl-11">
        <div className="flex items-center gap-6 text-sm">
          <span className="text-primary">{contact.email}</span>
          {contact.linkedin_url && (
            <a
              href={contact.linkedin_url}
              target="_blank"
              rel="noreferrer"
              className="text-primary hover:underline"
              onClick={(e) => e.stopPropagation()}
            >
              LinkedIn
            </a>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
