"""
Script helper para copiar o arquivo com nome correto para os testes.
Execute antes de rodar pytest.
"""

import shutil
import os
from pathlib import Path

def setup_tests():
    """Copia arquivo principal com nome correto para testes."""

    # Procura pelo arquivo v8.1
    candidates = [
        "visualizador_pecas_v8.1_COMPLETO.py",
        "visualizador_pecas_v8_1_COMPLETO.py"
    ]

    source = None
    for candidate in candidates:
        if Path(candidate).exists():
            source = candidate
            break

    if not source:
        print("❌ Erro: Arquivo visualizador_pecas_v8.1_COMPLETO.py não encontrado!")
        print()
        print("Por favor, certifique-se que o arquivo está no diretório atual.")
        return False

    # Nome esperado pelos testes (com underscores)
    target = "visualizador_pecas_v8_1_COMPLETO.py"

    if source != target:
        print(f"📋 Copiando {source} → {target}")
        try:
            shutil.copy2(source, target)
            print("✅ Arquivo copiado com sucesso!")
        except Exception as e:
            print(f"❌ Erro ao copiar: {e}")
            return False
    else:
        print("✅ Arquivo já está com nome correto!")

    print()
    print("="*80)
    print("PRONTO PARA EXECUTAR TESTES!")
    print("="*80)
    print()
    print("Execute: pytest -v")
    print()

    return True

if __name__ == "__main__":
    setup_tests()
