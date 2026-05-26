'use client';

import { useEffect, useRef } from 'react';

interface ReportViewerProps {
  html: string;
  title: string;
}

export default function ReportViewer({ html, title }: ReportViewerProps) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Re-execute inline scripts injected by adaptHtml, because
    // dangerouslySetInnerHTML does not run script tags automatically.
    if (!ref.current) return;
    ref.current.querySelectorAll('script').forEach((oldScript) => {
      const newScript = document.createElement('script');
      if (oldScript.src) {
        newScript.src = oldScript.src;
      } else {
        newScript.textContent = oldScript.textContent;
      }
      oldScript.replaceWith(newScript);
    });
  }, [html]);

  return (
    <>
      <title>{title}</title>
      <div ref={ref} dangerouslySetInnerHTML={{ __html: html }} />
    </>
  );
}
