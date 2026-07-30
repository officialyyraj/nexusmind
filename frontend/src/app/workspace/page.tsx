"use client";

import { Workspace } from "@/components/workspace";
import { AppShell } from "@/components/layout/app-shell";

export default function WorkspacePage() {
  return (
    <AppShell>
      <Workspace className="flex-1" />
    </AppShell>
  );
}
