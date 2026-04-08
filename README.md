# 🛠️ Painel de Suporte TI - Automação de Queries SQL

Este é um aplicativo desktop desenvolvido em Python com interface gráfica moderna (CustomTkinter) focado em otimizar e padronizar as querys da equipe de Suporte Técnico. 

O sistema permite que técnicos executem manutenções no banco de dados (MySQL) de múltiplos clientes diretamente por uma interface simples, sem a necessidade de acessar gerenciadores de banco de dados (como HeidiSQL ou DBeaver) ou manipular scripts SQL manualmente.

## ✨ Funcionalidades Principais

* **Arquitetura Extensível (Data-Driven UI):** O sistema possui um design "Plug and Play" orientado a dados. A interface principal e o motor de execução são totalmente desacoplados das regras de negócio. Para adicionar uma nova rotina/query no sistema, basta criar um novo bloco no dicionário de configuração, e a interface gerará os campos de input dinamicamente (Dynamic UI Generation) baseada nos parâmetros exigidos pelo SQL.
* **Busca Inteligente & Autocomplete:** Dropdown com filtro em tempo real organizado em ordem alfabética. O sistema permite a digitação contínua e utiliza atalhos inteligentes (`Enter` ou `Seta para Baixo`) para abrir a lista de resultados filtrados sem travar o teclado.
* **Segurança Criptográfica (AES) Simplificada:** As credenciais não ficam expostas no código. O sistema utiliza a biblioteca `cryptography` (Fernet) combinada com derivação de chave (SHA-256 e Base64). Isso permite trancar e destrancar o arquivo `clientes.enc` usando uma senha mestre fixa, eliminando a necessidade de recompilar o executável a cada novo cliente adicionado.
* **Gestão Completa de Clientes (Importar/Exportar):** A interface permite criar novos clientes manualmente ou geri-los em massa. É possível **Exportar** a lista atual para JSON (para backups) e **Importar** um ficheiro JSON. A importação encripta e substitui os dados automaticamente na hora, dispensando o uso de scripts externos.
* **UX/UI:** Interface em Dark Mode nativo, inicialização perfeitamente centralizada em relação a janela principal e caixas de diálogo modais personalizadas (`CTkMessagebox`) que acompanham a janela principal.
* **Validação de Inputs:** Sistema de prevenção de erros que bloqueia a execução de queries caso campos obrigatórios estejam vazios, fornecendo feedback visual imediato.
* **Suporte a Conexões Legadas:** Configurado para suportar versões antigas do MySQL (`pymysql` configurado para compatibilidade com senhas pré-4.1) operando inclusive sobre túneis de VPN (ex: Radmin).

## 🚀 Tecnologias Utilizadas

* **Python 3**
* **CustomTkinter & CTkMessagebox:** Para a interface gráfica (GUI) e modais de aviso.
* **PyMySQL:** Para comunicação com o banco de dados e execução de *Multi-Statements*.
* **Cryptography & Hashlib:** Para encriptação simétrica e derivação segura de chaves.
* **JSON:** Para armazenamento temporário e processos de importação/exportação.
* **PyInstaller:** Para compilação do projeto em um executável `.exe` standalone.

## 📦 Como Instalar e Rodar Localmente

1. **Clone o repositório:**
```bash
git clone https://github.com/nicolasrapp05/painel-suporte-TI
cd painel-suporte-TI
```

2. **Instale as dependências:**
```bash
pip install customtkinter CTkMessagebox pymysql cryptography
```

3. **Configure os dados (Mock):**
* Renomeie o arquivo `clientes_exemplo.json` para `clientes.json`.
* Insira credenciais válidas de um banco de dados de teste.

4. **Gere o arquivo de segurança:**
* Abra os arquivos `criptografar.py` e `PainelSuporte.py` e defina a sua senha mestre na variável `minha_senha`.
* Rode o script de criptografia:
```bash
python criptografar.py
```
* O script gerará um arquivo `clientes.enc` trancado com a sua senha.
* Ou, clique em `📤 Importar Clientes (JSON)` para carregar uma lista JSON pronta. O sistema irá gerar o ficheiro clientes.enc encriptado automaticamente!

1. **Inicie o aplicativo:**
```bash
python PainelSuporte.py
```

## 🧩 Como adicionar novas Queries (Escalabilidade)

O sistema foi desenhado para ser facilmente escalável. Para adicionar uma nova ferramenta para a equipe, basta adicionar um arquivo `.sql` na pasta `Queries` e registrá-lo no dicionário `ROTINAS` dentro do `PainelSuporte.py`.

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
pyinstaller --onefile --noconsole --icon=icon.ico PainelSuporte.py
```
O arquivo final ficará na pasta `dist/`. Basta distribuir o executável junto com a pasta `Queries` e o arquivo `clientes.enc`.

---
*Aviso de Segurança: Nunca comite o arquivo `clientes.json` original ou o `clientes.enc` de produção no repositório. Mantenha o arquivo `.gitignore` sempre atualizado.*
