"use client";

import { Highlight, themes } from "prism-react-renderer";
import styles from "./CodeViewer.module.css";

interface Props {
  code: string;
  language?: string;
  title?: string;
}

export default function CodeViewer({ code, language = "python", title }: Props) {
  return (
    <div className={styles.wrapper}>
      {title && <div className={styles.header}>{title}</div>}
      <Highlight theme={themes.nightOwl} code={code.trim()} language={language}>
        {({ style, tokens, getLineProps, getTokenProps }) => (
          <pre className={styles.pre} style={{ ...style, background: "transparent" }}>
            {tokens.map((line, i) => {
              const lineProps = getLineProps({ line, key: i });
              return (
                <div key={i} {...lineProps}>
                  <span className={styles.lineNumber}>{i + 1}</span>
                  {line.map((token, key) => (
                    <span key={key} {...getTokenProps({ token, key })} />
                  ))}
                </div>
              );
            })}
          </pre>
        )}
      </Highlight>
    </div>
  );
}
