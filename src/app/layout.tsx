import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "売上実績ダッシュボード | トヨタモビリティパーツ神奈川支社",
  description: "トヨタ純正部品の日々の売上実績を可視化し、経営分析を支援するダッシュボード",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="antialiased">
        <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 gradient-primary rounded-lg flex items-center justify-center text-white font-bold text-xl">
                  T
                </div>
                <div>
                  <h1 className="text-xl font-bold text-gray-900">売上実績ダッシュボード</h1>
                  <p className="text-sm text-gray-600">トヨタモビリティパーツ神奈川支社</p>
                </div>
              </div>
            </div>
          </div>
        </header>
        <main className="min-h-screen">
          {children}
        </main>
      </body>
    </html>
  );
}
