import { Component, type ErrorInfo, type ReactNode } from "react";

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  message: string | null;
}

export default class ErrorBoundary extends Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  public state: ErrorBoundaryState = { hasError: false, message: null };

  public static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, message: error.message || "An unexpected interface error occurred." };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error("Unhandled frontend error", error, errorInfo);
  }

  public render(): ReactNode {
    if (this.state.hasError) {
      return <main className="error-boundary" role="alert">
        <span className="error-boundary-mark">!</span>
        <p className="eyebrow">INTERFACE RECOVERY</p>
        <h1>Something went wrong</h1>
        <p>{this.state.message}</p>
        <div>
          <button type="button" onClick={() => window.location.reload()}>Retry page</button>
          <a className="primary-link error-boundary-home" href="/">Return to overview</a>
        </div>
      </main>;
    }

    return this.props.children;
  }
}
