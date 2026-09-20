"use client";

import {
  useRouter,
} from "next/navigation";

import {
  useTransition,
} from "react";


type RetryActionProps =
  Readonly<{
    label?: string;
  }>;


export function RetryAction({
  label = "Try again",
}: RetryActionProps) {

  const router =
    useRouter();

  const [
    isPending,
    startTransition,
  ] =
    useTransition();


  function retry() {

    startTransition(
      () => {
        router.refresh();
      },
    );
  }


  return (
    <button
      type="button"
      onClick={
        retry
      }
      disabled={
        isPending
      }
      aria-busy={
        isPending
      }
      data-fixtureiq-component="retry-action"
      className="
        inline-flex min-h-11
        items-center justify-center
        rounded-lg border
        border-slate-300
        bg-white px-4 py-2
        text-sm font-semibold
        text-slate-950
        shadow-sm
        transition
        hover:bg-slate-50
        focus-visible:outline-none
        focus-visible:ring-2
        focus-visible:ring-slate-950
        focus-visible:ring-offset-2
        disabled:cursor-not-allowed
        disabled:opacity-60
      "
    >
      {
        isPending
          ? "Retrying..."
          : label
      }
    </button>
  );
}
