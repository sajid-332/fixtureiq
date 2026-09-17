import type {
  ReactNode,
} from "react";


type MatchCardProps =
  Readonly<{
    children?:
      ReactNode;
  }>;


export function MatchCard({
  children,
}: MatchCardProps) {
  return (
    <article
      className="
        overflow-hidden rounded-xl
        border border-slate-200
        bg-white shadow-sm
      "
      data-fixtureiq-component="match-card"
    >
      {children}
    </article>
  );
}
