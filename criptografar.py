import base64
import hashlib
from cryptography.fernet import Fernet

senha = input("Escolha uma senha: ")

chave_fernet = base64.urlsafe_b64encode(hashlib.sha256(senha.encode()).digest())

f = Fernet(chave_fernet)

try:
    with open('clientes.json', 'rb') as file:
        dados_originais = file.read()

    dados_criptografados = f.encrypt(dados_originais)

    with open('clientes.enc', 'wb') as file:
        file.write(dados_criptografados)
        
    print(f"Sucesso! Arquivo criptografado usando a senha: {senha}\nVocê precisará colar ela no PainelSuporte.py")
except FileNotFoundError:
    print("Erro: O arquivo clientes.json não foi encontrado.")