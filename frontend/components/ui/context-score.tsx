import type {
  ContextSupportScore,
} from "../../lib/domain/types";


const signedIntegerFormatter =
  new Intl.NumberFormat(
    "en-GB",
    {
      maximumFractionDigits: 0,
      signDisplay: "exceptZero",
    },
  );


type ContextScoreProps =
  Readonly<{
    score:
      ContextSupportScore;
  }>;


export function ContextScore({
  score,
}: ContextScoreProps) {

  return (
    <span
      aria-label={`Context support score: ${score}`}
      className="
        inline-flex items-center
        rounded-md
        border border-slate-200
        bg-slate-50
        px-2.5 py-1
        text-sm font-semibold
        tabular-nums
        text-slate-950
      "
      data-fixtureiq-component="context-score"
      data-context-score={
        score
      }
    >
      {signedIntegerFormatter.format(
        score,
      )}
    </span>
  );
}
