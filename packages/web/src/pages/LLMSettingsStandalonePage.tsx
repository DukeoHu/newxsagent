import { AppShell } from "../components/layout/AppShell";
import { LLMSettingsPage } from "./LLMSettingsPage";

export function LLMSettingsStandalonePage() {
  return (
    <AppShell centered>
      <LLMSettingsPage />
    </AppShell>
  );
}
