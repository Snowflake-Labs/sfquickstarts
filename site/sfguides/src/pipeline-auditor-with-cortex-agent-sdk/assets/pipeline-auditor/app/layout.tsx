import type { Metadata } from "next"
import type React from "react"

export const metadata: Metadata = {
  title: "Pipeline Auditor",
  description: "AI-powered pipeline health analysis for Snowflake",
  icons: { icon: "/icon.svg" },
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        {children}
      </body>
    </html>
  )
}
