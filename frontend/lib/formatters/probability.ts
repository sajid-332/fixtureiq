const probabilityFormatter =
  new Intl.NumberFormat(
    "en-GB",
    {
      style: "percent",
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    },
  );


export function formatProbability(
  value: number,
): string {
  if (
    !Number.isFinite(value)
    ||
    value < 0
    ||
    value > 1
  ) {
    throw new RangeError(
      "Probability must be a finite number between 0 and 1.",
    );
  }

  return probabilityFormatter.format(
    value,
  );
}
