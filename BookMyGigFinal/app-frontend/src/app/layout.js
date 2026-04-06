import localFont from "next/font/local";
import "./globals.css";

export const metadata = {
  title: "BookMyGig | AI-Powered Platform",
  description: "UK Music Booking Platform powered by 5 ML Models",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <div className="bg-glow" />
        <main>
          {children}
        </main>
      </body>
    </html>
  );
}
