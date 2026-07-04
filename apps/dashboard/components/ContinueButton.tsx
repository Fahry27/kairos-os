"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

export function ContinueButton() {
  const [label, setLabel] = useState("Continue Mission");

  useEffect(() => {
    const goal = localStorage.getItem("kairos:workspace:goal");
    if (goal && goal.trim().length > 0) {
      const shortGoal = goal.length > 30 ? goal.substring(0, 30) + "..." : goal;
      setLabel(`Continue: ${shortGoal}`);
    }
  }, []);

  return (
    <Link className="btnSmall btnSave" href="/workspace" style={{ padding: '12px 24px', fontSize: '16px' }}>
      {label}
    </Link>
  );
}
