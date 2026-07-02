import Link from "next/link";
import { AIWorkspace } from "../../components/AIWorkspace";
import { KAIROS_API_URL } from "../../lib/api";

export default function WorkspacePage() {
  return (
    <main className="page">
      <header className="topBar">
        <div>
          <p className="eyebrow">Kairos OS</p>
          <h1>AI Workspace</h1>
          <p className="subtitle">Dashboard connected to {KAIROS_API_URL}</p>
        </div>
        <Link className="btnSmall btnOutline topBarLink" href="/">
          Operator Console
        </Link>
      </header>

      <AIWorkspace />
    </main>
  );
}
