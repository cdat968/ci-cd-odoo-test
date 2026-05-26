'use client';

interface ReportViewerProps {
  html: string;
  title: string;
}

export default function ReportViewer({ html, title }: ReportViewerProps) {
  return (
    <>
      <title>{title}</title>
      <iframe
        srcdoc={html}
        title={title}
        style={{ width: '100%', height: '100vh', border: 'none' }}
      />
    </>
  );
}
