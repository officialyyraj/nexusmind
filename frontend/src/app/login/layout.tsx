import type { Metadata } from "next";

// Login page uses its own minimal layout without auth requirements
export const metadata: Metadata = {
  title: "Sign In - NexusMind",
  description: "Sign in to your NexusMind account",
};

// This layout is intentionally minimal - no auth provider needed for the login page
export default function LoginLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
