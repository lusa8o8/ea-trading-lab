export default function Header({ hasAlert }: { hasAlert: boolean }) {
  return (
    <header className="flex items-start justify-between flex-wrap gap-4">
      <div>
        <h1 className="font-mono text-2xl font-bold text-white tracking-tight">
          EA Trading Lab
        </h1>
        <p className="text-muted text-sm mt-1">
          An algorithmic forex system being validated in public.
        </p>
      </div>
      <div className="mt-1">
        {hasAlert ? (
          <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded text-xs font-mono bg-yellow-950 text-yellow-400 border border-yellow-800">
            <span className="w-1.5 h-1.5 rounded-full bg-yellow-400 shrink-0" />
            Active alert
          </span>
        ) : (
          <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded text-xs font-mono bg-positive/10 text-positive border border-positive/30">
            <span className="w-1.5 h-1.5 rounded-full bg-positive shrink-0" />
            All systems normal
          </span>
        )}
      </div>
    </header>
  )
}
