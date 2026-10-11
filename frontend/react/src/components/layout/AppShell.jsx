export function AppShell({ children }) {
  return (
    <div className="app-shell">
      <header className="site-header">
        <a className="brand" href="/" aria-label="ClearMed AI home">
          <span className="brand-mark" aria-hidden="true">✦</span>
          <span>ClearMed AI</span>
        </a>
        <p className="header-status"><span className="status-dot" />Private, plain-language support</p>
      </header>
      <main>{children}</main>
      <footer className="site-footer">
        ClearMed AI provides educational information, not medical advice, diagnosis, or emergency care.
      </footer>
    </div>
  );
}
