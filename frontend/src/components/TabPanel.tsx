"use client";

import { useState, useEffect } from "react";
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

  // When tabs change (e.g. after data loads), pick the best tab:
  // prefer the defaultTab if it now exists, otherwise keep current if valid
  useEffect(() => {
    const currentValid = tabs.some((t) => t.id === activeId);
    const defaultExists = defaultTab && tabs.some((t) => t.id === defaultTab);
    if (defaultExists && activeId !== defaultTab) {
      setActiveId(defaultTab);
    } else if (!currentValid && tabs.length > 0) {
      setActiveId(tabs[0].id);
    }
  }, [tabs, defaultTab]); // eslint-disable-line react-hooks/exhaustive-deps

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
