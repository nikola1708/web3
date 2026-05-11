import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Bunny - Digital Heartbeat for Writers',
  description: 'Decentralized attestation layer for novelists. Prove your work is human-authored.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
