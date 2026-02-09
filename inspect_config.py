
import sys
sys.path.insert(0, '.')

from visualizador_pecas_v8_1_COMPLETO import ConfigManager
import tempfile

# Cria instância temporária
with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
    config_file = f.name

cm = ConfigManager(config_file)

print("MÉTODOS PÚBLICOS DO ConfigManager:")
print("="*80)
metodos = [m for m in dir(cm) if not m.startswith('_')]
for metodo in metodos:
    attr = getattr(cm, metodo)
    if callable(attr):
        print(f"  • {metodo}()")
    else:
        print(f"  • {metodo} [propriedade]")

print()
print("ATRIBUTOS DE INSTÂNCIA:")
print("="*80)
for attr in dir(cm):
    if not attr.startswith('_') and not callable(getattr(cm, attr)):
        valor = getattr(cm, attr)
        print(f"  • {attr} = {valor}")

print()
print("TESTANDO MÉTODOS:")
print("="*80)

# Tenta diferentes APIs
try:
    # API 1: get/set simples
    print("Tentando: cm.set('test', 'value')")
    cm.set('test', 'value')
    print("✅ Funcionou!")
    print(f"   cm.get('test') = {cm.get('test')}")
except Exception as e:
    print(f"❌ Erro: {e}")

print()

try:
    # API 2: getattr/setattr
    print("Tentando: setattr(cm, 'test', 'value')")
    setattr(cm, 'test', 'value')
    print("✅ Funcionou!")
    print(f"   getattr(cm, 'test') = {getattr(cm, 'test')}")
except Exception as e:
    print(f"❌ Erro: {e}")

print()

try:
    # API 3: dict-like
    print("Tentando: cm['test'] = 'value'")
    cm['test'] = 'value'
    print("✅ Funcionou!")
    print(f"   cm['test'] = {cm['test']}")
except Exception as e:
    print(f"❌ Erro: {e}")

print()

try:
    # API 4: config dict
    print("Tentando: cm.config")
    config = cm.config
    print(f"✅ Funcionou! Tipo: {type(config)}")
    print(f"   Keys: {list(config.keys())[:5]}")
except Exception as e:
    print(f"❌ Erro: {e}")

# Cleanup
import os
os.unlink(config_file)
