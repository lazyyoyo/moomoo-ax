"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/live", label: "Live", icon: "📡" },
  { href: "/north-star", label: "North Star", icon: "🎯" },
  { href: "/levelup", label: "Levelup", icon: "🔬" },
  { href: "/projects", label: "Projects", icon: "📁" },
  { href: "/feedback", label: "Feedback", icon: "💬" },
  { href: "/tokens", label: "Tokens", icon: "🪙" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-56 border-r bg-muted/30 p-4 flex flex-col gap-1">
      <div className="mb-6 px-3">
        <div className="font-bold text-lg">moomoo-ax</div>
        <div className="text-xs text-muted-foreground">3 레이어 관측</div>
      </div>
      {navItems.map((item) => (
        <Link
          key={item.href}
          href={item.href}
          className={cn(
            "flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors",
            pathname.startsWith(item.href)
              ? "bg-primary/10 text-primary font-medium"
              : "text-muted-foreground hover:bg-muted"
          )}
        >
          <span>{item.icon}</span>
          {item.label}
        </Link>
      ))}
      <div className="mt-auto pt-4 border-t text-[10px] text-muted-foreground px-3">
        v0.1
      </div>
    </aside>
  );
}
