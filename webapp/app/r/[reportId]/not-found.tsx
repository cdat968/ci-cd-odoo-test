export default function ReportNotFound() {
  return (
    <main
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        gap: '0.5rem',
      }}
    >
      <h2 style={{ fontSize: '1.5rem', fontWeight: 600 }}>Report Not Found</h2>
      <p style={{ color: '#666' }}>
        The report link is invalid or has expired. Please check your link and try again.
      </p>
      <a href="/" style={{ color: '#0070f3', marginTop: '1rem' }}>
        Go back home
      </a>
    </main>
  );
}
