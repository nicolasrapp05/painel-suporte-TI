import json
import os
import pymysql
from pymysql.constants import CLIENT
import warnings
import customtkinter as ctk
from tkinter import messagebox
from cryptography.fernet import Fernet

# Esconde o aviso de banco de dados antigo
warnings.filterwarnings("ignore", category=UserWarning, module="pymysql")

# =======================================================================
# 1. CONFIGURAÇÃO DE QUERIES
# Para adicionar uma nova query, basta criar um novo bloco aqui!
# =======================================================================
ROTINAS = {
    "Excluir Entrada (Aberta/Fechada)": {
        "arquivo": os.path.join('Queries', 'excluir_entrada.sql'),
        "parametros": [
            # O 'var_banco' deve ser EXATAMENTE o nome da variável @ no SQL (sem o @)
            {"var_banco": "codpceentrada", "label": "Código da Entrada:", "tipo": "texto"},
            {"var_banco": "codfuncionario", "label": "Código do Funcionário (Log):", "tipo": "texto"},
            {"var_banco": "confirmacomfinanceiro", "label": "Ignorar aviso de Financeiro?", "tipo": "opcao", "opcoes": ["True", "False"]},
            {"var_banco": "confirmacomsaida", "label": "Ignorar aviso de Saída?", "tipo": "opcao", "opcoes": ["True", "False"]}
        ]
    },
    "Reabrir Entrada": {
        "arquivo": os.path.join('Queries', 'reabrir_entrada.sql'),
        "parametros": [
            {"var_banco": "codpceentrada", "label": "Código da Entrada:", "tipo": "texto"},
            {"var_banco": "codfuncionario", "label": "Código do Funcionário (Log):", "tipo": "texto"}
        ]
    },
    "Duplicidade CTE": {
        "arquivo": os.path.join('Queries', 'duplicidade_cte.sql'),
        "parametros": [
            {"var_banco": "cod_cte", "label": "Código do CTE:", "tipo": "texto"},
            {"var_banco": "protocolo", "label": "Protocolo:", "tipo": "texto"},
            {"var_banco": "chave", "label": "Chave:", "tipo": "texto"},
            {"var_banco": "xml_cte", "label": "XML:", "tipo": "texto"}
        ]
    }
}

# =======================================================================
# 2. CLASSE DA INTERFACE GRÁFICA
# =======================================================================
ctk.set_appearance_mode("System")  # Segue o tema do Windows (Dark/Light)
ctk.set_default_color_theme("blue")

