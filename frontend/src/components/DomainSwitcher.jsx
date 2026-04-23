const DOMAINS = [
  { id: "banking", label: "Banking" },
  { id: "ecommerce", label: "Ecommerce" }
];

export default function DomainSwitcher({ activeDomain, onSwitch }) {
  return (
    <div className="inline-flex rounded-xl bg-slate-100 p-1 dark:bg-[#1e1f22]">
      {DOMAINS.map((domain) => {
        const isActive = activeDomain === domain.id;
        return (
          <button
            key={domain.id}
            type="button"
            className={`rounded-lg px-4 py-2 text-sm font-semibold transition ${
              isActive
                ? "bg-indigo-600 text-white shadow-sm dark:bg-[#5865f2]"
                : "text-slate-600 hover:bg-white hover:text-slate-900 dark:text-[#b5bac1] dark:hover:bg-[#2b2d31] dark:hover:text-[#f2f3f5]"
            }`}
            onClick={() => onSwitch(domain.id)}
          >
            {domain.label}
          </button>
        );
      })}
    </div>
  );
}
