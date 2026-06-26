// Route-level loading UI — shown while a page fetches CMS/API data so it never looks frozen.
export default function Loading() {
  return (
    <div className="grid min-h-[60vh] place-items-center bg-background text-foreground">
      <div className="flex flex-col items-center gap-3">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-muted border-t-primary" />
        <p className="text-sm text-muted-foreground">Loading…</p>
      </div>
    </div>
  );
}
