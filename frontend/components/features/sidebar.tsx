"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  ChartBar,
  BookOpen,
  Robot,
  Tray,
  Kanban,
  GearSix,
  Sparkle,
  CreditCard,
} from "@phosphor-icons/react";
import { UserButton, OrganizationSwitcher } from "@clerk/nextjs";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: ChartBar },
  { href: "/agents", label: "Agentes", icon: Robot },
  { href: "/inbox", label: "Inbox", icon: Tray },
  { href: "/crm", label: "CRM", icon: Kanban },
  { href: "/knowledge", label: "Base de conhecimento", icon: BookOpen },
  { href: "/learning", label: "Aprendizado", icon: Sparkle },
];

const secondaryItems = [
  { href: "/billing", label: "Plano", icon: CreditCard },
  { href: "/settings", label: "Configurações", icon: GearSix },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex h-screen w-56 flex-col border-r border-border bg-sidebar">
      {/* Logo */}
      <div className="flex h-14 items-center px-4">
        <span className="text-lg font-bold tracking-tight">Convo</span>
      </div>

      {/* Organization switcher */}
      <div className="border-b border-border px-3 pb-3">
        <OrganizationSwitcher
          hidePersonal
          appearance={{
            elements: {
              rootBox: "w-full",
              organizationSwitcherTrigger:
                "w-full justify-start gap-2 rounded-md px-2 py-1.5 text-sm hover:bg-sidebar-accent transition-colors",
            },
          }}
        />
      </div>

      {/* Nav principal */}
      <nav className="flex-1 overflow-y-auto px-2 py-3">
        <ul className="flex flex-col gap-0.5">
          {navItems.map((item) => {
            const isActive = pathname.startsWith(item.href);
            const Icon = item.icon;
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-sidebar-accent text-sidebar-accent-foreground"
                      : "text-muted-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
                  )}
                >
                  <Icon className="h-4 w-4 shrink-0" />
                  {item.label}
                </Link>
              </li>
            );
          })}
        </ul>

        <div className="mt-4 border-t border-sidebar-border pt-4">
          <ul className="flex flex-col gap-0.5">
            {secondaryItems.map((item) => {
              const isActive = pathname.startsWith(item.href);
              const Icon = item.icon;
              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    className={cn(
                      "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                      isActive
                        ? "bg-sidebar-accent text-sidebar-accent-foreground"
                        : "text-muted-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
                    )}
                  >
                    <Icon className="h-4 w-4 shrink-0" />
                    {item.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </div>
      </nav>

      {/* User button */}
      <div className="border-t border-sidebar-border p-3">
        <UserButton
          appearance={{
            elements: {
              rootBox: "w-full",
              userButtonTrigger:
                "w-full justify-start gap-2 rounded-md px-2 py-1.5 hover:bg-sidebar-accent transition-colors",
            },
          }}
          showName
        />
      </div>
    </aside>
  );
}
