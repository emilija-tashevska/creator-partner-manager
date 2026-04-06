import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
import { getCreator } from "@/api/creators";
import { listCreatorContacts } from "@/api/contacts";
import { listBrandTargets } from "@/api/brands";
import { triggerDraftEmails } from "@/api/emails";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ContactWithBrands } from "@/types/contact";
import type { BrandTarget } from "@/types/brand";

export default function CreatorContacts() {
  const { id: creatorId } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [brandFilter, setBrandFilter] = useState<string>("all");

  const { data: creator } = useQuery({
    queryKey: ["creator", creatorId],
    queryFn: () => getCreator(creatorId!),
    enabled: !!creatorId,
  });

  const { data: contacts = [], isLoading } = useQuery({
    queryKey: ["creatorContacts", creatorId],
    queryFn: () => listCreatorContacts(creatorId!),
    enabled: !!creatorId,
  });

  const { data: brands = [] } = useQuery({
    queryKey: ["brands", creatorId],
    queryFn: () => listBrandTargets(creatorId!),
    enabled: !!creatorId,
  });

  const scoutedBrands = brands.filter(
    (b) => b.scouting_status === "completed"
  );

  const brandNameMap = new Map<string, BrandTarget>();
  for (const b of brands) brandNameMap.set(b.company_name, b);

  const filteredContacts =
    brandFilter === "all"
      ? contacts
      : contacts.filter((c) => c.brand_names.includes(brandFilter));

  const draftMutation = useMutation({
    mutationFn: () => {
      const firstContact = contacts.find((c) => selected.has(c.id));
      const brandName = firstContact?.brand_names[0];
      const brand = brandName ? brandNameMap.get(brandName) : undefined;
      return triggerDraftEmails({
        contact_ids: Array.from(selected),
        creator_id: creatorId!,
        brand_target_id: brand?.id ?? "",
      });
    },
    onSuccess: () => {
      const pendingDrafts = contacts
        .filter((c) => selected.has(c.id))
        .map((c) => ({
          contactName: c.full_name,
          contactEmail: c.email,
          brandName: c.brand_names[0] ?? null,
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
    if (selected.size === filteredContacts.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(filteredContacts.map((c) => c.id)));
    }
  }

  const allBrandNames = [...new Set(contacts.flatMap((c) => c.brand_names))].sort();

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
          <h2 className="text-2xl font-bold">Scouted Contacts</h2>
          {creator && (
            <p className="text-muted-foreground mt-1">
              All contacts found for {creator.name} across {scoutedBrands.length} scouted brand{scoutedBrands.length !== 1 ? "s" : ""}
            </p>
          )}
        </div>
        {filteredContacts.length > 0 && (
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

      {allBrandNames.length > 1 && (
        <div className="flex items-center gap-2 mb-6 flex-wrap">
          <span className="text-sm text-muted-foreground">Filter by brand:</span>
          <Button
            size="sm"
            variant={brandFilter === "all" ? "default" : "outline"}
            onClick={() => setBrandFilter("all")}
          >
            All ({contacts.length})
          </Button>
          {allBrandNames.map((name) => {
            const count = contacts.filter((c) => c.brand_names.includes(name)).length;
            return (
              <Button
                key={name}
                size="sm"
                variant={brandFilter === name ? "default" : "outline"}
                onClick={() => setBrandFilter(name)}
              >
                {name} ({count})
              </Button>
            );
          })}
        </div>
      )}

      {isLoading ? (
        <p className="text-muted-foreground">Loading contacts...</p>
      ) : contacts.length === 0 ? (
        <Card>
          <CardContent className="pt-6 text-center">
            <p className="text-muted-foreground mb-2">No scouted contacts yet.</p>
            <p className="text-sm text-muted-foreground mb-4">
              Approve brands in Brand Discovery, then scout them to find contacts.
            </p>
            <Button
              variant="outline"
              onClick={() => navigate(`/creators/${creatorId}/brands`)}
            >
              Go to Brand Discovery
            </Button>
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
                  selected.size === filteredContacts.length && filteredContacts.length > 0
                    ? "bg-primary border-primary text-primary-foreground"
                    : "border-muted-foreground"
                }`}
              >
                {selected.size === filteredContacts.length && filteredContacts.length > 0 && "✓"}
              </span>
              {selected.size === filteredContacts.length && filteredContacts.length > 0
                ? "Deselect all"
                : "Select all"}
            </button>
            {selected.size > 0 && (
              <span className="text-sm text-muted-foreground">
                {selected.size} of {filteredContacts.length} selected
              </span>
            )}
          </div>
          <div className="space-y-3">
            {filteredContacts.map((contact) => (
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
  contact: ContactWithBrands;
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
          <div className="flex items-center gap-2 flex-wrap justify-end">
            {contact.has_conflict && (
              <Badge variant="outline" className="bg-yellow-100 text-yellow-800">
                Conflict
              </Badge>
            )}
            {contact.brand_names.map((name) => (
              <Badge key={name} variant="secondary">
                {name}
              </Badge>
            ))}
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
