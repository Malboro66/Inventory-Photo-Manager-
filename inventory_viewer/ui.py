"""Interface Tkinter da aplicação de visualização de peças."""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import threading
import queue
from pathlib import Path

from .core import StructuredLogger, ConfigManager, DirectoryCache, ParallelImageLoader, BuscadorService, ThreadManager


class VisualizadorPecas:
    """Interface gráfica principal do sistema v8.1."""

    def __init__(self, root):
        self.root = root
        self.logger = StructuredLogger("VisualizadorPecas")
        self.logger.info("Application starting", event_type="app_start", version="8.1",
                        features=["parallel_loading", "unicode_normalization"])

        self.config_manager = ConfigManager()

        self.root.title("Buscador de Peças Pro - v8.1 ⚡ Unicode+")
        geometry = self.config_manager.get_window_geometry()
        self.root.geometry(geometry)
        self.root.minsize(800, 600)

        self.style = ttk.Style()
        theme = self.config_manager.get("ui", "theme", "clam")
        try:
            self.style.theme_use(theme)
        except:
            self.style.theme_use('clam')

        self.diretorio_raiz = tk.StringVar()
        self.pesquisa_var = tk.StringVar()
        self.imagens_ativas = []
        self.widgets_imagem = []
        self.contador_buscas = 0
        self.last_stats = None

        cache_ttl = self.config_manager.get("general", "cache_ttl_seconds", 300)
        self.dir_cache = DirectoryCache(ttl_seconds=cache_ttl, logger=self.logger)
        self.thread_manager = ThreadManager(logger=self.logger)
        self.fila = queue.Queue()

        self.grid_row = 0
        self.grid_col = 0
        self.max_cols = self.config_manager.get("ui", "max_columns", 3)

        self.criar_interface()
        self.verificar_fila()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        last_dir = self.config_manager.get("general", "last_directory", "")
        if last_dir and Path(last_dir).exists():
            self.diretorio_raiz.set(last_dir)

    def criar_interface(self):
        controle_frame = ttk.Frame(self.root, padding=10)
        controle_frame.pack(fill="x")

        linha1 = ttk.Frame(controle_frame)
        linha1.pack(fill="x", pady=5)

        ttk.Button(linha1, text="📂 Selecionar Pasta", 
                  command=self.selecionar_pasta).pack(side="left", padx=5)
        ttk.Label(linha1, text="Código:").pack(side="left", padx=(20, 5))

        self.combo_pesquisa = ttk.Combobox(linha1, textvariable=self.pesquisa_var, width=30)
        self.combo_pesquisa.pack(side="left", padx=5)
        self.combo_pesquisa.bind("<Return>", lambda e: self.iniciar_busca())

        history = self.config_manager.get_history()
        if history:
            self.combo_pesquisa['values'] = history

        ttk.Button(linha1, text="🔍 Buscar", 
                  command=self.iniciar_busca).pack(side="left", padx=5)

        self.btn_cancelar = ttk.Button(linha1, text="⏹ Cancelar",
                                       command=self.cancelar_busca, state="disabled")
        self.btn_cancelar.pack(side="left", padx=5)

        ttk.Button(linha1, text="❌ Limpar", 
                  command=self.limpar_tudo).pack(side="left", padx=5)

        ttk.Button(linha1, text="⚙️ Config", 
                  command=self.abrir_configuracoes).pack(side="left", padx=5)

        self.progress_frame = ttk.Frame(controle_frame)
        self.progress_frame.pack(fill="x", pady=5)

        self.progress_bar = ttk.Progressbar(self.progress_frame, mode="indeterminate")
        self.lbl_progresso = ttk.Label(self.progress_frame, text="")

        container_scroll = ttk.Frame(self.root)
        container_scroll.pack(fill="both", expand=True, padx=10, pady=5)

        self.canvas = tk.Canvas(container_scroll, bg="white")
        self.scrollbar = ttk.Scrollbar(container_scroll, orient="vertical",
                                       command=self.canvas.yview)

        self.scrollable_frame = tk.Frame(self.canvas, bg="white")
        self.scrollable_frame.bind("<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.canvas.bind_all("<MouseWheel>",
            lambda e: self.canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        self.status_var = tk.StringVar(value="Aguardando... | v8.1 ⚡ Unicode+")
        status_bar = ttk.Label(self.root, textvariable=self.status_var,
                              relief="sunken", anchor="w", padding=(5, 2))
        status_bar.pack(side="bottom", fill="x")

    def selecionar_pasta(self):
        pasta = filedialog.askdirectory(title="Selecione a Pasta Raiz")
        if not pasta:
            return
        try:
            pasta_real = Path(pasta).resolve()
            if not pasta_real.exists():
                messagebox.showerror("Erro", "Diretório não existe")
                return
            self.diretorio_raiz.set(str(pasta_real))
            self.config_manager.set("general", "last_directory", str(pasta_real))
            self.logger.info("Root directory selected", directory=str(pasta_real))
            self.status_var.set(f"📁 {pasta_real.name}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro: {e}")

    def iniciar_busca(self):
        if self.thread_manager.is_running():
            messagebox.showwarning("Aviso", "Busca já em andamento")
            return

        termo = self.pesquisa_var.get().strip()
        if not termo:
            messagebox.showwarning("Aviso", "Digite um código")
            return

        if not self.diretorio_raiz.get():
            messagebox.showwarning("Aviso", "Selecione a pasta raiz")
            return

        self.contador_buscas += 1
        self.config_manager.add_to_history(termo)
        self.combo_pesquisa['values'] = self.config_manager.get_history()
        self.limpar_visualizacao()

        service = BuscadorService(self.fila, self.thread_manager.cancel_event,
                                 self.dir_cache, self.logger, self.config_manager)

        self.thread_manager.start_thread(target=service.buscar_e_carregar,
                                        args=(self.diretorio_raiz.get(), termo),
                                        name=f"Busca-{termo}")

        self.progress_bar.pack(side="left", fill="x", expand=True, padx=5)
        self.progress_bar.start(10)
        self.lbl_progresso.pack(side="left", padx=5)

        mode = "⚡ Paralelo" if self.config_manager.is_parallel_loading_enabled() else "Síncrono"
        self.lbl_progresso.config(text=f"Buscando '{termo}'... ({mode})")
        self.status_var.set("🔍 Carregando...")
        self.root.config(cursor="watch")
        self.btn_cancelar.config(state="normal")

    def cancelar_busca(self):
        if not self.thread_manager.is_running():
            return
        self.btn_cancelar.config(state="disabled")
        self.lbl_progresso.config(text="Cancelando...")
        self.thread_manager.cancel_thread(timeout=3.0)
        self.finalizar_carregamento("❌ Cancelado")

    def limpar_tudo(self):
        self.pesquisa_var.set("")
        self.limpar_visualizacao()
        self.status_var.set("Limpo")

    def limpar_visualizacao(self):
        for widget in self.widgets_imagem:
            try:
                if widget.winfo_exists():
                    widget.config(image='')
            except:
                pass
        self.imagens_ativas.clear()
        self.widgets_imagem.clear()
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        gc.collect()
        self.grid_row = 0
        self.grid_col = 0

    def verificar_fila(self):
        try:
            msg = self.fila.get_nowait()

            if msg["status"] == "found_part":
                tk.Label(self.scrollable_frame, text=f"📦 {msg['nome']}",
                        font=("Arial", 12, "bold"), bg="white").grid(
                    row=self.grid_row, column=0, columnspan=self.max_cols, pady=10)
                self.grid_row += 1

            elif msg["status"] in ["start", "start_parallel"]:
                self.progress_bar.config(mode="determinate", maximum=msg["total"])

            elif msg["status"] == "progress":
                nome, photo, caminho = msg["data"]
                self.adicionar_imagem_grid(nome, photo, caminho)
                self.imagens_ativas.append(photo)
                self.progress_bar['value'] = msg.get("current", 0) + 1

            elif msg["status"] == "done":
                stats = msg.get("stats")
                if stats:
                    self.last_stats = stats
                    status_msg = f"✅ {stats['loaded']} imagens"
                    if stats.get('speedup'):
                        status_msg += f" | Speedup: {stats['speedup']:.1f}x"
                    if stats.get('throughput_imgs_per_sec'):
                        status_msg += f" | {stats['throughput_imgs_per_sec']:.1f} imgs/s"
                    self.finalizar_carregamento(status_msg)
                else:
                    self.finalizar_carregamento(f"✅ {len(self.imagens_ativas)} imagens")

            elif msg["status"] == "cancelled":
                self.finalizar_carregamento("❌ Cancelado")

            elif msg["status"] == "not_found":
                tk.Label(self.scrollable_frame, text="❌ Não encontrado",
                        font=("Arial", 14, "bold"), fg="red", bg="white").grid(
                    row=0, column=0, columnspan=self.max_cols, pady=20)
                self.finalizar_carregamento("❌ Não encontrado")

            elif msg["status"] == "no_images":
                tk.Label(self.scrollable_frame, text="⚠️ Sem imagens",
                        font=("Arial", 12), fg="orange", bg="white").grid(
                    row=0, column=0, columnspan=self.max_cols, pady=20)
                self.finalizar_carregamento("⚠️ Sem imagens")

            elif msg["status"] == "error":
                messagebox.showerror("Erro", msg["msg"])
                self.finalizar_carregamento("❌ Erro")

        except queue.Empty:
            pass

        self.root.after(50, self.verificar_fila)

    def adicionar_imagem_grid(self, nome: str, photo: ImageTk.PhotoImage, caminho: str):
        frame = tk.Frame(self.scrollable_frame, borderwidth=2, relief="groove",
                        bg="white", padx=5, pady=5)
        frame.grid(row=self.grid_row, column=self.grid_col, padx=10, pady=10, sticky="n")

        lbl_img = tk.Label(frame, image=photo, bg="white", cursor="hand2")
        lbl_img.pack()
        lbl_img.bind("<Double-Button-1>", lambda e, p=caminho: self.abrir_visualizador(p))
        self.widgets_imagem.append(lbl_img)

        tk.Label(frame, text=nome, font=("Arial", 8), wraplength=200,
                bg="white").pack(pady=5)

        self.grid_col += 1
        if self.grid_col >= self.max_cols:
            self.grid_col = 0
            self.grid_row += 1

    def abrir_visualizador(self, caminho_imagem: str):
        try:
            path = Path(caminho_imagem)
            if not path.exists():
                messagebox.showerror("Erro", "Arquivo não existe")
                return
            janela = tk.Toplevel(self.root)
            janela.title(f"Visualização: {path.name}")
            janela.geometry("1200x900")
            janela.configure(bg="black")
            img = Image.open(path)
            img.thumbnail((1920, 1080), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            container = tk.Frame(janela, bg="black")
            container.pack(expand=True, fill="both", padx=10, pady=10)
            lbl = tk.Label(container, image=photo, bg="black")
            lbl.image = photo
            lbl.pack(expand=True)
            ttk.Button(janela, text="✖ Fechar (ESC)",
                      command=janela.destroy).pack(pady=10)
            janela.bind("<Escape>", lambda e: janela.destroy())
        except Exception as e:
            messagebox.showerror("Erro", f"Erro: {e}")

    def abrir_configuracoes(self):
        config_win = tk.Toplevel(self.root)
        config_win.title("⚙️ Configurações")
        config_win.geometry("500x650")
        config_win.transient(self.root)
        config_win.grab_set()

        notebook = ttk.Notebook(config_win)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        perf_frame = ttk.Frame(notebook, padding=10)
        notebook.add(perf_frame, text="⚡ Performance")

        parallel_var = tk.BooleanVar(value=self.config_manager.is_parallel_loading_enabled())
        ttk.Checkbutton(perf_frame, text="Habilitar carregamento paralelo (recomendado)",
                       variable=parallel_var).grid(row=0, column=0, columnspan=2, sticky="w", pady=10)

        ttk.Label(perf_frame, text="Workers (threads):").grid(row=1, column=0, sticky="w", pady=5)
        workers_var = tk.StringVar(value=str(self.config_manager.get_max_workers() or "Auto"))
        workers_combo = ttk.Combobox(perf_frame, textvariable=workers_var, width=10)
        workers_combo['values'] = ["Auto", "2", "4", "6", "8", "12", "16"]
        workers_combo.grid(row=1, column=1, sticky="w", padx=10)

        ttk.Label(perf_frame, text="Tamanho thumbnail:").grid(row=2, column=0, sticky="w", pady=5)
        thumb_var = tk.IntVar(value=self.config_manager.get_thumbnail_size())
        thumb_spin = ttk.Spinbox(perf_frame, from_=100, to=500, increment=50, 
                                textvariable=thumb_var, width=10)
        thumb_spin.grid(row=2, column=1, sticky="w", padx=10)

        if self.last_stats:
            stats_frame = ttk.LabelFrame(perf_frame, text="📊 Última Busca", padding=10)
            stats_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=20)
            ttk.Label(stats_frame, text=f"Imagens: {self.last_stats['loaded']}").pack(anchor="w")
            ttk.Label(stats_frame, text=f"Tempo: {self.last_stats['duration_ms']:.0f}ms").pack(anchor="w")
            ttk.Label(stats_frame, text=f"Speedup: {self.last_stats.get('speedup', 1):.2f}x").pack(anchor="w")
            ttk.Label(stats_frame, text=f"Throughput: {self.last_stats.get('throughput_imgs_per_sec', 0):.1f} imgs/s").pack(anchor="w")

        cache_frame = ttk.Frame(notebook, padding=10)
        notebook.add(cache_frame, text="💾 Cache")

        ttk.Label(cache_frame, text="TTL (segundos):").grid(row=0, column=0, sticky="w", pady=5)
        ttl_var = tk.IntVar(value=self.config_manager.get("general", "cache_ttl_seconds", 300))
        ttl_spin = ttk.Spinbox(cache_frame, from_=10, to=3600, increment=30,
                              textvariable=ttl_var, width=10)
        ttl_spin.grid(row=0, column=1, sticky="w", padx=10)

        ttk.Button(cache_frame, text="🗑️ Limpar Cache",
                  command=lambda: self.dir_cache.invalidate()).grid(row=1, column=0, pady=10)

        ui_frame = ttk.Frame(notebook, padding=10)
        notebook.add(ui_frame, text="🎨 Interface")

        ttk.Label(ui_frame, text="Colunas:").grid(row=0, column=0, sticky="w", pady=5)
        cols_var = tk.IntVar(value=self.max_cols)
        cols_spin = ttk.Spinbox(ui_frame, from_=1, to=6, textvariable=cols_var, width=10)
        cols_spin.grid(row=0, column=1, sticky="w", padx=10)

        ttk.Label(ui_frame, text="Tema:").grid(row=1, column=0, sticky="w", pady=5)
        theme_var = tk.StringVar(value=self.config_manager.get("ui", "theme", "clam"))
        theme_combo = ttk.Combobox(ui_frame, textvariable=theme_var, width=10)
        theme_combo['values'] = self.style.theme_names()
        theme_combo.grid(row=1, column=1, sticky="w", padx=10)

        btn_frame = ttk.Frame(config_win)
        btn_frame.pack(fill="x", padx=10, pady=10)

        def salvar():
            self.config_manager.set("performance", "enable_parallel_loading", parallel_var.get())
            workers_val = workers_var.get()
            if workers_val == "Auto":
                self.config_manager.set("performance", "max_workers", None)
            else:
                self.config_manager.set("performance", "max_workers", int(workers_val))
            self.config_manager.set("performance", "thumbnail_size", thumb_var.get())
            self.config_manager.set("general", "cache_ttl_seconds", ttl_var.get())
            self.max_cols = cols_var.get()
            self.config_manager.set("ui", "max_columns", cols_var.get())
            self.config_manager.set("ui", "theme", theme_var.get())
            try:
                self.style.theme_use(theme_var.get())
            except:
                pass
            self.config_manager.save()
            messagebox.showinfo("Sucesso", "Configurações salvas!")
            config_win.destroy()

        ttk.Button(btn_frame, text="💾 Salvar", command=salvar).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="❌ Cancelar", command=config_win.destroy).pack(side="right")

    def finalizar_carregamento(self, msg: str):
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.lbl_progresso.pack_forget()
        self.status_var.set(msg)
        self.root.config(cursor="")
        self.btn_cancelar.config(state="disabled")

    def on_closing(self):
        self.logger.info("Application closing", event_type="app_stop")
        try:
            geometry = self.root.geometry()
            self.config_manager.update_window_geometry(geometry)
        except:
            pass
        if self.thread_manager.is_running():
            self.thread_manager.cancel_thread(timeout=3.0)
        self.thread_manager.cleanup()
        self.limpar_visualizacao()
        self.logger.log_metrics_summary()
        gc.collect()
        self.root.destroy()




def run_app():
    root = tk.Tk()
    app = VisualizadorPecas(root)
    root.mainloop()
