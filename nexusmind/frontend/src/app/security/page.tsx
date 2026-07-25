"use client";

import { SecurityDashboard } from "@/components/security";
import { AppShell } from "@/components/layout/app-shell";

export default function SecurityPage() {
  return (
    <AppShell>
      <SecurityDashboard className="flex-1" />
    </AppShell>
  );
}
