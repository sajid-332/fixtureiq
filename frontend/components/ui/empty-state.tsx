import type {
  ReactNode,
} from "react";


type EmptyStateProps =
  Readonly<{
    title:
      string;

    message:
      string;

    action?:
      ReactNode;
  }>;


export function EmptyState({
  title,
  message,
  action,
}: EmptyStateProps) {

  return (
    <section
      aria-labelledby="fixtureiq-empty-state-heading"
      className="
        rounded-xl
        border border-dashed
        border-slate-300
        bg-white
        px-5 py-8
        text-center
        sm:px-8
      "
      data-fixtureiq-component="empty-state"
    >
      <h2
        id="fixtureiq-empty-state-heading"
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
                data-empty-state-action
              >
                {action}
              </div>
            )
          : null
      }
    </section>
  );
}
