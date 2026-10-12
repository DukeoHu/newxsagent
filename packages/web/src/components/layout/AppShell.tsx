import type { ReactNode } from "react";
import { GridBackground } from "./GridBackground";
import { NoiseOverlay } from "./NoiseOverlay";
import { SideNav } from "./SideNav";
import { SupervisionPanel } from "./SupervisionPanel";
import "./AppShell.css";

interface AppShellProps {
  children: ReactNode;
  projectId?: string;
  projectTitle?: string;
  onboardingComplete?: boolean;
  showSupervision?: boolean;
  centered?: boolean;
}

export function AppShell({
  children,
  projectId,
  projectTitle,
  onboardingComplete = false,
  showSupervision = false,
  centered = true,
}: AppShellProps) {
  return (
    <>
      <GridBackground />
      <NoiseOverlay />
      <div className="app-shell">
        <SideNav
          projectId={projectId}
          projectTitle={projectTitle}
          onboardingComplete={onboardingComplete}
        />
        <div className="app-shell__main">
          <main
            className={`app-shell__content${centered ? " app-shell__content--centered" : ""}`}
          >
            {children}
          </main>
        </div>
        {showSupervision && projectId && (
          <SupervisionPanel projectId={projectId} />
        )}
      </div>
    </>
  );
}
