"use client";

import { useCallback, useState, useRef } from "react";
import styles from "./FileUpload.module.css";

interface Props {
  onUpload: (file: File) => void;
  disabled?: boolean;
}

export default function FileUpload({ onUpload, disabled }: Props) {
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(
    (file: File) => {
      if (disabled) return;
      const ext = file.name.split(".").pop()?.toLowerCase();
      if (ext === "cbl" || ext === "cob" || ext === "cobol") {
        onUpload(file);
      } else {
        alert("Please upload a COBOL file (.cbl, .cob, .cobol)");
      }
    },
    [onUpload, disabled]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      if (e.dataTransfer.files.length > 0) {
        handleFile(e.dataTransfer.files[0]);
      }
    },
    [handleFile]
  );

  return (
    <div
      className={`${styles.dropzone} ${isDragging ? styles.dragging : ""} ${disabled ? styles.disabled : ""}`}
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
      onClick={() => !disabled && inputRef.current?.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".cbl,.cob,.cobol"
        className={styles.input}
        onChange={(e) => {
          if (e.target.files?.[0]) handleFile(e.target.files[0]);
        }}
      />
      <div className={styles.icon}>⬆</div>
      <p className={styles.title}>
        {disabled ? "Submitting..." : "Upload Legacy Source"}
      </p>
      <p className={styles.subtitle}>
        Drag &amp; drop a COBOL file or click to browse
      </p>
      <p className={styles.formats}>.cbl · .cob · .cobol</p>
    </div>
  );
}
