import {
  EmptyState,
} from "../ui/empty-state";


export function EmptyFixturesState() {

  return (
    <div
      data-fixtureiq-component="empty-fixtures-state"
      data-fixtureiq-runtime-state="EMPTY_FIXTURES"
    >
      <EmptyState
        title="No upcoming matches"
        message={
          "FixtureIQ received a ready response with no upcoming fixtures. "
          +
          "No previous fixture list is being reused."
        }
      />
    </div>
  );
}
