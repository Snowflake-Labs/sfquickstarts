import Link from 'next/link';

/** Co-branded top bar: Twelve Labs lockup × Snowflake. */
export function AppHeader() {
  return (
    <header className="sticky top-0 z-40 w-full bg-background/70 backdrop-blur-xl">
      <div className="mx-auto flex h-24 w-full max-w-7xl items-center gap-5 px-4 sm:h-32 sm:px-6 lg:px-8">
        <Link href="/" className="flex min-w-0 items-center gap-4 sm:gap-6" aria-label="Home">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/brand/tl-lockup-white.svg" alt="Twelve Labs" className="h-9 w-auto shrink-0 sm:h-12" />
          <span className="text-3xl font-extralight text-ash sm:text-4xl">×</span>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/brand/snowflake-logo.png" alt="Snowflake" className="h-9 w-auto shrink-0 sm:h-12" />
        </Link>
        <span className="tl-pill ml-auto hidden border-border text-muted-foreground md:inline-flex">
          Powered by Snowflake Cortex AI
        </span>
      </div>
      <div className="tl-hairline opacity-70" />
    </header>
  );
}
