export default function NotFound() {
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
      <h2 style={{ fontSize: '1.5rem', fontWeight: 600 }}>404 - Page Not Found</h2>
      <p style={{ color: '#666' }}>The page you are looking for does not exist.</p>
      <a href="/" style={{ color: '#0070f3', marginTop: '1rem' }}>
        Go back home
      </a>
    </main>
  );
}
