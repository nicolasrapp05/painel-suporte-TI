import json
import os
import pymysql
from pymysql.constants import CLIENT
import warnings
import customtkinter as ctk
from customtkinter import filedialog
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

        # COLOQUE A SENHA QUE ESCOLHEU PARA CRIPTOGRAFAR
        self.minha_senha = "cfinfohard" 
        self.chave_fernet = base64.urlsafe_b64encode(hashlib.sha256(self.minha_senha.encode()).digest())

        self.inputs_dinamicos = {}

        self.carregar_clientes()
        self.criar_interface()

    def carregar_clientes(self):
        try:
            f = Fernet(self.chave_fernet)
            
            with open('clientes.enc', 'rb') as file:
                dados_criptografados = file.read()
                
            dados_descriptografados = f.decrypt(dados_criptografados)
            
            self.clientes = json.loads(dados_descriptografados)
            
        except Exception as e:
            self.update()
            erro_msg = str(e) if str(e) else "Senha incorreta ou arquivo corrompido (InvalidToken)."
            CTkMessagebox(master=self, title="Erro Técnico Detalhado", message=f"O motivo exato do erro foi:\n\n{erro_msg}", icon="cancel")
            self.clientes = {"Nenhum cliente encontrado": {}}

    def criar_interface(self):
        frame_top = ctk.CTkFrame(self)
        frame_top.pack(pady=10, padx=20, fill="x")

        ctk.CTkLabel(frame_top, text="1. Selecione o Cliente:", font=("Arial", 14, "bold")).pack(pady=(10, 0))
        self.cb_cliente = ctk.CTkComboBox(frame_top, values=sorted(self.clientes.keys()))
        self.cb_cliente.pack(pady=10, padx=20, fill="x")
        self.cb_cliente.bind("<KeyRelease>", self.filtrar_clientes)

        self.btn_novo_cliente = ctk.CTkButton(
            frame_top, 
            text="➕ Novo Cliente", 
            fg_color="#1f538d",
            hover_color="#14375e",
            command=self.abrir_janela_novo_cliente
        )
        self.btn_novo_cliente.pack(pady=(0, 10), padx=20, fill="x")

        self.btn_exportar = ctk.CTkButton(
            frame_top, 
            text="📥 Exportar Clientes (JSON)", 
            fg_color="#1f538d",
            hover_color="#14375e",
            command=self.exportar_json_clientes
        )
        self.btn_exportar.pack(pady=(0, 10), padx=20, fill="x")

        ctk.CTkLabel(frame_top, text="2. Selecione a Query:", font=("Arial", 14, "bold")).pack(pady=(10, 0))
        self.cb_rotina = ctk.CTkOptionMenu(frame_top, values=list(ROTINAS.keys()), command=self.gerar_campos_dinamicos)
        self.cb_rotina.pack(pady=10, padx=20, fill="x")

        self.frame_campos = ctk.CTkFrame(self)
        self.frame_campos.pack(pady=10, padx=20, fill="x")
        
        self.btn_executar = ctk.CTkButton(self, text="▶ EXECUTAR QUERY", fg_color="darkred", hover_color="red", height=40, font=("Arial", 14, "bold"), command=self.executar_query)
        self.btn_executar.pack(pady=10, padx=20, fill="x")

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
        if event.keysym in ['Down', 'Return']:
            self.cb_cliente._open_dropdown_menu()
            return

        if event.keysym in ['Up', 'Left', 'Right']:
            return

        texto_digitado = self.cb_cliente.get()
        texto_min = texto_digitado.lower()
        
        if texto_min == "":
            clientes_filtrados = sorted(self.clientes.keys())
        else:
            clientes_filtrados = sorted([cliente for cliente in self.clientes.keys() if texto_min in cliente.lower()])
        
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
            button_width=100
        )

        if msg.get() != "Sim":
            return

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

            self.btn_executar.configure(text="✔ QUERY EXECUTADA!", text_color="white", fg_color="#28a745", hover_color="#218838")

        except Exception as e:
            self.log(f"\n[ERRO FATAL] {e}")
            self.btn_executar.configure(text="✖ Erro na Execução", text_color="white", fg_color="#d9534f", hover_color="#c9302c")
            
        finally:
            if 'conn' in locals() and conn.open:
                cursor.close()
                conn.close()

            def resetar_botao():
                self.btn_executar.configure(text="▶ EXECUTAR QUERY", fg_color="darkred", hover_color="red", state="normal")
            
            self.after(2500, resetar_botao)
    
    def abrir_janela_novo_cliente(self):
        janela = ctk.CTkToplevel(self)
        janela.title("Adicionar Novo Cliente")
        
        try:
            janela.iconbitmap("icon.ico")
        except:
            pass

        largura_janela = 400
        altura_janela = 600

        self.update_idletasks()

        x_painel = self.winfo_x()
        y_painel = self.winfo_y()
        largura_painel = self.winfo_width()
        altura_painel = self.winfo_height()

        pos_x = x_painel + int((largura_painel / 2) - (largura_janela / 2))
        pos_y = y_painel + int((altura_painel / 2) - (altura_janela / 2))

        janela.geometry(f"{largura_janela}x{altura_janela}+{pos_x}+{pos_y}")
        
        janela.transient(self)
        janela.grab_set()

        campos = {}

        config_campos = [
            ("Nome do Cliente (ex: 200.14 - Papel e CIA)", "nome"),
            ("Host (IP ou endereço)", "host"),
            ("Porta (ex: 3306)", "port"),
            ("Usuário", "user"),
            ("Senha", "password"),
            ("Nome do Banco de Dados", "database")
        ]

        ctk.CTkLabel(janela, text="Dados de Conexão MySQL:", font=("Arial", 16, "bold")).pack(pady=20)

        for label_texto, chave in config_campos:
            ctk.CTkLabel(janela, text=label_texto, anchor="w").pack(padx=20, fill="x")
            
            show_char = "*" if chave == "password" else ""
            entry = ctk.CTkEntry(janela, show=show_char)
            entry.pack(padx=20, pady=(0, 10), fill="x")
            
            campos[chave] = entry

        def salvar_cliente():
            for chave, entry in campos.items():
                if not entry.get().strip():
                    CTkMessagebox(master=janela, title="Aviso", message="Preencha todos os campos!", icon="warning")
                    return

            nome_cliente = campos["nome"].get().strip()

            if nome_cliente in self.clientes:
                CTkMessagebox(master=janela, title="Aviso", message="Já existe um cliente com este nome!", icon="warning")
                return

            dados_conexao = {
                "host": campos["host"].get().strip(),
                "port": campos["port"].get().strip(),
                "user": campos["user"].get().strip(),
                "password": campos["password"].get().strip(),
                "database": campos["database"].get().strip()
            }

            try:
                self.clientes[nome_cliente] = dados_conexao

                dados_json = json.dumps(self.clientes, indent=4).encode('utf-8')

                f = Fernet(self.chave_fernet)

                dados_criptografados = f.encrypt(dados_json)

                with open('clientes.enc', 'wb') as file:
                    file.write(dados_criptografados)

                self.cb_cliente.configure(values=sorted(self.clientes.keys()))
                self.cb_cliente.set(nome_cliente)

                janela.destroy()
                CTkMessagebox(master=self, title="Sucesso", message=f"Cliente '{nome_cliente}' salvo com segurança!", icon="check")

            except Exception as e:
                CTkMessagebox(master=janela, title="Erro ao Salvar", message=f"Erro técnico:\n\n{str(e)}", icon="cancel")

        btn_salvar = ctk.CTkButton(janela, text="✔ Salvar Cliente", fg_color="#28a745", hover_color="#218838", font=("Arial", 14, "bold"), command=salvar_cliente)
        btn_salvar.pack(pady=20, padx=20, fill="x")

    def exportar_json_clientes(self):
        if not self.clientes or "Nenhum cliente encontrado" in self.clientes:
            CTkMessagebox(master=self, title="Aviso", message="Não há clientes válidos para exportar.", icon="warning")
            return

        caminho_arquivo = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("Arquivo JSON", "*.json")],
            title="Salvar lista de clientes como...",
            initialfile="clientes_exportados.json"
        )

        if not caminho_arquivo:
            return

        try:
            with open(caminho_arquivo, 'w', encoding='utf-8') as file:
                json.dump(self.clientes, file, indent=4, ensure_ascii=False)
            
            CTkMessagebox(master=self, title="Sucesso", message=f"Arquivo JSON salvo com sucesso em:\n{caminho_arquivo}", icon="check")
            
        except Exception as e:
            CTkMessagebox(master=self, title="Erro ao Exportar", message=f"Falha ao salvar o arquivo:\n\n{str(e)}", icon="cancel")

if __name__ == "__main__":
    app = PainelSuporte()
    app.mainloop()