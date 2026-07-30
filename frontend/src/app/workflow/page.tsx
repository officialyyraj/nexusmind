"use client";

import { WorkflowPage } from "@/components/workflow";
import { AppShell } from "@/components/layout/app-shell";

export default function Workflow() {
  return (
    <AppShell>
      <WorkflowPage className="flex-1" />
    </AppShell>
  );
}
