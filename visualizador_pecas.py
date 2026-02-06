import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import os
import threading
import queue
import unicodedata  # Necessário para a busca melhorada

class BuscadorService:
    """
    Responsável pela lógica de busca e carregamento de arquivos (Background).
    """
    def __init__(self, fila_resultados):
        self.fila = fila_resultados

    def _normalizar_texto(self, texto):
        """
        Remove acentos e caracteres especiais para facilitar a busca.
        Ex: 'Peçã' vira 'Peca', 'Café' vira 'Cafe'.
        """
        nfkd_form = unicodedata.normalize('NFKD', texto)
        return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])

    def buscar_e_carregar(self, diretorio_raiz, termo_busca):
        """
        Procura a pasta e carrega as imagens em background.
        Lógica de Busca Aprimorada:
        1. Remove acentos do termo de busca.
        2. Remove acentos dos nomes das pastas.
        3. Tenta correspondência exata primeiro.
        4. Caso não ache, tenta correspondência parcial (contém).
        """
        caminho_pasta = None
        nome_peca_encontrada = ""
        
        # Normaliza o termo de busca (remove acentos e lowercase)
        termo_normalizado = self._normalizar_texto(termo_busca).lower().strip()
        
        if not os.path.exists(diretorio_raiz):
            self.fila.put({"status": "error", "msg": "Diretório raiz não encontrado."})
            return

        if not termo_normalizado:
            self.fila.put({"status": "error", "msg": "Termo de busca vazio."})
            return

        # 1. Lógica de Busca
        try:
            match_parcial = None  # Guarda a melhor opção parcial se a exata falhar
            
            for pasta in os.listdir(diretorio_raiz):
                caminho_completo = os.path.join(diretorio_raiz, pasta)
                
                if os.path.isdir(caminho_completo):
                    # Normaliza o nome da pasta para comparação
                    pasta_normalizada = self._normalizar_texto(pasta).lower()
                    
                    # Prioridade 1: Correspondência Exata (ignorando acentos)
                    if pasta_normalizada == termo_normalizado:
                        caminho_pasta = caminho_completo
                        nome_peca_encontrada = pasta
                        break  # Para o loop, achou o perfeito
                    
                    # Prioridade 2: Correspondência Parcial (Fuzzy Search)
                    # Verifica se o termo digitado está contido no nome da pasta
                    if termo_normalizado in pasta_normalizada:
                        # Se ainda não temos um parcial, salva este
                        if match_parcial is None:
                            match_parcial = (caminho_completo, pasta)
            
            # Se não achou exato, mas achou parcial, usa o parcial
            if not caminho_pasta and match_parcial:
                caminho_pasta, nome_peca_encontrada = match_parcial
            elif not caminho_pasta:
                self.fila.put({"status": "not_found"})
                return
                
        except Exception as e:
            self.fila.put({"status": "error", "msg": f"Erro ao ler pastas: {str(e)}"})
            return

        # 2. Carregamento de Imagens
        try:
            arquivos = os.listdir(caminho_pasta)
            extensoes = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')
            imagens = [f for f in arquivos if f.lower().endswith(extensoes)]
            
            total = len(imagens)
            if total == 0:
                self.fila.put({"status": "no_images"})
                return

            self.fila.put({"status": "start", "total": total, "nome": nome_peca_encontrada})

            for i, arquivo in enumerate(imagens):
                caminho_img = os.path.join(caminho_pasta, arquivo)
                
                try:
                    # Carrega e redimensiona (Thumbnail para a grade)
                    img = Image.open(caminho_img)
                    img.thumbnail((250, 250)) 
                    
                    # Converte para PhotoImage
                    photo = ImageTk.PhotoImage(img)
                    
                    # Envia para a UI thread
                    self.fila.put({
                        "status": "progress",
                        "data": (arquivo, photo, caminho_img),
                        "current": i,
                        "total": total
                    })
                except Exception as e:
                    # Emite erro individual, mas não para o processo
                    self.fila.put({
                        "status": "warning", 
                        "msg": f"Erro ao carregar {arquivo}: {str(e)}"
                    })
            
            self.fila.put({"status": "done"})

        except Exception as e:
            self.fila.put({"status": "error", "msg": f"Erro ao listar imagens: {str(e)}"})


