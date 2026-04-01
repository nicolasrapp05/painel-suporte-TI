import json
import os
import pymysql
from pymysql.constants import CLIENT
import warnings
import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
import base64
import hashlib
from cryptography.fernet import Fernet

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
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class PainelSuporte(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Painel | Suporte")

        largura_janela = 600
        altura_janela = 750
        largura_tela = self.winfo_screenwidth()
        altura_tela = self.winfo_screenheight()
        pos_x = int((largura_tela / 2) - (largura_janela / 2))
        pos_y = int((altura_tela / 2) - (altura_janela / 2))
        self.geometry(f"{largura_janela}x{altura_janela}+{pos_x}+{pos_y}")

        try:
            self.iconbitmap("icon.ico")
        except:
            pass

        self.inputs_dinamicos = {}

        self.carregar_clientes()
        self.criar_interface()

    def carregar_clientes(self):
        # COLOQUE A SENHA QUE ESCOLHEU PARA CRIPTOGRAFAR
        SENHA = "cole_aqui"
        CHAVE_MESTRA = base64.urlsafe_b64encode(hashlib.sha256(SENHA.encode()).digest())

        try:
            f = Fernet(CHAVE_MESTRA)
            
            with open('clientes.enc', 'rb') as file:
                dados_criptografados = file.read()
                
            dados_descriptografados = f.decrypt(dados_criptografados)
            
            self.clientes = json.loads(dados_descriptografados)
            
        except Exception as e:
            CTkMessagebox(title="Erro Técnico Detalhado", master=self, message=f"O motivo exato do erro foi:\n\n{str(e)}", icon="cancel")
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

        self.gerar_campos_dinamicos(self.cb_rotina.get())

    def gerar_campos_dinamicos(self, nome_rotina):
        for widget in self.frame_campos.winfo_children():
            widget.destroy()
        self.inputs_dinamicos.clear()

        config = ROTINAS[nome_rotina]

        ctk.CTkLabel(self.frame_campos, text="3. Preencha os Parâmetros:", font=("Arial", 14, "bold")).pack(pady=10)

        for param in config["parametros"]:
            frame_linha = ctk.CTkFrame(self.frame_campos, fg_color="transparent")
            frame_linha.pack(pady=5, padx=20, fill="x")
            
            ctk.CTkLabel(frame_linha, text=param["label"], width=200, anchor="w").pack(side="left")
            
            if param["tipo"] == "texto":
                input_field = ctk.CTkEntry(frame_linha)
            elif param["tipo"] == "opcao":
                input_field = ctk.CTkOptionMenu(frame_linha, values=param["opcoes"])
                
            input_field.pack(side="right", fill="x", expand=True)
            
            self.inputs_dinamicos[param["var_banco"]] = input_field

    def filtrar_clientes(self, event):
        if event.keysym == 'Down':
            self.cb_cliente._open_dropdown_menu()
            return

        if event.keysym in ['Up', 'Left', 'Right', 'Return']:
            return

        texto_digitado = self.cb_cliente.get()
        texto_min = texto_digitado.lower()
        
        if texto_min == "":
            clientes_filtrados = list(self.clientes.keys())
        else:
            clientes_filtrados = [cliente for cliente in self.clientes.keys() if texto_min in cliente.lower()]
        
        if not clientes_filtrados:
            clientes_filtrados = ["Nenhum cliente encontrado..."]
            
        self.cb_cliente.configure(values=clientes_filtrados)

    def log(self, mensagem):
        self.txt_log.insert("end", mensagem + "\n")
        self.txt_log.see("end")
        self.update()

    def executar_query(self):
        cliente_nome = self.cb_cliente.get()
        rotina_nome = self.cb_rotina.get()

        if cliente_nome not in self.clientes:
            CTkMessagebox(title="Cliente Inválido", master=self, message="Por favor, selecione um cliente válido da lista.", icon="warning")
            return

        config = ROTINAS[rotina_nome]

        mensagem_formatada = (
            f"Você está prestes a executar a rotina:\n"
            f"'{rotina_nome}'\n\n"
            f"No banco de dados do cliente:\n"
            f"'{cliente_nome}'\n\n"
            f"Deseja continuar?"
        )

        msg = CTkMessagebox(
            master=self,
            title="Confirmação de Execução", 
            message=mensagem_formatada,
            icon="warning", 
            option_1="Não", 
            option_2="Sim",
            button_width=100  # Trava a largura dos botões para não esticarem
        )

        if msg.get() != "Sim":
            return

        # 1. ESTADO: RODANDO (AZUL)
        self.btn_executar.configure(text="⏳ RODANDO QUERY...", text_color="white", text_color_disabled="white", fg_color="#1f538d", hover_color="#14375e", state="disabled")
        self.update()

        self.txt_log.delete("1.0", "end")
        self.log(f"Iniciando rotina: {rotina_nome}")
        self.log(f"Conectando ao cliente: {cliente_nome}...")

        cabecalho_sql = ""
        for param in config["parametros"]:
            var_nome = param["var_banco"]
            valor_digitado = self.inputs_dinamicos[var_nome].get()
            
            if not valor_digitado:
                CTkMessagebox(
                    title="Campo Obrigatório",
                    master=self,
                    message=f"O campo '{param['label']}' é obrigatório.\nPor favor, preencha-o antes de continuar.",
                    icon="warning"
                )
                self.log(f"[ERRO] O campo '{param['label']}' não pode ficar vazio.")
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
            self.btn_executar.configure(text="✖ Erro na Execução", text_color="white", fg_color="#d9534f", hover_color="#c9302c")
            
        finally:
            if 'conn' in locals() and conn.open:
                cursor.close()
                conn.close()

            # 3. ESTADO: RESET
            def resetar_botao():
                self.btn_executar.configure(text="▶ EXECUTAR QUERY", fg_color="darkred", hover_color="red", state="normal")
            
            self.after(2500, resetar_botao)

if __name__ == "__main__":
    app = PainelSuporte()
    app.mainloop()