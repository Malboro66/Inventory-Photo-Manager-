import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import os

class VisualizadorPecas:
    def __init__(self, root):
        self.root = root
        self.root.title("Inventory Photo Manager - Lista e Busca")
        self.root.geometry("1000x700")

        # Dicionário para armazenar o mapeamento: Nome da Peça -> Caminho da Pasta
        self.mapa_pecas = {}
        self.diretorio_raiz = ""
        
        # Lista para manter as referências das imagens na memória
        self.imagens_ativas = []

        # --- Elementos da Interface (Topo) ---
        self.frame_controle = tk.Frame(root, pady=10, bg="#f0f0f0")
        self.frame_controle.pack(fill="x")

        self.btn_selecionar = tk.Button(self.frame_controle, text="📂 Selecionar Pasta das Peças", command=self.selecionar_pasta, bg="#dddddd", font=("Arial", 10))
        self.btn_selecionar.pack(side="left", padx=10)

        self.lbl_pesquisa = tk.Label(self.frame_controle, text="Código da Peça:", bg="#f0f0f0", font=("Arial", 10))
        self.lbl_pesquisa.pack(side="left", padx=5)
        
        self.entrada_pesquisa = tk.Entry(self.frame_controle, width=30, font=("Arial", 10))
        self.entrada_pesquisa.pack(side="left", padx=5)
        self.entrada_pesquisa.bind("<Return>", self.buscar_peca) 
        self.entrada_pesquisa.bind("<KeyRelease>", self.filtrar_lista) # Filtra a lista enquanto digita

        self.btn_buscar = tk.Button(self.frame_controle, text="🔍 Buscar", command=self.buscar_peca, bg="#4CAF50", fg="white", font=("Arial", 10, "bold"))
        self.btn_buscar.pack(side="left", padx=5)

        # --- Área Principal (Dividida em Esquerda e Direita) ---
        self.paned_window = tk.PanedWindow(root, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        self.paned_window.pack(fill="both", expand=True, padx=10, pady=5)

        # 1. Painel da Esquerda: Lista de Pastas
        self.frame_lista = tk.Frame(self.paned_window, bg="white", width=250)
        self.paned_window.add(self.frame_lista, minsize=200)

        tk.Label(self.frame_lista, text="Lista de Peças", font=("Arial", 12, "bold"), bg="#e0e0e0").pack(fill="x", pady=5)

        # Treeview para a lista
        self.trv = ttk.Treeview(self.frame_lista, columns=("codigo"), show='headings', height=25)
        self.trv.heading("codigo", text="Código / Nome")
        self.trv.column("codigo", width=200, anchor='w')
        
        # Scrollbar para a lista
        self.scrollbar_lista = ttk.Scrollbar(self.frame_lista, orient=tk.VERTICAL, command=self.trv.yview)
        self.trv.configure(yscroll=self.scrollbar_lista.set)
        
        self.trv.pack(side="left", fill="both", expand=True)
        self.scrollbar_lista.pack(side="right", fill="y")

        # Evento de clique na lista
        self.trv.bind("<<TreeviewSelect>>", self.on_selecionar_lista)

        # 2. Painel da Direita: Visualização de Fotos
        self.frame_fotos = tk.Frame(self.paned_window, bg="white")
        self.paned_window.add(self.frame_fotos, minsize=400)

        # Canvas com Scroll para as fotos
        self.canvas = tk.Canvas(self.frame_fotos, bg="white")
        self.scrollbar_fotos = tk.Scrollbar(self.frame_fotos, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="white")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar_fotos.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar_fotos.pack(side="right", fill="y")

        # Label de Status
        self.status_label = tk.Label(root, text="Nenhuma pasta selecionada.", bd=1, relief=tk.SUNKEN, anchor=tk.W, font=("Arial", 9))
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

    def selecionar_pasta(self):
        """Abre o diálogo para selecionar a pasta raiz"""
        pasta = filedialog.askdirectory()
        if pasta:
            self.diretorio_raiz = pasta
            self.indexar_pecas()
            self.status_label.config(text=f"Pasta carregada: {pasta} | {len(self.mapa_pecas)} peças encontradas.")
            messagebox.showinfo("Sucesso", f"Indexação concluída!\nForam encontradas {len(self.mapa_pecas)} pastas de peças.")

    def indexar_pecas(self):
        """Lê todas as subpastas, cria o índice e popula a lista visual"""
        self.mapa_pecas.clear()
        
        # Limpa a lista visual (Treeview)
        for item in self.trv.get_children():
            self.trv.delete(item)
            
        try:
            lista_pastas = []
            # CORREÇÃO: Variável definida como nome_pasta
            for nome_pasta in os.listdir(self.diretorio_raiz):
                caminho_completo = os.path.join(self.diretorio_raiz, nome_pasta)
                if os.path.isdir(caminho_completo):
                    self.mapa_pecas[nome_pasta.lower()] = caminho_completo
                    # CORREÇÃO: Adiciona a variável correta à lista
                    lista_pastas.append(nome_pasta) 
            
            # Ordena alfabeticamente e insere na Treeview
            lista_pastas.sort()
            for p in lista_pastas:
                self.trv.insert("", tk.END, values=(p,))
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao ler pastas: {e}")

    def filtrar_lista(self, event=None):
        """Filtra a lista da esquerda baseado no que é digitado na busca"""
        termo = self.entrada_pesquisa.get().strip().lower()
        
        # Remove destaque atual
        for item in self.trv.get_children():
            self.trv.item(item, tags=())
            
        # Se estiver vazio, mostra tudo (ou restaura a visão original se tivéssemos ocultado)
        # Para simplificar, vamos apenas selecionar o primeiro que bater
        if termo:
            for item in self.trv.get_children():
                valores = self.trv.item(item, "values")
                if valores and valores[0].lower().startswith(termo):
                    self.trv.selection_set(item)
                    self.trv.see(item)
                    break

    def on_selecionar_lista(self, event):
        """Evento acionado ao clicar em um item na lista da esquerda"""
        selected_items = self.trv.selection()
        if selected_items:
            item = selected_items[0]
            codigo = self.trv.item(item, "values")[0]
            
            # Preenche a busca e executa
            self.entrada_pesquisa.delete(0, tk.END)
            self.entrada_pesquisa.insert(0, codigo)
            self.buscar_peca()

    def buscar_peca(self, event=None):
        """Procura a peça no índice e exibe as fotos"""
        termo = self.entrada_pesquisa.get().strip().lower()
        
        # Limpa a área de visualização anterior
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.imagens_ativas.clear()

        if not termo:
            return

        if termo in self.mapa_pecas:
            caminho_pasta = self.mapa_pecas[termo]
            self.exibir_fotos(caminho_pasta, termo)
            self.status_label.config(text=f"Exibindo imagens para: {termo}")
        else:
            self.status_label.config(text=f"Peça '{termo}' não encontrada.")
            lbl_erro = tk.Label(self.scrollable_frame, text=f"Nenhuma pasta encontrada com o nome '{termo}'", font=("Arial", 14), fg="red", bg="white")
            lbl_erro.pack(pady=20)

    def exibir_fotos(self, caminho_pasta, nome_peca):
        """Carrega e exibe as imagens da pasta encontrada"""
        arquivos = os.listdir(caminho_pasta)
        extensoes_validas = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')
        imagens_encontradas = [f for f in arquivos if f.lower().endswith(extensoes_validas)]

        if not imagens_encontradas:
            tk.Label(self.scrollable_frame, text="Esta pasta não contém imagens válidas.", bg="white").pack()
            return

        # Título da pasta encontrada
        tk.Label(self.scrollable_frame, text=f"Código: {nome_peca.upper()}", font=("Arial", 16, "bold"), bg="white").pack(pady=10)

        # Grid para exibir imagens
        coluna = 0
        linha = 0
        
        for arquivo_img in imagens_encontradas:
            caminho_img = os.path.join(caminho_pasta, arquivo_img)
            
            try:
                # Abrir e redimensionar imagem usando Pillow
                img_original = Image.open(caminho_img)
                img_original.thumbnail((200, 200)) 
                photo = ImageTk.PhotoImage(img_original)
                
                self.imagens_ativas.append(photo)

                # Criar o widget na interface
                frame_img = tk.Frame(self.scrollable_frame, borderwidth=2, relief="groove", bg="white")
                frame_img.grid(row=linha, column=coluna, padx=10, pady=10)

                label_img = tk.Label(frame_img, image=photo, bg="white")
                label_img.pack()

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