class VisualizadorPecas:
    def __init__(self, root):
        self.root = root
        self.root.title("Buscador de Peças Pro - Inventory Photo Manager")
        self.root.geometry("1100x800")
        self.root.minsize(800, 600)
        
        # Configuração de Estilo (Tema)
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("TButton", font=("Arial", 10))
        self.style.configure("TLabel", font=("Arial", 10))
        self.style.configure("Header.TLabel", font=("Arial", 12, "bold"))

        # Variáveis de Controle
        self.diretorio_raiz = tk.StringVar()
        self.pesquisa_var = tk.StringVar()
        self.imagens_ativas = []
        self.worker_thread = None
        self.fila = queue.Queue()
        
        # Controle de Grid e UI
        self.grid_row = 0
        self.grid_col = 0
        self.max_cols = 3 
        
        # Controle de concorrência (evitar buscas duplas)
        self.is_busy = False

        # Interface
        self.criar_interface()
        
        # Inicia o loop de verificação da fila
        self.verificar_fila()

    def criar_interface(self):
        # --- Topo: Controles ---
        controle_frame = ttk.Frame(self.root, padding=10)
        controle_frame.pack(fill="x")

        # Linha 1: Pasta, Busca e Limpar
        linha1 = ttk.Frame(controle_frame)
        linha1.pack(fill="x", pady=5)

        ttk.Button(linha1, text="📂 Selecionar Pasta Raiz", command=self.selecionar_pasta).pack(side="left", padx=5)
        
        ttk.Label(linha1, text="Código da Peça:").pack(side="left", padx=(20, 5))
        
        self.combo_pesquisa = ttk.Combobox(
            linha1, 
            textvariable=self.pesquisa_var, 
            width=30, 
            font=("Arial", 10),
            state="readonly" # Começa readonly, muda para normal ao carregar pasta
        )
        self.combo_pesquisa.pack(side="left", padx=5)
        self.combo_pesquisa.bind("<Return>", lambda e: self.iniciar_busca())
        self.combo_pesquisa.bind("<<ComboboxSelected>>", lambda e: self.iniciar_busca())
        
        ttk.Button(linha1, text="🔍 Buscar", command=self.iniciar_busca).pack(side="left", padx=5)
        ttk.Button(linha1, text="❌ Limpar", command=self.limpar_tudo).pack(side="left", padx=5)

        # Barra de Progresso (Invisível inicialmente)
        self.progress_frame = ttk.Frame(controle_frame)
        self.progress_frame.pack(fill="x", pady=5)
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, mode="indeterminate")
        self.lbl_progresso = ttk.Label(self.progress_frame, text="")

        # --- Meio: Área de Scroll ---
        container_scroll = ttk.Frame(self.root)
        container_scroll.pack(fill="both", expand=True, padx=10, pady=5)

        self.canvas = tk.Canvas(container_scroll, bg="white")
        self.scrollbar = ttk.Scrollbar(container_scroll, orient="vertical", command=self.canvas.yview)
        
        # CORREÇÃO PYTHON 3.14: tk.Frame para permitir bg="white"
        self.scrollable_frame = tk.Frame(self.canvas, bg="white")
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Suporte a Mouse Wheel
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # --- Rodapé: Status ---
        self.status_var = tk.StringVar(value="Aguardando seleção de pasta...")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief="sunken", anchor="w")
        status_bar.pack(side="bottom", fill="x")

    def selecionar_pasta(self):
        pasta = filedialog.askdirectory(title="Selecione a pasta onde estão as pastas das peças")
        if pasta:
            self.diretorio_raiz.set(pasta)
            self.atualizar_lista_pecas(pasta)

    def atualizar_lista_pecas(self, caminho_pasta):
        """Varre a pasta raiz, encontra as subpastas (peças) e popula o Combobox."""
        try:
            self.combo_pesquisa['values'] = []
            self.pesquisa_var.set("") # Limpa o texto
            
            pastas_encontradas = []
            for item in os.listdir(caminho_pasta):
                item_path = os.path.join(caminho_pasta, item)
                if os.path.isdir(item_path):
                    pastas_encontradas.append(item)
            
            pastas_encontradas.sort()
            
            self.combo_pesquisa['values'] = pastas_encontradas
            
            # CORREÇÃO CRÍTICA: Define como 'normal' para permitir digitação
            self.combo_pesquisa.config(state="normal")
            
            quantidade = len(pastas_encontradas)
            self.status_var.set(f"Pasta carregada: {os.path.basename(caminho_pasta)} | {quantidade} peças disponíveis.")
            
            if quantidade > 0:
                self.combo_pesquisa.focus() # Coloca o foco no campo de busca
            else:
                messagebox.showinfo("Aviso", "Nenhuma subpasta encontrada na pasta selecionada.")

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao listar peças:\n{e}")

    def limpar_tudo(self):
        """Limpa a busca e a área de visualização."""
        self.pesquisa_var.set("")
        self.limpar_visualizacao()
        self.status_var.set("Busca limpa.")

    def iniciar_busca(self):
        if self.is_busy:
            return

        termo = self.pesquisa_var.get().strip()
        if not termo:
            messagebox.showwarning("Aviso", "Selecione ou digite um código de peça.")
            return
        
        if not self.diretorio_raiz.get():
            messagebox.showwarning("Aviso", "Selecione a pasta raiz primeiro.")
            return

        self.is_busy = True
        self.limpar_visualizacao()
        
        self.worker_thread = threading.Thread(
            target=self._worker_target, 
            args=(termo,), 
            daemon=True
        )
        self.worker_thread.start()

        # Atualiza UI para estado de carregamento
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=5)
        self.progress_bar.start(10)
        self.lbl_progresso.pack(side="left", padx=5)
        self.lbl_progresso.config(text=f"Buscando por '{termo}'...")
        self.status_var.set("Carregando imagens... (Dê duplo clique para ampliar)")
        self.root.config(cursor="watch")

    def _worker_target(self, termo):
        """Função executada na thread separada."""
        service = BuscadorService(self.fila)
        service.buscar_e_carregar(self.diretorio_raiz.get(), termo)

    def limpar_visualizacao(self):
        """Destroi todos os widgets do grid e limpa memória."""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.imagens_ativas.clear()
        self.grid_row = 0
        self.grid_col = 0

    def verificar_fila(self):
        """Verifica mensagens da thread de background e atualiza a UI."""
        try:
            msg = self.fila.get_nowait()
            
            if msg["status"] == "start":
                # Usa grid para o título (evita conflito com pack/grid)
                tk.Label(
                    self.scrollable_frame, 
                    text=f"Resultados para: {msg['nome']}", 
                    font=("Arial", 12, "bold"),
                    bg="white"
                ).grid(row=self.grid_row, column=0, columnspan=self.max_cols, pady=10, sticky="ew")
                
                self.grid_row += 1 # Pula para a próxima linha para as imagens
                
                self.progress_bar.config(mode="determinate", maximum=msg["total"])
                self.progress_bar['value'] = 0

            elif msg["status"] == "progress":
                nome_arquivo, photo, caminho_completo = msg["data"]
                self.adicionar_imagem_grid(nome_arquivo, photo, caminho_completo)
                self.imagens_ativas.append(photo)
                
                self.progress_bar['value'] = msg["current"] + 1
                self.lbl_progresso.config(text=f"Carregando: {msg['current']+1}/{msg['total']}")

            elif msg["status"] == "done":
                self.finalizar_carregamento("Imagens carregadas com sucesso!")
            
            elif msg["status"] == "not_found":
                tk.Label(self.scrollable_frame, text="Peça não encontrada.", font=("Arial", 14), fg="red", bg="white").grid(row=0, column=0, columnspan=self.max_cols, pady=20)
                self.finalizar_carregamento("Peça não encontrada no índice.")
            
            elif msg["status"] == "no_images":
                tk.Label(self.scrollable_frame, text="Pasta encontrada, mas sem imagens.", bg="white").grid(row=0, column=0, columnspan=self.max_cols, pady=20)
                self.finalizar_carregamento("Pasta vazia.")
            
            elif msg["status"] == "warning":
                print(f"Aviso: {msg['msg']}")

            elif msg["status"] == "error":
                messagebox.showerror("Erro", msg["msg"])
                self.finalizar_carregamento("Erro ao processar.")

        except queue.Empty:
            pass
        
        self.root.after(50, self.verificar_fila)

    def adicionar_imagem_grid(self, nome_arquivo, photo, caminho_completo):
        """Cria os widgets da imagem e os posiciona no grid."""
        # Usa tk.Frame para controle de background e bordas
        frame_item = tk.Frame(self.scrollable_frame, borderwidth=2, relief="groove", bg="white")
        frame_item.grid(row=self.grid_row, column=self.grid_col, padx=10, pady=10)

        # Imagem (CORREÇÃO: Usar tk.Label para bg="white")
        lbl_img = tk.Label(frame_item, image=photo, bg="white")
        lbl_img.pack()
        
        # Duplo Clique para Abrir
        lbl_img.bind("<Double-Button-1>", lambda e, path=caminho_completo: self.abrir_visualizador(path))

        # Nome do arquivo (CORREÇÃO: Usar tk.Label para bg="white")
        lbl_texto = tk.Label(frame_item, text=nome_arquivo, font=("Arial", 8), wraplength=200, bg="white")
        lbl_texto.pack(pady=5)

        # Atualiza contadores do grid
        self.grid_col += 1
        if self.grid_col >= self.max_cols:
            self.grid_col = 0
            self.grid_row += 1

    def abrir_visualizador(self, caminho_imagem):
        """Abre uma nova janela com a imagem em tamanho grande para conferência."""
        try:
            janela_visualizacao = tk.Toplevel(self.root)
            janela_visualizacao.title(f"Visualização: {os.path.basename(caminho_imagem)}")
            janela_visualizacao.geometry("1200x900")
            
            img_original = Image.open(caminho_imagem)
            # Redimensiona para caber na tela mantendo qualidade (Full HD Max)
            img_original.thumbnail((1920, 1080), Image.Resampling.LANCZOS)
            
            photo_visual = ImageTk.PhotoImage(img_original)
            
            # Frame container para garantir centralização
            container_visual = tk.Frame(janela_visualizacao, bg="black")
            container_visual.pack(expand=True, fill="both", padx=10, pady=10)
            
            # Label centralizado com a imagem
            lbl_visual = tk.Label(container_visual, image=photo_visual, bg="black")
            lbl_visual.image = photo_visual # Mantém referência
            lbl_visual.pack(expand=True) # O expand com anchor padrão centraliza verticalmente
            
            # Botão para fechar
            btn_fechar = ttk.Button(janela_visualizacao, text="Fechar (ESC)", command=janela_visualizacao.destroy)
            btn_fechar.pack(pady=10)
            
            janela_visualizacao.bind("<Escape>", lambda e: janela_visualizacao.destroy())

        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir a imagem:\n{e}")

    def finalizar_carregamento(self, mensagem_status):
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.lbl_progresso.pack_forget()
        self.status_var.set(mensagem_status)
        self.is_busy = False
        self.root.config(cursor="")

if __name__ == "__main__":
    root = tk.Tk()
    app = VisualizadorPecas(root)
    root.mainloop()