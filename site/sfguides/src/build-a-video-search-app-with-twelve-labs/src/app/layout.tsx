import { AppHeader } from '@/components/app-header';
import { QueryProvider } from '@/components/query-provider';
import { ThemeProvider } from '@/components/theme-provider';
import { APP_TITLE, LOGO_SRC } from '@/lib/constants';
import type { Metadata } from 'next';
import type React from 'react';
import './globals.css';

export const metadata: Metadata = {
  title: `${APP_TITLE} · Snowflake × Twelve Labs`,
  description: 'Search and understand video with Twelve Labs Marengo and Pegasus, natively on Snowflake Cortex.',
  icons: { icon: LOGO_SRC },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body className="min-h-screen antialiased">
        <ThemeProvider>
          <QueryProvider>
            <AppHeader />
            {children}
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
