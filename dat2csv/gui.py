"""
Interface gráfica desktop para o dat2csv usando Tkinter (biblioteca padrão).

Permite selecionar arquivos .dat, .sps e definir saída .csv,
com opções de apply-labels, clean, no-backup e hash,
além de preview e conversão em thread separada (não bloqueia a interface).
"""

import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path


class Dat2CsvGUI:
    """Janela principal da interface gráfica do dat2csv."""

    def __init__(self, root: tk.Tk) -> None:
        """
        Inicializa a janela principal e monta os widgets.

        Args:
            root: Instância Tk raiz.
        """
        self.root = root
        root.title("dat2csv — Conversor de arquivos .dat")
        style = ttk.Style()
        style.theme_use('clam')  # ou 'alt'
        root.resizable(True, True)
        root.minsize(640, 500)

        # ── Variáveis de controle ────────────────────────────────────────────
        self.dat_path = tk.StringVar()
        self.sps_path = tk.StringVar()
        self.csv_path = tk.StringVar()
        self.var_apply_labels = tk.BooleanVar(value=False)
        self.var_clean = tk.BooleanVar(value=False)
        self.var_no_backup = tk.BooleanVar(value=False)
        self.var_hash = tk.BooleanVar(value=False)

        # ── Construção da interface ──────────────────────────────────────────
        self._build_widgets()

    # ── Construção dos widgets ───────────────────────────────────────────────

    def _build_widgets(self) -> None:
        """Monta todos os widgets da janela principal."""
        # --- Frame: arquivos ---
        frame_arquivos = ttk.LabelFrame(self.root, text="Arquivos", padding=10)
        frame_arquivos.pack(fill="x", padx=10, pady=(10, 5))

        # .dat
        ttk.Label(frame_arquivos, text="Arquivo .dat (obrigatório):").grid(
            row=0, column=0, sticky="w", pady=(0, 5)
        )
        ttk.Entry(frame_arquivos, textvariable=self.dat_path, width=60).grid(
            row=0, column=1, padx=(5, 5), pady=(0, 5), sticky="ew"
        )
        ttk.Button(
            frame_arquivos, text="Procurar\u2026", command=self._selecionar_dat
        ).grid(row=0, column=2, pady=(0, 5))
        frame_arquivos.columnconfigure(1, weight=1)

        # .sps
        ttk.Label(frame_arquivos, text="Arquivo .sps (opcional):").grid(
            row=1, column=0, sticky="w", pady=(0, 5)
        )
        ttk.Entry(frame_arquivos, textvariable=self.sps_path, width=60).grid(
            row=1, column=1, padx=(5, 5), pady=(0, 5), sticky="ew"
        )
        ttk.Button(
            frame_arquivos, text="Procurar\u2026", command=self._selecionar_sps
        ).grid(row=1, column=2, pady=(0, 5))

        # .csv
        ttk.Label(frame_arquivos, text="Arquivo .csv de saída (opcional):").grid(
            row=2, column=0, sticky="w"
        )
        ttk.Entry(frame_arquivos, textvariable=self.csv_path, width=60).grid(
            row=2, column=1, padx=(5, 5), sticky="ew"
        )
        ttk.Button(
            frame_arquivos, text="Procurar\u2026", command=self._selecionar_csv
        ).grid(row=2, column=2)

        # --- Frame: opções ---
        frame_opcoes = ttk.LabelFrame(self.root, text="Opções", padding=10)
        frame_opcoes.pack(fill="x", padx=10, pady=5)

        ttk.Checkbutton(
            frame_opcoes,
            text="Aplicar rótulos do .sps (apply-labels)",
            variable=self.var_apply_labels,
        ).grid(row=0, column=0, sticky="w", padx=(0, 20))

        ttk.Checkbutton(
            frame_opcoes,
            text="Remover colunas vazias (clean)",
            variable=self.var_clean,
        ).grid(row=0, column=1, sticky="w")

        ttk.Checkbutton(
            frame_opcoes,
            text="Desabilitar backup (no-backup)",
            variable=self.var_no_backup,
        ).grid(row=1, column=0, sticky="w", padx=(0, 20))

        ttk.Checkbutton(
            frame_opcoes,
            text="Exibir hash SHA256 (hash)",
            variable=self.var_hash,
        ).grid(row=1, column=1, sticky="w")

        # --- Frame: botões de ação ---
        frame_acoes = ttk.Frame(self.root, padding=10)
        frame_acoes.pack(fill="x", padx=10, pady=5)

        self.btn_converter = ttk.Button(
            frame_acoes, text="Converter", command=self._converter
        )
        self.btn_converter.pack(side="left", padx=(0, 10))

        ttk.Label(frame_acoes, text="Linhas:").pack(side="left", padx=(10, 2))
        self.preview_rows = tk.Spinbox(
            frame_acoes, from_=1, to=50, width=5,
        )
        self.preview_rows.pack(side="left", padx=(0, 10))
        self.preview_rows.delete(0, "end")
        self.preview_rows.insert(0, "5")

        self.btn_preview = ttk.Button(
            frame_acoes, text="Preview", command=self._preview
        )
        self.btn_preview.pack(side="left")

        # --- Área de logs ---
        frame_log = ttk.LabelFrame(self.root, text="Log", padding=10)
        frame_log.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        self.text_log = tk.Text(frame_log, wrap="word", state="disabled", height=14)
        scrollbar = ttk.Scrollbar(
            frame_log, orient="vertical", command=self.text_log.yview
        )
        self.text_log.configure(yscrollcommand=scrollbar.set)
        self.text_log.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    # ── Seleção de arquivos ──────────────────────────────────────────────────

    def _selecionar_dat(self) -> None:
        # Abre diálogo para selecionar arquivo .dat
        path = filedialog.askopenfilename(
            title="Selecionar arquivo .dat",
            filetypes=[("Arquivos DAT", "*.dat"), ("Todos os arquivos", "*.*")],
        )
        if path:
            self.dat_path.set(path)

    def _selecionar_sps(self) -> None:
        # Abre diálogo para selecionar arquivo .sps
        path = filedialog.askopenfilename(
            title="Selecionar arquivo .sps",
            filetypes=[("Arquivos SPS", "*.sps"), ("Todos os arquivos", "*.*")],
        )
        if path:
            self.sps_path.set(path)

    def _selecionar_csv(self) -> None:
        # Abre diálogo para selecionar arquivo .csv de saída
        path = filedialog.asksaveasfilename(
            title="Selecionar arquivo .csv de saída",
            defaultextension=".csv",
            filetypes=[("Arquivos CSV", "*.csv"), ("Todos os arquivos", "*.*")],
        )
        if path:
            self.csv_path.set(path)

    # ── Ações ────────────────────────────────────────────────────────────────

    def _log(self, mensagem: str) -> None:
        """
        Insere texto na área de logs (thread-safe).

        Pode ser chamada de qualquer thread; programa o insert na
        thread principal via ``root.after()``.
        """
        def _inserir() -> None:
            self.text_log.configure(state="normal")
            self.text_log.insert("end", mensagem + "\n")
            self.text_log.see("end")
            self.text_log.configure(state="disabled")

        self.root.after(0, _inserir)

    def _erro(self, mensagem: str) -> None:
        """
        Exibe uma caixa de diálogo de erro (thread-safe).

        Args:
            mensagem: Texto da mensagem de erro.
        """
        self.root.after(0, lambda: messagebox.showerror("Erro", mensagem))

    def _alternar_botoes(self, habilitar: bool) -> None:
        # Habilita/desabilita os botões de ação
        estado = "normal" if habilitar else "disabled"
        self.btn_converter.configure(state=estado)
        self.btn_preview.configure(state=estado)

    def _converter(self) -> None:
        """Valida entrada e dispara a conversão em uma thread separada."""
        if not self.dat_path.get().strip():
            self._erro("Selecione um arquivo .dat de entrada.")
            return

        # Se o caminho de saída não foi informado, usa <input>.csv
        if not self.csv_path.get().strip():
            input_p = Path(self.dat_path.get().strip())
            self.csv_path.set(str(input_p.with_suffix(".csv")))

        self._alternar_botoes(False)
        self._log("▶ Iniciando convers\u00e3o\u2026")
        thread = threading.Thread(target=self._executar_conversao, daemon=True)
        thread.start()

    def _executar_conversao(self) -> None:
        """Executa a conversão em background (roda em thread separada)."""
        try:
            from .converter import convert
            from .utils import calcular_hash

            input_path = Path(self.dat_path.get().strip())
            output_path = Path(self.csv_path.get().strip())
            sps = (
                Path(self.sps_path.get().strip())
                if self.sps_path.get().strip()
                else None
            )
            apply_labels = self.var_apply_labels.get()
            clean = self.var_clean.get()
            no_backup = self.var_no_backup.get()
            do_hash = self.var_hash.get()

            # Hash antes da conversão (opcional)
            if do_hash:
                digest = calcular_hash(input_path)
                self._log(f"Hash SHA256 do original: {digest}")

            result = convert(
                input_path=input_path,
                output_path=output_path,
                sps_path=sps,
                apply_labels=apply_labels,
                clean=clean,
                backup=(not no_backup),
                add_header=True,
            )

            # Monta resumo
            linhas = result.get("rows", 0)
            colunas = result.get("columns", 0)
            backup_path = result.get("backup")
            removed = result.get("removed_cols")

            self._log(f"✔ Arquivo convertido com sucesso!")
            self._log(f"  Entrada:  {input_path}")
            self._log(f"  Sa\u00edda:    {output_path}")
            self._log(f"  Linhas:   {linhas}")
            self._log(f"  Colunas:  {colunas}")
            if sps is not None:
                self._log(f"  Metadados .sps: {sps}")
            if removed is not None:
                self._log(f"  Colunas removidas (--clean): {removed}")
            if backup_path:
                self._log(f"  Backup criado: {backup_path}")
            elif no_backup:
                self._log("  Backup: desabilitado (--no-backup)")
            else:
                self._log("  Backup: nenhum (arquivo novo)")

        except Exception as exc:
            self._erro(f"Erro durante a convers\u00e3o:\n{exc}")
        finally:
            self.root.after(0, lambda: self._alternar_botoes(True))

    def _preview(self) -> None:
        """Valida entrada e dispara o preview em uma thread separada."""
        if not self.dat_path.get().strip():
            self._erro("Selecione um arquivo .dat de entrada.")
            return

        self._alternar_botoes(False)
        self._log("▶ Gerando preview\u2026")
        thread = threading.Thread(target=self._executar_preview, daemon=True)
        thread.start()

    def _executar_preview(self) -> None:
        """Executa o preview em background (roda em thread separada)."""
        try:
            from .utils import preview_csv_preview, format_csv_table

            input_path = Path(self.dat_path.get().strip())
            sps = (
                Path(self.sps_path.get().strip())
                if self.sps_path.get().strip()
                else None
            )
            apply_labels = self.var_apply_labels.get()
            clean = self.var_clean.get()

            n = int(self.preview_rows.get())

            csv_str = preview_csv_preview(
                input_path=input_path,
                sps_path=sps,
                apply_labels=apply_labels,
                clean=clean,
                add_header=True,
                n=n,
            )

            if not csv_str.strip():
                self._log("  (preview vazio — nenhuma linha para exibir)")
            else:
                has_header = bool(self.sps_path.get().strip())
                tabela = format_csv_table(csv_str, max_cols_display=10, has_header=has_header)
                self._log(
                    f"── Preview ({n} linha{'s' if n != 1 else ''}) "
                    f"{'─' * max(0, 40 - len(str(n)))}"
                )
                for linha in tabela.splitlines():
                    self._log(f"  {linha}")

        except Exception as exc:
            self._erro(f"Erro ao gerar preview:\n{exc}")
        finally:
            self.root.after(0, lambda: self._alternar_botoes(True))


def main() -> None:
    """Inicializa e exibe a interface gráfica do dat2csv."""
    root = tk.Tk()
    _ = Dat2CsvGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
