import { FormEvent, useState } from "react";
import { useAuth } from "../auth/AuthContext";

export default function Login() {
  const { login, error } = useAuth();
  const [token, setToken] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await login(token.trim());
    } catch {
      // surfaced via context
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-full grid place-items-center p-6 relative">
      {/* Decorative coordinate marks */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-6 left-6 mono text-[10px] tracking-[0.3em] uppercase text-hair">
          LAT 38.927 N
        </div>
        <div className="absolute top-6 right-6 mono text-[10px] tracking-[0.3em] uppercase text-hair">
          LON 110.793 W
        </div>
        <div className="absolute bottom-6 left-6 mono text-[10px] tracking-[0.3em] uppercase text-hair">
          MDRS UTAH
        </div>
        <div className="absolute bottom-6 right-6 mono text-[10px] tracking-[0.3em] uppercase text-hair">
          URC 2025
        </div>
      </div>

      <form
        onSubmit={onSubmit}
        className="panel w-full max-w-md p-8 relative stagger"
        style={{ ["--stagger" as string]: "90ms" }}
      >
        <div
          style={{ ["--i" as string]: 0 }}
          className="flex flex-col items-center text-center"
        >
          <img
            src="/husky-logo.png"
            alt="Husky Robotics"
            className="brand-mark w-24 h-24 object-contain"
          />
        </div>

        <div style={{ ["--i" as string]: 1 }} className="mt-6 text-center">
          <div className="eyebrow">Science Console / URC 2025</div>
          <h1 className="display-italic text-bone text-5xl leading-none mt-4">
            Authorize
          </h1>
          <p className="mono text-[11px] tracking-wider text-sand mt-3">
            Operator token required to reach the deck.
          </p>
        </div>

        <div style={{ ["--i" as string]: 2 }} className="mt-8">
          <label className="eyebrow block mb-2">Token</label>
          <input
            autoFocus
            className="input"
            type="password"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder="\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022"
          />
          {error && (
            <div className="mono text-[11px] tracking-wider text-blood mt-3">
              REJECTED / {error}
            </div>
          )}
        </div>

        <button
          style={{ ["--i" as string]: 3 }}
          className="btn btn-primary w-full justify-center mt-8"
          disabled={submitting || !token}
        >
          {submitting ? "Authenticating\u2026" : "Enter console"}
        </button>

        <div
          style={{ ["--i" as string]: 4 }}
          className="mono text-[10px] tracking-[0.25em] uppercase text-ash mt-8 flex items-center justify-between"
        >
          <span>v0.1</span>
          <span>Secure channel</span>
        </div>
      </form>
    </div>
  );
}
