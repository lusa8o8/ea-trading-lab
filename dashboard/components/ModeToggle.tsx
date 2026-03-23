import type { Mode } from '@/lib/supabase'

export default function ModeToggle({
  mode,
  onChange,
}: {
  mode: Mode
  onChange: (m: Mode) => void
}) {
  const isLive = mode === 'LIVE'

  return (
    <div className="bg-card border border-line rounded p-4 sm:p-5">
      <div className="flex items-start gap-4 sm:gap-6 flex-wrap">
        {/* LIVE side */}
        <button
          onClick={() => onChange('LIVE')}
          className="flex flex-col gap-1.5 text-left focus:outline-none group"
        >
          <div className="flex items-center gap-2">
            {isLive ? (
              <span className="relative flex h-2.5 w-2.5 shrink-0">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-positive opacity-60" />
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-positive" />
              </span>
            ) : (
              <span className="h-2.5 w-2.5 rounded-full bg-[#333] shrink-0" />
            )}
            <span
              className={`font-mono text-sm font-bold tracking-widest transition-colors ${
                isLive ? 'text-positive' : 'text-muted group-hover:text-[#888]'
              }`}
            >
              LIVE
            </span>
          </div>
          <p className={`text-xs font-mono pl-4 transition-colors ${isLive ? 'text-muted' : 'text-[#444]'}`}>
            Starting from zero. No backtest padding.
          </p>
        </button>

        {/* Toggle pill */}
        <button
          onClick={() => onChange(isLive ? 'BACKTEST' : 'LIVE')}
          className={`relative inline-flex items-center rounded-full transition-colors duration-200 focus:outline-none mt-0.5 flex-shrink-0 ${
            isLive ? 'bg-green-500' : 'bg-gray-600'
          }`}
          style={{ width: '44px', height: '24px', padding: '2px' }}
          aria-label="Toggle data mode"
        >
          <span
            className="inline-block rounded-full bg-white transition-transform duration-200"
            style={{
              width: '20px',
              height: '20px',
              transform: isLive ? 'translateX(20px)' : 'translateX(0px)',
            }}
          />
        </button>

        {/* BACKTEST side */}
        <button
          onClick={() => onChange('BACKTEST')}
          className="flex flex-col gap-1.5 text-left focus:outline-none group"
        >
          <div className="flex items-center gap-2">
            <span
              className={`font-mono text-sm font-bold tracking-widest transition-colors ${
                !isLive ? 'text-white' : 'text-muted group-hover:text-[#888]'
              }`}
            >
              BACKTEST
            </span>
            <span
              className={`h-2.5 w-2.5 rounded-full shrink-0 ${!isLive ? 'bg-[#888]' : 'bg-[#333]'}`}
            />
          </div>
          <p className={`text-xs font-mono transition-colors ${!isLive ? 'text-muted' : 'text-[#444]'}`}>
            484 trades | Jan 2023 – Mar 2026
          </p>
        </button>
      </div>
    </div>
  )
}
