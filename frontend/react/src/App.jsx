import { AppShell } from "./components/layout/AppShell";
import { HowItWorks } from "./features/landing/HowItWorks";
import { LandingHero } from "./features/landing/LandingHero";
import { SimplifyWorkspace } from "./features/simplify/SimplifyWorkspace";

export default function App() {
  return (
    <AppShell>
      <LandingHero />
      <HowItWorks />
      <SimplifyWorkspace />
    </AppShell>
  );
}
