"use client";

import { useState } from "react";
import { registerUser, loginUser } from "@/lib/api";
import { useRouter } from "next/navigation";
import Link from "next/link";
import styles from "../login/page.module.css";

export default function RegisterPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const router = useRouter();

  async function handleRegister(e: React.FormEvent) {
    e.preventDefault();
    try {
      await registerUser(username, password);
      // Auto-login upon registration success
      await loginUser(username, password);
      router.push("/");
    } catch (err: any) {
      setError(err.message || "Failed to register");
    }
  }

  return (
    <div className={styles.container}>
      <form className={styles.formBox} onSubmit={handleRegister}>
        <h2>Register an Account</h2>
        {error && <p className={styles.error}>{error}</p>}
        <div className={styles.field}>
          <label>Username</label>
          <input type="text" value={username} onChange={e => setUsername(e.target.value)} required autoFocus />
        </div>
        <div className={styles.field}>
          <label>Password</label>
          <input type="password" value={password} onChange={e => setPassword(e.target.value)} required />
        </div>
        <button type="submit" className={styles.btn}>Create Account</button>
        <p className={styles.prompt}>
          Already have an account? <Link href="/login">Login</Link>
        </p>
      </form>
    </div>
  );
}
