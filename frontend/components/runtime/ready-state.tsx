import type {
  ReactNode,
} from "react";


type ReadyStateProps =
  Readonly<{
    children:
      ReactNode;
  }>;


export function ReadyState({
  children,
}: ReadyStateProps) {

  return (
    <div
      data-fixtureiq-component="ready-state"
      data-fixtureiq-runtime-state="READY"
    >
      {children}
    </div>
  );
}
