const kickoffFormatter =
  new Intl.DateTimeFormat(
    "en-GB",
    {
      dateStyle: "medium",
      timeStyle: "short",
      timeZone: "UTC",
    },
  );


export function formatKickoffUtc(
  value: string,
): string {
  const kickoff =
    new Date(value);

  if (
    Number.isNaN(
      kickoff.getTime(),
    )
  ) {
    throw new RangeError(
      "Invalid kickoff timestamp.",
    );
  }

  return kickoffFormatter.format(
    kickoff,
  );
}
