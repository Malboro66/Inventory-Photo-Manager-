import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import os

class VisualizadorPecas:
    def __init__(self, root):
        self.root = root
        self.root.title("Inventory Photo Manager - Seleção e Cópia")
        self.root.geometry("1000x700")

        # Dicionário que mapeia o ID do item na Treeview (iid) para o Caminho Real da Pasta
        self.tree_paths = {}
        self.diretorio_raiz = ""
        
        # Lista para manter as referências das imagens na memória
        self.imagens_ativas = []

        # Dicionário para rastrear fotos selecionadas: {widget_frame: caminho_arquivo}
        self.fotos_selecionadas = {}

        # --- Elementos da Interface (Topo) ---
        self.frame_controle = tk.Frame(root, pady=10, bg="#f0f0f0")
        self.frame_controle.pack(fill="x")

        self.btn_selecionar = tk.Button(self.frame_controle, text="📂 Selecionar Pasta", command=self.selecionar_pasta, bg="#dddddd", font=("Arial", 10))
        self.btn_selecionar.pack(side="left", padx=10)

        self.lbl_pesquisa = tk.Label(self.frame_controle, text="Buscar:", bg="#f0f0f0", font=("Arial", 10))
        self.lbl_pesquisa.pack(side="left", padx=5)
        
        self.entrada_pesquisa = tk.Entry(self.frame_controle, width=30, font=("Arial", 10))
        self.entrada_pesquisa.pack(side="left", padx=5)
        self.entrada_pesquisa.bind("<Return>", self.executar_busca) 
        self.entrada_pesquisa.bind("<KeyRelease>", self.filtrar_arvore) 

        self.btn_buscar = tk.Button(self.frame_controle, text="🔍 Buscar", command=self.executar_busca, bg="#4CAF50", fg="white", font=("Arial", 10, "bold"))
        self.btn_buscar.pack(side="left", padx=5)

        # NOVO: Botão Copiar
        self.btn_copiar = tk.Button(self.frame_controle, text="📋 Copiar Selecionados", command=self.copiar_selecionados, bg="#2196F3", fg="white", font=("Arial", 10, "bold"))
        self.btn_copiar.pack(side="right", padx=10)

        # --- Área Principal ---
        self.paned_window = tk.PanedWindow(root, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        self.paned_window.pack(fill="both", expand=True, padx=10, pady=5)

        # 1. Painel da Esquerda: Árvore
        self.frame_lista = tk.Frame(self.paned_window, bg="white", width=250)
        self.paned_window.add(self.frame_lista, minsize=200)

        tk.Label(self.frame_lista, text="Estrutura de Pastas", font=("Arial", 12, "bold"), bg="#e0e0e0").pack(fill="x", pady=5)

        self.trv = ttk.Treeview(self.frame_lista, columns=("nome",), show='tree headings', height=25)
        self.trv.heading("nome", text="Nome da Pasta")
        self.trv.column("nome", width=200, anchor='w')
        self.scrollbar_lista = ttk.Scrollbar(self.frame_lista, orient=tk.VERTICAL, command=self.trv.yview)
        self.trv.configure(yscroll=self.scrollbar_lista.set)
        self.trv.pack(side="left", fill="both", expand=True)
        self.scrollbar_lista.pack(side="right", fill="y")
        self.trv.bind("<<TreeviewSelect>>", self.on_selecionar_arvore)

        # 2. Painel da Direita: Fotos
        self.frame_fotos = tk.Frame(self.paned_window, bg="white")
        self.paned_window.add(self.frame_fotos, minsize=400)

        self.canvas = tk.Canvas(self.frame_fotos, bg="white")
        self.scrollbar_fotos = tk.Scrollbar(self.frame_fotos, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="white")

        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar_fotos.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar_fotos.pack(side="right", fill="y")

        self.status_label = tk.Label(root, text="Nenhuma pasta selecionada.", bd=1, relief=tk.SUNKEN, anchor=tk.W, font=("Arial", 9))
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

    def selecionar_pasta(self):
        pasta = filedialog.askdirectory()
        if pasta:
            self.diretorio_raiz = pasta
            self.construir_arvore()
            self.status_label.config(text=f"Pasta carregada: {pasta}")
            messagebox.showinfo("Sucesso", "Estrutura de pastas carregada!")

    def construir_arvore(self):
        for item in self.trv.get_children():
            self.trv.delete(item)
        self.tree_paths.clear()

        def _inserir_no(pai_id, caminho_pasta):
            try:
                with os.scandir(caminho_pasta) as entradas:
                    for entrada in entradas:
                        if entrada.is_dir():
                            novo_id = self.trv.insert(pai_id, tk.END, text=entrada.name, values=(entrada.name,))
                            self.tree_paths[novo_id] = entrada.path
                            _inserir_no(novo_id, entrada.path)
            except PermissionError:
                pass

        _inserir_no("", self.diretorio_raiz)

    def expandir_pais(self, item_id):
        parent_id = self.trv.parent(item_id)
        if parent_id:
            self.trv.item(parent_id, open=True)
            self.expandir_pais(parent_id)

    def filtrar_arvore(self, event=None):
        termo = self.entrada_pesquisa.get().strip().lower()
        if not termo:
            return
        selection = self.trv.selection()
        if selection:
            self.trv.selection_remove(selection)
        for iid, caminho in self.tree_paths.items():
            nome_pasta = os.path.basename(caminho)
            if termo in nome_pasta.lower():
                self.trv.selection_set(iid)
                self.trv.see(iid)
                self.expandir_pais(iid)
                break

    def executar_busca(self, event=None):
        selection = self.trv.selection()
        if selection:
            self.on_selecionar_arvore(None)

    def on_selecionar_arvore(self, event):
        selected_items = self.trv.selection()
        if selected_items:
            item_id = selected_items[0]
            caminho_pasta = self.tree_paths.get(item_id)
            if caminho_pasta and os.path.exists(caminho_pasta):
                nome_peca = os.path.basename(caminho_pasta)
                self.entrada_pesquisa.delete(0, tk.END)
                self.entrada_pesquisa.insert(0, nome_peca)
                self.exibir_fotos(caminho_pasta, nome_peca)
                self.status_label.config(text=f"Exibindo: {caminho_pasta}")

    # --- NOVA FUNÇÃO: Alternar Seleção ---
    def toggle_selecao(self, event, frame_widget, caminho_arquivo):
        """Adiciona ou remove a foto da lista de seleção quando clicada"""
        if frame_widget in self.fotos_selecionadas:
            # Já estava selecionado, remove
            del self.fotos_selecionadas[frame_widget]
            frame_widget.config(relief="groove", borderwidth=2, bg="white") # Volta ao normal
        else:
            # Não estava selecionado, adiciona
            self.fotos_selecionadas[frame_widget] = caminho_arquivo
            frame_widget.config(relief="solid", borderwidth=4, bg="#ffcccc") # Fica vermelho (selecionado)

    # --- NOVA FUNÇÃO: Copiar Selecionados ---
    def copiar_selecionados(self):
        """Copia os caminhos das fotos selecionadas para o clipboard"""
        if not self.fotos_selecionadas:
            messagebox.showwarning("Aviso", "Nenhuma foto selecionada.\nClique nas fotos para selecioná-las (borda vermelha).")
            return

        # Pega apenas os caminhos (valores do dicionário)
        caminhos = list(self.fotos_selecionadas.values())
        
        # Junta os caminhos com quebra de linha
        texto_para_copiar = "\n".join(caminhos)
        
        # Copia para a área de transferência
        self.root.clipboard_clear()
        self.root.clipboard_append(texto_para_copiar)
        self.root.update() # Força a atualização do clipboard
        
        messagebox.showinfo("Copiado", f"{len(caminhos)} fotos copiadas para a área de transferência!")

    def exibir_fotos(self, caminho_pasta, nome_peca):
        """Carrega e exibe as imagens"""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.imagens_ativas.clear()
        
        # Limpa seleções anteriores ao trocar de pasta
        self.fotos_selecionadas.clear()

        try:
            arquivos = os.listdir(caminho_pasta)
        except Exception as e:
            tk.Label(self.scrollable_frame, text=f"Erro ao ler pasta: {e}", bg="white", fg="red").grid(row=0, column=0, pady=10)
            return

        extensoes_validas = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')
        imagens_encontradas = [f for f in arquivos if f.lower().endswith(extensoes_validas)]

        if not imagens_encontradas:
            tk.Label(self.scrollable_frame, text="Esta pasta não contém imagens.", bg="white").grid(row=0, column=0, pady=10)
            return

        tk.Label(self.scrollable_frame, text=f"Pasta: {nome_peca}", font=("Arial", 16, "bold"), bg="white").grid(row=0, column=0, columnspan=3, pady=10)

        coluna = 0
        linha = 1
        
        for arquivo_img in imagens_encontradas:
            caminho_img = os.path.join(caminho_pasta, arquivo_img)
            
            try:
                img_original = Image.open(caminho_img)
                img_original.thumbnail((200, 200)) 
                photo = ImageTk.PhotoImage(img_original)
                self.imagens_ativas.append(photo)

                frame_img = tk.Frame(self.scrollable_frame, borderwidth=2, relief="groove", bg="white")
                frame_img.grid(row=linha, column=coluna, padx=10, pady=10)

                # --- BIND DO CLIQUE ---
                # Passamos o próprio frame_img e o caminho para a função de toggle
                frame_img.bind("<Button-1>", lambda e, f=frame_img, p=caminho_img: self.toggle_selecao(e, f, p))

                label_img = tk.Label(frame_img, image=photo, bg="white")
                label_img.pack()
                # Se clicar na label, propaga o evento para o frame (opcional, mas ajuda)
                label_img.bind("<Button-1>", lambda e, f=frame_img, p=caminho_img: self.toggle_selecao(e, f, p))

                label_nome = tk.Label(frame_img, text=arquivo_img, font=("Arial", 8), wraplength=180, bg="white")
                label_nome.pack()

                coluna += 1
                if coluna > 2:
                    coluna = 0
                    linha += 1

            except Exception as e:
                print(f"Erro ao carregar imagem {arquivo_img}: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = VisualizadorPecas(root)
    root.mainloop()