class PainelSuporte(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Painel | Suporte CF")
        self.geometry("600x750")
        try:
            self.iconbitmap("cf.ico")
        except:
            pass # Se esquecer de mandar o ícone, o app não trava!

        self.inputs_dinamicos = {} # Vai guardar os campos gerados na tela

        self.carregar_clientes()
        self.criar_interface()

    def carregar_clientes(self):
        # COLOQUE A CHAVE QUE O SCRIPT GEROU AQUI DENTRO (Mantenha o 'b' no começo)
        CHAVE_MESTRA = b"wR7DuiLKpuR8h2EOjDGxIFbYSUcUWG8TGknFCga3Om8="

        try:
            f = Fernet(CHAVE_MESTRA)
            
            # Lê o arquivo criptografado
            with open('clientes.enc', 'rb') as file:
                dados_criptografados = file.read()
                
            # Descriptografa na memória (não gera arquivo, super seguro!)
            dados_descriptografados = f.decrypt(dados_criptografados)
            
            # Carrega o JSON a partir dos dados descriptografados
            self.clientes = json.loads(dados_descriptografados)
            
        except Exception as e:
            messagebox.showerror("Erro Técnico Detalhado", f"O motivo exato do erro foi:\n\n{str(e)}")
            self.clientes = {"Nenhum cliente encontrado": {}}

    def criar_interface(self):
        # --- SEÇÃO: CLIENTE E ROTINA ---
        frame_top = ctk.CTkFrame(self)
        frame_top.pack(pady=10, padx=20, fill="x")

        ctk.CTkLabel(frame_top, text="1. Selecione o Cliente:", font=("Arial", 14, "bold")).pack(pady=(10, 0))
        self.cb_cliente = ctk.CTkComboBox(frame_top, values=list(self.clientes.keys()))
        self.cb_cliente.pack(pady=10, padx=20, fill="x")
        self.cb_cliente.bind("<KeyRelease>", self.filtrar_clientes)

        ctk.CTkLabel(frame_top, text="2. Selecione a Query:", font=("Arial", 14, "bold")).pack(pady=(10, 0))
        self.cb_rotina = ctk.CTkOptionMenu(frame_top, values=list(ROTINAS.keys()), command=self.gerar_campos_dinamicos)
        self.cb_rotina.pack(pady=10, padx=20, fill="x")

        # --- SEÇÃO: CAMPOS DINÂMICOS ---
        self.frame_campos = ctk.CTkFrame(self)
        self.frame_campos.pack(pady=10, padx=20, fill="x")
        
        # --- SEÇÃO: BOTÃO DE EXECUÇÃO ---
        self.btn_executar = ctk.CTkButton(self, text="▶ EXECUTAR QUERY", fg_color="darkred", hover_color="red", height=40, font=("Arial", 14, "bold"), command=self.executar_query)
        self.btn_executar.pack(pady=10, padx=20, fill="x")

        # --- SEÇÃO: LOG DE SAÍDA ---
        ctk.CTkLabel(self, text="Resultado da Execução:").pack(pady=(10, 0))
        self.txt_log = ctk.CTkTextbox(self, height=150)
        self.txt_log.pack(pady=5, padx=20, fill="both", expand=True)

        # Gera os campos para a primeira rotina logo que o app abre
        self.gerar_campos_dinamicos(self.cb_rotina.get())

    def gerar_campos_dinamicos(self, nome_rotina):
        # Limpa os campos antigos da tela
        for widget in self.frame_campos.winfo_children():
            widget.destroy()
        self.inputs_dinamicos.clear()

        # Pega a configuração da rotina selecionada
        config = ROTINAS[nome_rotina]

        ctk.CTkLabel(self.frame_campos, text="3. Preencha os Parâmetros:", font=("Arial", 14, "bold")).pack(pady=10)

        # Cria os campos na tela baseado no dicionário
        for param in config["parametros"]:
            frame_linha = ctk.CTkFrame(self.frame_campos, fg_color="transparent")
            frame_linha.pack(pady=5, padx=20, fill="x")
            
            ctk.CTkLabel(frame_linha, text=param["label"], width=200, anchor="w").pack(side="left")
            
            if param["tipo"] == "texto":
                input_field = ctk.CTkEntry(frame_linha)
            elif param["tipo"] == "opcao":
                input_field = ctk.CTkOptionMenu(frame_linha, values=param["opcoes"])
                
            input_field.pack(side="right", fill="x", expand=True)
            
            # Salva a referência do campo usando o nome da variável do banco
            self.inputs_dinamicos[param["var_banco"]] = input_field

    def filtrar_clientes(self, event):
        # Se o técnico apertar a "Seta para Baixo", abre a lista filtrada para ele escolher!
        if event.keysym == 'Down':
            self.cb_cliente._open_dropdown_menu()
            return

        # Ignora as outras teclas de navegação para não dar conflito
        if event.keysym in ['Up', 'Left', 'Right', 'Return']:
            return

        # Pega o texto
        texto_digitado = self.cb_cliente.get()
        texto_min = texto_digitado.lower()
        
        # Filtra a lista
        if texto_min == "":
            clientes_filtrados = list(self.clientes.keys())
        else:
            clientes_filtrados = [cliente for cliente in self.clientes.keys() if texto_min in cliente.lower()]
        
        if not clientes_filtrados:
            clientes_filtrados = ["Nenhum cliente encontrado..."]
            
        # Atualiza os valores do menu SILENCIOSAMENTE (sem forçar a abertura)
        self.cb_cliente.configure(values=clientes_filtrados)

    def log(self, mensagem):
        self.txt_log.insert("end", mensagem + "\n")
        self.txt_log.see("end") # Rola o texto para o final
        self.update()

    def executar_query(self):
        cliente_nome = self.cb_cliente.get()
        rotina_nome = self.cb_rotina.get()

        if cliente_nome not in self.clientes:
            messagebox.showwarning("Cliente Inválido", "Por favor, selecione um cliente válido da lista.")
            return

        config = ROTINAS[rotina_nome]

        if not messagebox.askyesno("Confirmação", f"Tem certeza que deseja rodar '{rotina_nome}' em '{cliente_nome}'?"):
            return

        # 1. ESTADO: RODANDO (AZUL)
        # Muda cor, texto e desativa o botão para evitar duplo clique
        self.btn_executar.configure(text="⏳ RODANDO QUERY...", text_color="white", text_color_disabled="white", fg_color="#1f538d", hover_color="#14375e", state="disabled")
        self.update() # Força a tela a atualizar a cor do botão AGORA!

        self.txt_log.delete("1.0", "end")
        self.log(f"Iniciando rotina: {rotina_nome}")
        self.log(f"Conectando ao cliente: {cliente_nome}...")

        # Monta o cabeçalho SQL lendo o que o usuário digitou
        cabecalho_sql = ""
        for param in config["parametros"]:
            var_nome = param["var_banco"]
            valor_digitado = self.inputs_dinamicos[var_nome].get()
            
            if not valor_digitado:
                self.log(f"[ERRO] O campo '{param['label']}' não pode ficar vazio.")
                # Se der erro de validação, devolve o botão ao normal
                self.btn_executar.configure(text="▶ EXECUTAR QUERY", fg_color="darkred", hover_color="red", state="normal")
                return
                
            cabecalho_sql += f"set @{var_nome} = '{valor_digitado}';\n"

        # Conecta no banco e executa
        cred = self.clientes[cliente_nome]
        try:
            conn = pymysql.connect(
                host=cred['host'], port=int(cred.get('port', 3306)),
                user=cred['user'], password=cred['password'], database=cred['database'],
                client_flag=CLIENT.MULTI_STATEMENTS
            )
            cursor = conn.cursor()

            with open(config["arquivo"], 'r', encoding='utf-8') as file:
                script_base = file.read()

            script_final = cabecalho_sql + script_base

            self.log("Enviando script para o banco de dados...")
            cursor.execute(script_final)

            mensagem_final = "Comandos executados, mas nenhum retorno foi capturado."
            linhas_afetadas = 0
            
            while True:
                if cursor.description is not None:
                    linha = cursor.fetchone()
                    if linha:
                        mensagem_final = linha[0]
                    cursor.fetchall() 
                else:
                    if cursor.rowcount > 0:
                        linhas_afetadas += cursor.rowcount

                if not cursor.nextset():
                    break

            conn.commit()
            self.log(f"\n>>> SUCESSO! ({linhas_afetadas} linhas alteradas no banco)")
            self.log(f"Resultado: {mensagem_final}")

            # 2. ESTADO: SUCESSO (VERDE)
            self.btn_executar.configure(text="✔ QUERY EXECUTADA!", text_color="white", fg_color="#28a745", hover_color="#218838")

        except Exception as e:
            self.log(f"\n[ERRO FATAL] {e}")
            # Se der erro no banco, o botão fica laranja/vermelho claro para alertar
            self.btn_executar.configure(text="✖ Erro na Execução", text_color="white", fg_color="#d9534f", hover_color="#c9302c")
            
        finally:
            if 'conn' in locals() and conn.open:
                cursor.close()
                conn.close()

            # 3. ESTADO: RESET (Volta ao VERMELHO original após 2.5s)
            def resetar_botao():
                self.btn_executar.configure(text="▶ EXECUTAR QUERY", fg_color="darkred", hover_color="red", state="normal")
            
            # Agenda a função resetar_botao para rodar daqui a 2500 milissegundos
            self.after(2500, resetar_botao)

if __name__ == "__main__":
    app = PainelSuporte()
    app.mainloop()