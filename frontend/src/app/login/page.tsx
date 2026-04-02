"use client";

import { useState } from "react";
import { loginUser } from "@/lib/api";
import { useRouter } from "next/navigation";
import Link from "next/link";
import styles from "./page.module.css";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const router = useRouter();

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    try {
      await loginUser(username, password);
      router.push("/");
    } catch (err: any) {
      setError(err.message || "Failed to login");
    }
  }

  return (
    <div className={styles.container}>
      <form className={styles.formBox} onSubmit={handleLogin}>
        <h2>Sign in to LegacyLens</h2>
        {error && <p className={styles.error}>{error}</p>}
        <div className={styles.field}>
          <label>Username</label>
          <input type="text" value={username} onChange={e => setUsername(e.target.value)} required autoFocus />
        </div>
        <div className={styles.field}>
          <label>Password</label>
          <input type="password" value={password} onChange={e => setPassword(e.target.value)} required />
        </div>
        <button type="submit" className={styles.btn}>Login</button>
        <p className={styles.prompt}>
          No account? <Link href="/register">Register</Link>
        </p>
      </form>
    </div>
  );
}
