import type {
  ReactNode,
} from "react";


type ErrorStateProps =
  Readonly<{
    title:
      string;

    message:
      string;

    action?:
      ReactNode;
  }>;


export function ErrorState({
  title,
  message,
  action,
}: ErrorStateProps) {

  return (
    <section
      aria-labelledby="fixtureiq-error-state-heading"
      className="
        rounded-xl
        border border-slate-300
        bg-white
        px-5 py-8
        text-center
        shadow-sm
        sm:px-8
      "
      data-fixtureiq-component="error-state"
      role="alert"
    >
      <h2
        id="fixtureiq-error-state-heading"
        className="
          text-lg font-bold
          text-slate-950
        "
      >
        {title}
      </h2>

      <p
        className="
          mx-auto mt-2
          max-w-xl
          text-sm leading-6
          text-slate-600
        "
      >
        {message}
      </p>

      {
        action
          ? (
              <div
                className="mt-5"
                data-error-state-action
              >
                {action}
              </div>
            )
          : null
      }
    </section>
  );
}
