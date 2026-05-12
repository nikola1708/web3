import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Bunny — Digital Receipt for Writers',
  description: 'Prove your manuscript is human-authored with a tamper-proof digital receipt. No crypto knowledge required.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Playfair+Display:ital,wght@0,500;0,700;1,500&display=swap" rel="stylesheet" />
      </head>
      <body>{children}</body>
    </html>
  );
}
