"use client";

import { useCallback, useState, useRef } from "react";
import styles from "./FileUpload.module.css";

interface Props {
  onUpload: (file: File, dependencies?: File[]) => void;
  disabled?: boolean;
}

export default function FileUpload({ onUpload, disabled }: Props) {
  const [isDragging, setIsDragging] = useState(false);
  const [stagedFiles, setStagedFiles] = useState<File[]>([]);
  const [primaryIndex, setPrimaryIndex] = useState<number>(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const ingestFiles = useCallback((filesList: FileList | File[]) => {
    const valid: File[] = [];
    for (let i = 0; i < filesList.length; i++) {
        const file = filesList[i];
        const ext = file.name.split(".").pop()?.toLowerCase();
        if (["cbl", "cob", "cobol", "cpy"].includes(ext || "")) {
            valid.push(file);
        }
    }
    
    if (valid.length > 0) {
        setStagedFiles((prev) => [...prev, ...valid]);
    } else {
        alert("Please upload COBOL or Copybook files (.cbl, .cob, .cpy)");
    }
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      if (disabled) return;
      if (e.dataTransfer.files.length > 0) {
        ingestFiles(e.dataTransfer.files);
      }
    },
    [ingestFiles, disabled]
  );
  
  const handleRemove = (idx: number) => {
      setStagedFiles(stagedFiles.filter((_, i) => i !== idx));
      if (primaryIndex === idx) setPrimaryIndex(0);
      else if (primaryIndex > idx) setPrimaryIndex(primaryIndex - 1);
  };
  
  const handleSubmit = (e: React.MouseEvent) => {
      e.stopPropagation();
      if (stagedFiles.length === 0 || disabled) return;
      
      const primary = stagedFiles[primaryIndex];
      const dependencies = stagedFiles.filter((_, i) => i !== primaryIndex);
      onUpload(primary, dependencies);
      setStagedFiles([]);
  };

  return (
    <div className={styles.container}>
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
            multiple
            accept=".cbl,.cob,.cobol,.cpy"
            className={styles.input}
            onChange={(e) => {
              if (e.target.files) ingestFiles(e.target.files);
            }}
          />
          <div className={styles.icon}>⬆</div>
          <p className={styles.title}>
            {disabled ? "Submitting..." : "Upload Legacy Source"}
          </p>
          <p className={styles.subtitle}>
            Drag &amp; drop COBOL sources + Copybooks, or click to browse
          </p>
          <p className={styles.formats}>.cbl · .cob · .cpy</p>
        </div>
        
        {stagedFiles.length > 0 && (
            <div className={styles.stagingArea}>
                <h3 className={styles.stagingTitle}>Staged Files</h3>
                <p className={styles.stagingHelp}>Select the primary entry-point file</p>
                <ul className={styles.fileList}>
                    {stagedFiles.map((f, idx) => (
                        <li key={`${f.name}-${idx}`} className={`${styles.fileItem} ${primaryIndex === idx ? styles.primaryRow : ''}`}>
                            <input 
                                type="radio" 
                                name="primaryFile" 
                                checked={primaryIndex === idx}
                                onChange={() => setPrimaryIndex(idx)}
                                className={styles.radioControl}
                            />
                            <span className={styles.fileName}>{f.name}</span>
                            <span className={styles.fileSize}>({(f.size / 1024).toFixed(1)}kb)</span>
                            {primaryIndex !== idx && (
                                <span className={styles.dependencyBadge}>Dependency</span>
                            )}
                            <button className={styles.removeBtn} onClick={(e) => { e.stopPropagation(); handleRemove(idx); }}>✕</button>
                        </li>
                    ))}
                </ul>
                <button 
                  className={styles.submitBtn} 
                  onClick={handleSubmit} 
                  disabled={disabled}
                >
                  {disabled ? "Processing..." : `Start Analysis (${stagedFiles.length} files)`}
                </button>
            </div>
        )}
    </div>
  );
}
