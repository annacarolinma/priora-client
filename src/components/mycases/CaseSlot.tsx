import { FiPlus } from "react-icons/fi";

/**
 * Espaço vazio no formato dos cartões de caso (aba + corpo), com um "+" no meio.
 * Só preenche a grade de "Meus casos" e abre o cadastro de um novo caso.
 */
export default function CaseSlot({ onClick }: { onClick: () => void }) {
  return (
    <div className="w-full max-w-sm">
      <div className="flex items-end">
        <span
          aria-hidden="true"
          className="relative z-10 -mb-px inline-block h-[30px] w-28 rounded-t-lg border border-b-0 border-dashed border-[#3a3a3a] bg-[#242424]"
        />
      </div>

      <button
        type="button"
        onClick={onClick}
        aria-label="Criar novo caso"
        className="group flex h-[258px] w-full items-center justify-center rounded-b-xl rounded-tr-xl border border-dashed border-[#3a3a3a] bg-[#242424] transition hover:border-[#139C73] hover:bg-[#2A2A2A]"
      >
        <span className="flex size-12 items-center justify-center rounded-full border border-dashed border-[#575757] text-white/40 transition group-hover:border-[#139C73] group-hover:text-[#139C73]">
          <FiPlus size={22} />
        </span>
      </button>
    </div>
  );
}
