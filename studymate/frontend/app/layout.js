import "./globals.css";
export const metadata = { title: "StudyMate", description: "Source-cited AI study companion" };
export default function RootLayout({ children }) {
  return (<html lang="en"><body>{children}</body></html>);
}
