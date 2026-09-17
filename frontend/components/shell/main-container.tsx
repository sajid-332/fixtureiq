import type {
  ReactNode,
} from "react";


type MainContainerProps =
  Readonly<{
    children:
      ReactNode;
  }>;


export function MainContainer({
  children,
}: MainContainerProps) {
  return (
    <main
      id="main-content"
      className="
        mx-auto w-full max-w-7xl
        px-4 py-8
        sm:px-6 sm:py-10
        lg:px-8 lg:py-12
      "
      data-fixtureiq-shell="main"
    >
      {children}
    </main>
  );
}
