import {
  ErrorState,
} from "../ui/error-state";

import {
  FreshnessIndicator,
} from "../ui/freshness-indicator";


type ConnectionErrorStateProps =
  Readonly<{
    httpStatus:
      number | null;

    resource:
      string;
  }>;


export function ConnectionErrorState({
  httpStatus,
  resource,
}: ConnectionErrorStateProps) {

  return (
    <section
      data-fixtureiq-component="connection-error-state"
      data-fixtureiq-runtime-state="CONNECTION_ERROR"
    >
      <ErrorState
        title={`${resource} cannot be reached`}
        message={
          "FixtureIQ could not reach the backend service. "
          +
          "No older result is being shown."
        }
      />

      <div className="mt-4">
        <FreshnessIndicator
          state="CONNECTION_ERROR"
          httpStatus={
            httpStatus
          }
        />
      </div>
    </section>
  );
}
