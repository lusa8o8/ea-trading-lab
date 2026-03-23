export default function Footer({ lastUpdated }: { lastUpdated: string }) {
  const formatted = new Date(lastUpdated).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    timeZoneName: 'short',
  })

  return (
    <footer className="border-t border-line pt-6 pb-10 flex flex-wrap items-center justify-between gap-4">
      <span className="text-xs font-mono text-muted">
        Built with data. Validated in public.
      </span>
      <div className="flex items-center gap-5 text-xs font-mono text-muted">
        <span>Updated {formatted}</span>
        <a
          href="https://github.com/lusa8o8/ea-trading-lab"
          target="_blank"
          rel="noopener noreferrer"
          className="hover:text-[#e5e5e5] transition-colors duration-150"
        >
          GitHub →
        </a>
      </div>
    </footer>
  )
}
