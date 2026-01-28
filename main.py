# main.py
from src.coleta import robo_inteligente
from src.processamento import processar_arquivos  # <--- Importação nova!

if __name__ == "__main__":
    print("Iniciando Sistema IntuitiveCare...")
    print("Alessandro Barbosa - Teste Técnico 2026\n")

    # Parte 1.1: Download
    robo_inteligente()

    print("\n" + "=" * 50 + "\n")

    # Parte 1.2: Processamento (O Inspetor)
    processar_arquivos()