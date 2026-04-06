import { useState, useRef, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getCreator } from "@/api/creators";
import {
  triggerBrandDiscovery,
  listBrandTargets,
  approveBrand,
  blacklistBrand,
  unblacklistBrand,
  triggerScout,
} from "@/api/brands";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { BrandTarget } from "@/types/brand";

const statusConfig: Record<string, { label: string; className: string; icon?: string }> = {
  suggested: { label: "Suggested", className: "bg-yellow-100 text-yellow-800" },
  approved: { label: "Approved", className: "bg-green-100 text-green-800", icon: "✓" },
  blacklisted: { label: "Blacklisted", className: "bg-red-100 text-red-800" },
};

export default function BrandDiscovery() {
  const { id: creatorId } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [roundFilter, setRoundFilter] = useState<string>("all");
  const [discovering, setDiscovering] = useState(false);
  const brandCountBeforeDiscovery = useRef<number>(0);

  const { data: creator } = useQuery({
    queryKey: ["creator", creatorId],
    queryFn: () => getCreator(creatorId!),
    enabled: !!creatorId,
  });

  const hasScouting = (brands: BrandTarget[]) =>
    brands.some((b) => b.scouting_status === "in_progress");

  const { data: brands = [], isLoading: brandsLoading } = useQuery({
    queryKey: ["brands", creatorId],
    queryFn: () => listBrandTargets(creatorId!),
    enabled: !!creatorId,
    refetchInterval: (query) => {
      if (discovering) return 3000;
      if (query.state.data && hasScouting(query.state.data)) return 3000;
      return false;
    },
  });

  useEffect(() => {
    if (discovering && brands.length > brandCountBeforeDiscovery.current) {
      setDiscovering(false);
    }
  }, [discovering, brands.length]);

  const discoveryRounds = [...new Set(brands.map((b) => b.discovery_round))].sort(
    (a, b) => b - a
  );

  const discoverMutation = useMutation({
    mutationFn: () => triggerBrandDiscovery(creatorId!),
    onSuccess: () => {
      brandCountBeforeDiscovery.current = brands.length;
      setDiscovering(true);
    },
  });

  const approveMutation = useMutation({
    mutationFn: approveBrand,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["brands", creatorId] }),
  });

  const blacklistMutation = useMutation({
    mutationFn: blacklistBrand,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["brands", creatorId] }),
  });

  const unblacklistMutation = useMutation({
    mutationFn: unblacklistBrand,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["brands", creatorId] }),
  });

  const [scoutingBrandIds, setScoutingBrandIds] = useState<Set<string>>(new Set());

  const scoutMutation = useMutation({
    mutationFn: triggerScout,
    onMutate: (brandId: string) => {
      setScoutingBrandIds((prev) => new Set(prev).add(brandId));
    },
    onSettled: (_data, _error, brandId) => {
      setScoutingBrandIds((prev) => {
        const next = new Set(prev);
        next.delete(brandId);
        return next;
      });
      queryClient.invalidateQueries({ queryKey: ["brands", creatorId] });
    },
  });

  const filteredBrands = brands.filter((b) => {
    if (statusFilter !== "all" && b.status !== statusFilter) return false;
    if (roundFilter !== "all" && b.discovery_round !== Number(roundFilter)) return false;
    return true;
  });

  const canDiscover = creator?.enrichment_status === "completed";

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
          <h2 className="text-2xl font-bold">Brand Discovery</h2>
          {creator && (
            <p className="text-muted-foreground mt-1">
              Finding brand partners for {creator.name}
            </p>
          )}
        </div>
        <Button
          onClick={() => discoverMutation.mutate()}
          disabled={discoverMutation.isPending || discovering || !canDiscover}
        >
          {discoverMutation.isPending || discovering ? (
            <span className="flex items-center gap-2">
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
              Discovering...
            </span>
          ) : (
            `Discover Brands${brands.length > 0 ? " (New Round)" : ""}`
          )}
        </Button>
      </div>

      {!canDiscover && (
        <Card className="mb-6 border-yellow-200 bg-yellow-50">
          <CardContent className="pt-6">
            <p className="text-sm text-yellow-800">
              Brand discovery requires a completed creator enrichment profile.
              {creator?.enrichment_status === "failed"
                ? " Enrichment failed — please re-enrich the creator first."
                : creator?.enrichment_status === "pending" ||
                    creator?.enrichment_status === "processing"
                  ? " Enrichment is currently in progress..."
                  : " Please enrich the creator profile first."}
            </p>
          </CardContent>
        </Card>
      )}

      {brands.length > 0 && (
        <div className="flex items-center gap-4 mb-6">
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Status:</span>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[140px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                <SelectItem value="suggested">Suggested</SelectItem>
                <SelectItem value="approved">Approved</SelectItem>
                <SelectItem value="blacklisted">Blacklisted</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Round:</span>
            <Select value={roundFilter} onValueChange={setRoundFilter}>
              <SelectTrigger className="w-[120px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                {discoveryRounds.map((r) => (
                  <SelectItem key={r} value={String(r)}>
                    Round {r}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <span className="text-sm text-muted-foreground ml-auto">
            {filteredBrands.length} brand{filteredBrands.length !== 1 ? "s" : ""}
          </span>
        </div>
      )}

      {brandsLoading ? (
        <p className="text-muted-foreground">Loading brands...</p>
      ) : brands.length === 0 ? (
        <Card>
          <CardContent className="pt-6 text-center">
            <p className="text-muted-foreground mb-2">
              No brand suggestions yet.
            </p>
            <p className="text-sm text-muted-foreground">
              Click "Discover Brands" to let AI find ideal brand partners for this
              creator.
            </p>
          </CardContent>
        </Card>
      ) : filteredBrands.length === 0 ? (
        <p className="text-muted-foreground">
          No brands match the current filters.
        </p>
      ) : (
        <div className="space-y-4">
          {filteredBrands.map((brand) => (
            <BrandCard
              key={brand.id}
              brand={brand}
              onApprove={() => approveMutation.mutate(brand.id)}
              onBlacklist={() => blacklistMutation.mutate(brand.id)}
              onUnblacklist={() => unblacklistMutation.mutate(brand.id)}
              onScout={() => scoutMutation.mutate(brand.id)}
              onViewContacts={() => navigate(`/creators/${creatorId}/brands/${brand.id}/contacts`)}
              isUpdating={
                approveMutation.isPending ||
                blacklistMutation.isPending ||
                unblacklistMutation.isPending
              }
              isScouting={scoutingBrandIds.has(brand.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

const scoutingConfig: Record<string, { label: string; className: string }> = {
  not_started: { label: "Not Scouted", className: "bg-gray-100 text-gray-600" },
  in_progress: { label: "Scouting...", className: "bg-blue-100 text-blue-700" },
  completed: { label: "Scouted", className: "bg-emerald-100 text-emerald-700" },
  failed: { label: "Scout Failed", className: "bg-red-100 text-red-700" },
};

function BrandCard({
  brand,
  onApprove,
  onBlacklist,
  onUnblacklist,
  onScout,
  onViewContacts,
  isUpdating,
  isScouting,
}: {
  brand: BrandTarget;
  onApprove: () => void;
  onBlacklist: () => void;
  onUnblacklist: () => void;
  onScout: () => void;
  onViewContacts: () => void;
  isUpdating: boolean;
  isScouting: boolean;
}) {
  const config = statusConfig[brand.status] || statusConfig.suggested;
  const scoutCfg = brand.scouting_status
    ? scoutingConfig[brand.scouting_status] || scoutingConfig.not_started
    : null;

  return (
    <Card
      className={
        brand.status === "blacklisted"
          ? "opacity-60"
          : brand.status === "approved"
            ? "border-l-4 border-l-green-500 bg-green-50/30"
            : undefined
      }
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-3 flex-wrap">
              <CardTitle className="text-base">{brand.company_name}</CardTitle>
              <Badge variant="outline" className={config.className}>
                {config.icon && <span className="mr-1">{config.icon}</span>}
                {config.label}
              </Badge>
              {scoutCfg && (
                <Badge variant="outline" className={scoutCfg.className}>
                  {brand.scouting_status === "in_progress" && (
                    <span className="h-3 w-3 mr-1.5 animate-spin rounded-full border-2 border-current border-t-transparent inline-block" />
                  )}
                  {scoutCfg.label}
                </Badge>
              )}
              <Badge variant="secondary" className="text-xs">
                Round {brand.discovery_round}
              </Badge>
            </div>
            {brand.company_domain && (
              <a
                href={`https://${brand.company_domain}`}
                target="_blank"
                rel="noreferrer"
                className="text-sm text-primary hover:underline mt-1 inline-block"
              >
                {brand.company_domain}
              </a>
            )}
          </div>
          <div className="flex items-center gap-2 ml-4 shrink-0">
            {brand.status === "suggested" && (
              <>
                <Button
                  size="sm"
                  onClick={onApprove}
                  disabled={isUpdating}
                >
                  Approve
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  className="text-red-600 hover:text-red-700 hover:bg-red-50"
                  onClick={onBlacklist}
                  disabled={isUpdating}
                >
                  Blacklist
                </Button>
              </>
            )}
            {brand.status === "approved" && (
              <>
                {(!brand.scouting_status || brand.scouting_status === "not_started" || brand.scouting_status === "failed") && (
                  <Button
                    size="sm"
                    onClick={onScout}
                    disabled={isScouting}
                  >
                    {brand.scouting_status === "failed" ? "Retry Scout" : "Scout Contacts"}
                  </Button>
                )}
                {brand.scouting_status === "completed" && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={onViewContacts}
                  >
                    View Contacts
                  </Button>
                )}
                <Button
                  size="sm"
                  variant="outline"
                  className="text-red-600 hover:text-red-700 hover:bg-red-50"
                  onClick={onBlacklist}
                  disabled={isUpdating}
                >
                  Blacklist
                </Button>
              </>
            )}
            {brand.status === "blacklisted" && (
              <Button
                size="sm"
                variant="outline"
                onClick={onUnblacklist}
                disabled={isUpdating}
              >
                Undo Blacklist
              </Button>
            )}
          </div>
        </div>
      </CardHeader>
      {brand.reasoning && (
        <CardContent className="pt-0">
          <p className="text-sm text-muted-foreground">{brand.reasoning}</p>
        </CardContent>
      )}
    </Card>
  );
}
