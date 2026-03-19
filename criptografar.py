from cryptography.fernet import Fernet

# 1. Gera uma Chave Mestra única
chave = Fernet.generate_key()
print("GUARDE ESTA CHAVE! Você vai precisar colar ela no suporte.py:")
print(f"Chave: {chave.decode()}\n")

f = Fernet(chave)

# 2. Lê o seu clientes.json atual com as senhas expostas
try:
    with open('clientes.json', 'rb') as file:
        dados_originais = file.read()

    # 3. Criptografa tudo
    dados_criptografados = f.encrypt(dados_originais)

    # 4. Salva no novo arquivo criptografado ( .enc )
    with open('clientes.enc', 'wb') as file:
        file.write(dados_criptografados)
        
    print("Sucesso! O arquivo criptografado 'clientes.enc' foi criado.")
except FileNotFoundError:
    print("Erro: O arquivo clientes.json não foi encontrado.")