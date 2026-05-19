import './globals.css';

export const metadata = {
  title: 'Hobbyt – AI-Powered Robotics Intelligence',
  description: 'Understand robotics codebases instantly and generate starter kits, wiring diagrams, and documentation with Google Gemini AI.',
};

export const viewport = {
  width: 'device-width',
  initialScale: 1.0,
  themeColor: '#e6ebf4',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        {children}
      </body>
    </html>
  );
}
