import { Link } from "@tanstack/react-router";
import { Activity, BookOpen, Info, Users, Wallet } from "lucide-react";

const ITEMS = [
  { to: "/", label: "Live", icon: Activity },
  { to: "/how-it-works", label: "How", icon: BookOpen },
  /*{ to: "/profile", label: "Profile", icon: Users },*/
  { to: "/wallet", label: "Wallet", icon: Wallet },
  { to: "/about", label: "About", icon: Info },
] as const;

export function MobileNav() {
  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 border-t border-border bg-background/95 backdrop-blur md:hidden">
      <ul className="grid grid-cols-4">
        {ITEMS.map((item) => (
          <li key={item.to}>
            <Link
              to={item.to}
              activeOptions={{ exact: item.to === "/" }}
              className="flex flex-col items-center gap-1 py-2.5 text-muted-foreground"
              activeProps={{
                className: "flex flex-col items-center gap-1 py-2.5 text-primary",
              }}
            >
              <item.icon className="h-5 w-5" />
              <span className="font-mono text-[0.625rem] uppercase tracking-[0.16em]">
                {item.label}
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}
