import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'QA Report Platform',
};

export default function HomePage() {
  return (
    <main
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        gap: '1rem',
        padding: '2rem',
      }}
    >
      <h1 style={{ fontSize: '2rem', fontWeight: 700 }}>QA Report Platform</h1>
      <p style={{ color: '#555', maxWidth: 480, textAlign: 'center' }}>
        Share and collaborate on QA test reports. Open a report link to view bug
        summaries, add notes, and track resolution status.
      </p>
    </main>
  );
}
