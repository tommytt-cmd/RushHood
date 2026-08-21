import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

export function Panel({
  children,
  className,
  as: Tag = "div",
}: {
  children: ReactNode;
  className?: string;
  as?: "div" | "section" | "article";
}) {
  return <Tag className={cn("panel p-6", className)}>{children}</Tag>;
}

export function SectionHeading({
  eyebrow,
  title,
  children,
}: {
  eyebrow?: string;
  title: string;
  children?: ReactNode;
}) {
  return (
    <div className="grid gap-4 md:grid-cols-[1fr_1.2fr] md:items-end">
      <div>
        {eyebrow && <p className="label-tech mb-3">{eyebrow}</p>}
        <h2 className="text-3xl leading-[1.05] sm:text-4xl text-foreground">{title}</h2>
        <div className="mt-3 h-1 w-24 rounded bg-primary/80" />
      </div>
      {children && <p className="text-sm text-muted-foreground md:pb-2">{children}</p>}
    </div>
  );
}
