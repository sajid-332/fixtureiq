import Link from "next/link";

import {
  EmptyState,
} from "../../../components/ui/empty-state";


export default function MatchNotFound() {

  return (
    <EmptyState
      title="Match not found"
      message={
        "FixtureIQ does not have current intelligence "
        +
        "for this match."
      }
      action={
        <Link
          href="/"
          className="
            text-sm font-semibold
            text-slate-950
            underline
            underline-offset-4
          "
        >
          Back to upcoming matches
        </Link>
      }
    />
  );
}
