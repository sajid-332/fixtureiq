import {
  RetryAction,
} from "./retry-action";

import {
  ErrorState,
} from "../ui/error-state";

import {
  FreshnessIndicator,
} from "../ui/freshness-indicator";


type ServiceNotReadyStateProps =
  Readonly<{
    state:
      "NOT_READY";

    httpStatus:
      number | null;

    resource:
      string;
  }>;


export function ServiceNotReadyState({
  state,
  httpStatus,
  resource,
}: ServiceNotReadyStateProps) {

  return (
    <section
      data-fixtureiq-component="service-not-ready-state"
      data-fixtureiq-runtime-state="NOT_READY"
    >
      <ErrorState
        title={`${resource} is temporarily unavailable`}
        message={
          "FixtureIQ does not have a current ready response "
          +
          "for this resource. No older result is being shown."
        }
      action={
        <RetryAction />
      }
      />

      <div className="mt-4">
        <FreshnessIndicator
          state={
            state
          }
          httpStatus={
            httpStatus
          }
        />
      </div>
    </section>
  );
}
