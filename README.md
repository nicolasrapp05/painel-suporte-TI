# 🛠️ Painel de Suporte TI - Automação de Queries SQL

Este é um aplicativo desktop desenvolvido em Python com interface gráfica moderna (CustomTkinter) focado em otimizar e padronizar as querys da equipe de Suporte Técnico. 

O sistema permite que técnicos executem manutenções no banco de dados (MySQL) de múltiplos clientes diretamente por uma interface simples, sem a necessidade de acessar gerenciadores de banco de dados (como HeidiSQL ou DBeaver) ou manipular scripts SQL manualmente.

## ✨ Funcionalidades Principais

* **Arquitetura Extensível (Data-Driven UI):** O sistema possui um design "Plug and Play" orientado a dados. A interface principal e o motor de execução são totalmente desacoplados das regras de negócio. Para adicionar uma nova rotina/query no sistema, basta criar um novo bloco no dicionário de configuração, e a interface gerará os campos de input dinamicamente (Dynamic UI Generation) baseada nos parâmetros exigidos pelo SQL, sem necessidade de alterar o código principal.
* **Busca Inteligente de Clientes:** Dropdown com filtro em tempo real (autocomplete) para lidar facilmente com listas extensas de clientes.
* **Segurança Criptográfica (AES):** As credenciais de banco de dados dos clientes não ficam expostas no código. O sistema utiliza a biblioteca `cryptography` (Fernet) para ler um arquivo `.enc` criptografado em tempo de execução.
* **Feedback Visual em Tempo Real:** Botões com controle de estado (Rodando, Sucesso, Erro) e terminal de log integrado na interface.
* **Suporte a Conexões Legadas:** Configurado para suportar versões antigas do MySQL (`pymysql` configurado para compatibilidade com senhas pré-4.1) operando inclusive sobre túneis de VPN (ex: Radmin).

## 🚀 Tecnologias Utilizadas

* **Python 3**
* **CustomTkinter:** Para a interface gráfica (GUI).
* **PyMySQL:** Para comunicação com o banco de dados e execução de *Multi-Statements*.
* **Cryptography:** Para encriptação simétrica das credenciais dos clientes.
* **PyInstaller:** Para compilação do projeto em um executável `.exe` standalone.

## 📦 Como Instalar e Rodar Localmente

1. **Clone o repositório:**
```bash
git clone https://github.com/nicolasrapp05/painel-suporte-TI
cd painel-suporte-TI
```

2. **Instale as dependências:**
```bash
pip install customtkinter pymysql cryptography
```

3. **Configure os dados (Mock):**
* Renomeie o arquivo `clientes_exemplo.json` para `clientes.json`.
* Insira credenciais válidas de um banco de dados de teste.

4. **Gere o arquivo de segurança:**
* Rode o script de criptografia:
```bash
python criptografar.py
```
* O script gerará um arquivo `clientes.enc` e exibirá uma **Chave Mestra** no terminal.
* Copie essa chave, abra o arquivo `suporte.py` e cole-a na variável `CHAVE_MESTRA`.

5. **Inicie o aplicativo:**
```bash
python suporte.py
```

## 🧩 Como adicionar novas Queries (Escalabilidade)

O sistema foi desenhado para ser facilmente escalável. Para adicionar uma nova ferramenta para a equipe, basta adicionar um arquivo `.sql` na pasta `Queries` e registrá-lo no dicionário `ROTINAS` dentro do `suporte.py`.

Exemplo:
```python
"Nome da Sua Rotina": {
    "arquivo": os.path.join('Queries', 'seu_script.sql'),
    "parametros": [
        {"var_banco": "id_cliente", "label": "ID do Cliente:", "tipo": "texto"},
        {"var_banco": "ignorar_aviso", "label": "Ignorar avisos?", "tipo": "opcao", "opcoes": ["False", "True"]}
    ]
}
```
As variáveis (`var_banco`) serão automaticamente injetadas no seu `.sql` como `@id_cliente` e `@ignorar_aviso`.

## ⚙️ Compilando para a Equipe (.exe)
Para distribuir o aplicativo para a equipe sem a necessidade de instalarem o Python, utilize o PyInstaller:

```bash
pyinstaller --onefile --noconsole --icon=icone.ico suporte.py
```
O arquivo final ficará na pasta `dist/`. Basta distribuir o executável junto com a pasta `Queries` e o arquivo `clientes.enc`.

---
*Aviso de Segurança: Nunca comite o arquivo `clientes.json` original ou o `clientes.enc` de produção no repositório. Mantenha o arquivo `.gitignore` sempre atualizado.*