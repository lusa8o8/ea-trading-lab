export default function ContextSection() {
  return (
    <section className="border-t border-line pt-10">
      <h2 className="text-xs font-mono uppercase tracking-widest text-muted mb-5">
        What is this?
      </h2>
      <div className="max-w-2xl space-y-4">
        <p className="text-[#e5e5e5] text-sm leading-relaxed">
          EA Trading Lab is a rules-based algorithmic trading system running on four forex pairs.
          Every trade is logged automatically to a database the moment it closes. Nothing is edited.
          Nothing is hidden. This dashboard updates in real time.
        </p>
        <p className="text-[#e5e5e5] text-sm leading-relaxed">
          The system is currently in paper trading validation. The backtest covers 3 years and 484
          trades. Live trading began in March 2026.
        </p>
        <p className="text-[#e5e5e5] text-sm leading-relaxed">
          The system runs fully automated across four currency pairs. Risk is managed
          algorithmically on every trade.
        </p>
        <p className="text-muted text-sm leading-relaxed">
          No profit guarantees. No hype. Just data.
        </p>
      </div>
    </section>
  )
}
