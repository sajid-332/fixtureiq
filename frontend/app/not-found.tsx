import Link from "next/link";

import {
  EmptyState,
} from "../components/ui/empty-state";


export default function NotFound() {

  return (
    <EmptyState
      title="Page not found"
      message={
        "The requested FixtureIQ page could not be found."
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
