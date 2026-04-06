import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { listCreators } from "@/api/creators";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

const statusColors: Record<string, string> = {
  draft: "bg-yellow-100 text-yellow-800",
  reviewed: "bg-blue-100 text-blue-800",
  active: "bg-green-100 text-green-800",
};

const enrichmentColors: Record<string, string> = {
  pending: "bg-gray-100 text-gray-600",
  processing: "bg-purple-100 text-purple-800",
  completed: "bg-green-100 text-green-800",
  failed: "bg-red-100 text-red-800",
};

export default function CreatorList() {
  const { data: creators, isLoading } = useQuery({
    queryKey: ["creators"],
    queryFn: listCreators,
  });

  if (isLoading) {
    return <div className="text-muted-foreground">Loading creators...</div>;
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">Creators</h2>
        <Link to="/creators/new">
          <Button>Add Creator</Button>
        </Link>
      </div>

      {!creators?.length ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            No creators yet. Add your first creator to get started.
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {creators.map((creator) => (
            <Link key={creator.id} to={`/creators/${creator.id}`}>
              <Card className="hover:border-primary/50 transition-colors cursor-pointer">
                <CardContent className="flex items-center justify-between py-4">
                  <div className="space-y-1">
                    <div className="font-semibold text-lg">{creator.name}</div>
                    <div className="flex items-center gap-3 text-sm text-muted-foreground">
                      {creator.niche && <span>{creator.niche}</span>}
                      {creator.audience_size_approx && (
                        <span>{creator.audience_size_approx} followers</span>
                      )}
                      {creator.instagram_handle && (
                        <span>{creator.instagram_handle}</span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className={enrichmentColors[creator.enrichment_status] || ""}>
                      {creator.enrichment_status}
                    </Badge>
                    <Badge variant="outline" className={statusColors[creator.profile_status] || ""}>
                      {creator.profile_status}
                    </Badge>
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
