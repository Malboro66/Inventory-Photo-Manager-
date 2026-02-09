# 🧪 Suite de Testes v8.2 - Visualizador de Peças

## 📋 Visão Geral

Suite completa de testes automatizados para validar robustez, performance e correção do sistema.

### **Estatísticas**

| Métrica | Valor |
|---------|-------|
| **Total de testes** | 32 testes |
| **Cobertura esperada** | 85%+ |
| **Tempo de execução** | ~2 minutos |
| **Categorias** | 4 (unit, integration, slow, stress) |

## 🗂️ Estrutura da Suite

```
.
├── conftest.py                # Fixtures do pytest
├── pytest.ini                 # Configuração pytest
├── test_normalization.py      # 12 testes - Normalização Unicode
├── test_edge_cases.py         # 12 testes - Casos limites
├── test_performance.py        # 8 testes - Performance
└── README_TESTS.md           # Esta documentação
```

## 📦 Dependências

```bash
pip install pytest pytest-cov pytest-timeout Pillow
```

## 🚀 Executando os Testes

### **Todos os testes**

```bash
pytest
```

### **Apenas testes rápidos (< 1s)**

```bash
pytest -m "not slow and not stress"
```

### **Com cobertura de código**

```bash
pytest --cov=. --cov-report=html --cov-report=term
```

Relatório HTML gerado em: `htmlcov/index.html`

### **Testes específicos**

```bash
# Apenas normalização
pytest test_normalization.py

# Apenas performance
pytest test_performance.py -v

# Um teste específico
pytest test_normalization.py::TestNormalization::test_basic_normalization
```

### **Com verbosidade**

```bash
pytest -v          # Verbose
pytest -vv         # Very verbose
pytest -s          # Mostra prints
```

## 📊 Categorias de Testes

### **1️⃣ Testes Unitários (`@pytest.mark.unit`)**

Testes rápidos (<100ms) que validam unidades isoladas:

- ✅ Normalização Unicode (12 casos)
- ✅ Cache hit/miss
- ✅ Validação de entrada
- ✅ Edge cases básicos

**Executar:**
```bash
pytest -m unit
```

### **2️⃣ Testes de Integração (`@pytest.mark.integration`)**

Testes que validam integração entre componentes:

- ✅ Busca completa (cache + normalização)
- ✅ Carregamento paralelo
- ✅ Thread management

**Executar:**
```bash
pytest -m integration
```

### **3️⃣ Testes Lentos (`@pytest.mark.slow`)**

Testes que demoram >1s:

- ✅ 1000+ imagens
- ✅ 10.000 entradas no cache
- ✅ Memory profiling

**Executar apenas rápidos:**
```bash
pytest -m "not slow"
```

### **4️⃣ Testes de Stress (`@pytest.mark.stress`)**

Testes de carga e limites extremos:

- ✅ Concorrência (20+ threads)
- ✅ Cache thrashing
- ✅ Memory stability

**Executar:**
```bash
pytest -m stress
```

## 🎯 Casos de Teste Importantes

### **Normalização Unicode**

| Teste | Entrada | Saída Esperada |
|-------|---------|----------------|
| Acentos | `"Café"` | `"cafe"` |
| Especiais | `"ABC@123"` | `"abc 123"` |
| Símbolos | `"100Ω"` | `"100 ohm"` |
| Gregas | `"α test"` | `"alpha test"` |

### **Casos Limites**

| Teste | Descrição | Critério |
|-------|-----------|----------|
| Empty cache | Cache vazio | Retorna None |
| 10.000 entries | Cache grande | Busca <5ms |
| TTL expiration | Expiração | Remove após TTL |
| Concurrent access | 20 threads | Thread-safe |

### **Performance**

| Teste | Critério | Target |
|-------|----------|--------|
| Normalização | 1000x | <1ms |
| Cache search | O(1) | <1ms |
| Memory leak | 100 ops | Estável |
| Concurrent | 10 threads | Speedup >1.5x |

