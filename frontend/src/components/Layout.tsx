import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import Callsign from "./deco/Callsign";

export default function Layout() {
  const { logout, authRequired } = useAuth();

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `text-[13px] font-medium px-3 py-1 transition-colors ${
      isActive
        ? "text-bone"
        : "text-sand hover:text-bone"
    }`;

  return (
    <div className="min-h-full flex flex-col relative">
      {/* ----- Top brand bar: black, mono wordmark left, husky center, nav right ----- */}
      <header className="relative z-10 bg-black border-b border-dusk">
        <div className="grid grid-cols-3 items-center px-6 md:px-10 h-14">
          {/* Left: monospace wordmark */}
          <div className="mono text-[11px] tracking-[0.28em] uppercase text-bone whitespace-nowrap">
            Husky Robotics &nbsp;-&nbsp; UW Seattle
          </div>

          {/* Center: husky logo */}
          <div className="flex justify-center">
            <img
              src="/husky-logo.png"
              alt="Husky Robotics"
              className="brand-mark h-9 w-9 object-contain"
            />
          </div>

          {/* Right: primary nav */}
          <nav className="flex items-center justify-end gap-1">
            <NavLink to="/" end className={linkClass}>
              Dashboard
            </NavLink>
            {authRequired && (
              <button
                onClick={logout}
                className="text-[13px] font-medium px-3 py-1 text-ash hover:text-blood ml-2"
              >
                Sign out
              </button>
            )}
          </nav>
        </div>

        {/* Sub-bar: translucent frosted strip with the active console label. */}
        <div className="bg-white/10 backdrop-blur-sm border-t border-b border-white/15">
          <div className="px-6 md:px-10 h-9 flex items-center justify-center">
            <span className="mono text-[10.5px] tracking-[0.28em] uppercase text-bone/90">
              Operator Console
            </span>
          </div>
        </div>
      </header>

      {/* ----- Live mission strip ----- */}
      <div className="px-6 md:px-10 pt-4 pb-3">
        <Callsign />
        <div className="tick-rule mt-2" />
      </div>

      {/* ----- Content ----- */}
      <main className="relative z-10 flex-1 px-6 md:px-10 pb-10">
        <Outlet />
      </main>

      {/* ----- Footer ----- */}
      <footer className="relative z-10 px-6 md:px-10 pb-5">
        <div className="tick-rule mb-2" />
        <div className="flex items-center justify-between text-ash mono text-[10px] tracking-[0.3em] uppercase">
          <span>Biosignature Survey / Mars Analog</span>
          <span>Husky Robotics / UW Seattle / v0.1</span>
        </div>
      </footer>
    </div>
  );
}
