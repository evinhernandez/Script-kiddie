import "./globals.css";

export const metadata = { title: "Script-kiddie", description: "AI governance + guardrails platform" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="max-w-6xl mx-auto p-6">
          <header className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <img
                src="/logo.png"
                alt="Script-kiddie logo"
                className="h-11 w-11 rounded-xl border border-zinc-800 bg-zinc-950 object-cover"
              />
              <div>
                <h1 className="text-2xl font-bold">Script-kiddie</h1>
                <p className="text-zinc-400">Rules + Ollama judges + policy-as-code</p>
              </div>
            </div>
            <nav className="flex gap-4 text-sm">
              <a href="/">Dashboard</a>
              <a href="/jobs">Jobs</a>
              <a href="/snippets">Snippets</a>
            </nav>
          </header>
          {children}
          <footer className="mt-10 text-xs text-zinc-500">
            Apache-2.0 • MVP
          </footer>
        </div>
      </body>
    </html>
  );
}
