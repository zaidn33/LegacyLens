"use client";

import { useState } from "react";
import styles from "./TabPanel.module.css";

interface Tab {
  id: string;
  label: string;
  content: React.ReactNode;
}

interface Props {
  tabs: Tab[];
  defaultTab?: string;
}

export default function TabPanel({ tabs, defaultTab }: Props) {
  const [activeId, setActiveId] = useState(defaultTab || tabs[0]?.id);
  const activeTab = tabs.find((t) => t.id === activeId);

  return (
    <div className={styles.wrapper}>
      <div className={styles.tabs}>
        {tabs.map((tab) => (
          <button
            key={tab.id}
            className={`${styles.tab} ${tab.id === activeId ? styles.active : ""}`}
            onClick={() => setActiveId(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div className={styles.content}>{activeTab?.content}</div>
    </div>
  );
}
