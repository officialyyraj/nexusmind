"use client";
import { Button } from "@/components/ui/button";
import { User, Key, Plug, Moon } from "lucide-react";
import Link from "next/link";

const items = [
  { icon: User, label: "Profile", href: "/settings/profile" },
  { icon: Key, label: "API Keys", href: "/settings/keys" },
  { icon: Plug, label: "Plugins", href: "/settings/plugins" },
  { icon: Moon, label: "Appearance", href: "/settings/appearance" },
];

export function SettingsList() {
  return (
    <div className="space-y-1 p-2">
      {items.map((item) => (
        <Link key={item.href} href={item.href}>
          <Button variant="ghost" className="w-full justify-start">
            <item.icon className="h-4 w-4 mr-2" />
            {item.label}
          </Button>
        </Link>
      ))}
    </div>
  );
}
