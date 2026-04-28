import { motion } from "framer-motion";

const DOMAINS = [
{ id: "banking", label: "Banking" },
{ id: "ecommerce", label: "Ecommerce" }
];

export default function DomainSwitcher({ activeDomain, onSwitch }) {
return ( <div className="relative inline-flex rounded-lg bg-slate-100/80 p-[3px] dark:bg-[#2b2d31]/80 border border-slate-200/50 dark:border-[#1e1f22]">
  {/* Sliding pill */}
  <motion.div
    layout
    transition={{ type: "spring", stiffness: 500, damping: 35 }}
    className="absolute top-[3px] bottom-[3px] rounded-md bg-indigo-600 dark:bg-[#5865f2]"
    style={{
      left: activeDomain === "banking" ? "0px" : "calc(50% - 6px)",
      width: "calc(50% - 0px)"
    }}
  />

  {DOMAINS.map((domain) => {
    const isActive = activeDomain === domain.id;
    return (
      <button
        key={domain.id}
        onClick={() => onSwitch(domain.id)}
        className={`relative z-10 flex-1 rounded-md px-4 py-1 text-sm font-semibold transition ${
          isActive
            ? "text-white"
            : "text-slate-600 hover:text-slate-900 dark:text-[#b5bac1] dark:hover:text-[#f2f3f5]"
        }`}
      >
        {domain.label}
      </button>
    );
  })}
</div>
);
}
