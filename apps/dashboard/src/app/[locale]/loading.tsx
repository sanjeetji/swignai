// Shown automatically while a route segment fetches data (SSR) or during navigation,
// so the screen never looks frozen. Branded spinner.
export default function Loading() {
  return (
    <div className="grid min-h-screen place-items-center bg-background text-foreground">
      <div className="flex flex-col items-center gap-3">
        <div className="grid h-10 w-10 place-items-center rounded-xl bg-primary font-bold text-primary-foreground">S</div>
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-muted border-t-primary" />
        <p className="text-sm text-muted-foreground">Loading…</p>
      </div>
    </div>
  );
}
