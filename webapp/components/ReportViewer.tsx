interface ReportViewerProps {
  url: string;
  title: string;
}

export default function ReportViewer({ url, title }: ReportViewerProps) {
  return (
    <>
      <title>{title}</title>
      <iframe
        src={url}
        title={title}
        style={{ width: '100%', height: '100vh', border: 'none' }}
      />
    </>
  );
}