## 📈 Interpretando Resultados

### **Saída de Sucesso**

```
======================== test session starts =========================
collected 32 items

test_normalization.py ............                            [ 37%]
test_edge_cases.py ............                               [ 75%]
test_performance.py ........                                  [100%]

========================= 32 passed in 120.45s ===================
```

### **Saída com Falhas**

```
FAILED test_normalization.py::test_basic - AssertionError
FAILED test_performance.py::test_speed - duration > 1.0s
```

### **Coverage Report**

```
Name                    Stmts   Miss  Cover
-------------------------------------------
cache.py                  150     10    93%
normalization.py           80      5    94%
-------------------------------------------
TOTAL                     500     25    95%
```

## 🐛 Troubleshooting

### **ImportError: No module named 'visualizador_pecas_v8_1_COMPLETO'**

**Solução:**
```bash
# Renomeie o arquivo principal para corresponder ao import
mv visualizador_pecas_v8.1_COMPLETO.py visualizador_pecas_v8_1_COMPLETO.py
```

Ou ajuste o import em `conftest.py`:
```python
from visualizador_pecas_v8_1_COMPLETO import DirectoryCache
```

### **Testes lentos demais**

**Solução:**
```bash
# Pule testes lentos durante desenvolvimento
pytest -m "not slow and not stress"

# Ou execute em paralelo (requer pytest-xdist)
pip install pytest-xdist
pytest -n auto
```

### **Fixture não encontrada**

**Solução:**
- Verifique que `conftest.py` está no mesmo diretório
- Execute pytest do diretório correto
- Use `pytest --fixtures` para listar fixtures disponíveis

### **Memory test falha**

**Solução:**
- Pode ser falso positivo em sistemas com pouca RAM
- Ajuste threshold no teste
- Execute isoladamente: `pytest test_performance.py::TestPerformance::test_memory_stability`

## ✅ Checklist de Validação

Antes de considerar o código pronto para produção:

- [ ] Todos os 32 testes passam
- [ ] Coverage >= 85%
- [ ] Nenhum teste de performance falha
- [ ] Sem memory leaks detectados
- [ ] Testes de concorrência passam
- [ ] CI/CD integrado (se aplicável)

## 📝 Adicionando Novos Testes

### **Template de Teste Unitário**

```python
import pytest

class TestNovaFuncionalidade:
    """Testes para nova funcionalidade."""

    @pytest.mark.unit
    def test_caso_basico(self):
        """Testa caso básico."""
        result = funcao_nova("input")
        assert result == "expected"

    @pytest.mark.unit
    def test_caso_erro(self):
        """Testa tratamento de erro."""
        with pytest.raises(ValueError):
            funcao_nova(None)
```

### **Template de Teste de Performance**

```python
import pytest
import time

class TestPerformanceNovo:
    """Testes de performance."""

    @pytest.mark.slow
    def test_performance_operacao(self):
        """Valida performance de operação."""
        start = time.time()

        for _ in range(1000):
            funcao_operacao()

        duration = time.time() - start
        assert duration < 1.0, f"Muito lento: {duration:.2f}s"
```

## 🔗 Integração CI/CD

### **GitHub Actions (exemplo)**

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.12'

    - name: Install dependencies
      run: |
        pip install pytest pytest-cov Pillow

    - name: Run tests
      run: |
        pytest --cov=. --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

## 📚 Referências

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Coverage](https://pytest-cov.readthedocs.io/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)

## 🎉 Conclusão

A suite de testes v8.2 garante **85%+ de cobertura** e valida:

✅ **Correção** - 12 testes de normalização Unicode  
✅ **Robustez** - 12 testes de casos limites  
✅ **Performance** - 8 testes de velocidade e memória  
✅ **Concorrência** - Thread-safety validado  

**Execute `pytest` regularmente durante o desenvolvimento!**
