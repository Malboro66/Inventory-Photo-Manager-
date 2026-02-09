"""
Fixtures e configurações do pytest para suite de testes v8.2.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from PIL import Image
import sys
import os

# Adiciona diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


@pytest.fixture
def temp_dir():
    """Cria diretório temporário para testes."""
    temp = tempfile.mkdtemp()
    yield Path(temp)
    shutil.rmtree(temp, ignore_errors=True)


@pytest.fixture
def sample_image(temp_dir):
    """Cria imagem de teste válida (100x100 RGB)."""
    img_path = temp_dir / "test_image.jpg"
    img = Image.new('RGB', (100, 100), color=(73, 109, 137))
    img.save(img_path, 'JPEG')
    return img_path


@pytest.fixture
def corrupted_image(temp_dir):
    """Cria arquivo de imagem corrompido."""
    img_path = temp_dir / "corrupted.jpg"
    with open(img_path, 'wb') as f:
        f.write(b'\xFF\xD8\xFF\xE0' + b'corrupted data' * 100)
    return img_path


@pytest.fixture
def large_image(temp_dir):
    """Cria imagem grande (2000x2000 = ~12MB descomprimido)."""
    img_path = temp_dir / "large.jpg"
    img = Image.new('RGB', (2000, 2000), color=(255, 0, 0))
    img.save(img_path, 'JPEG', quality=95)
    return img_path


@pytest.fixture
def image_collection(temp_dir):
    """Cria coleção de 50 imagens para testes."""
    img_dir = temp_dir / "images"
    img_dir.mkdir()

    images = []
    for i in range(50):
        img_path = img_dir / f"img{i:03d}.jpg"
        img = Image.new('RGB', (100, 100), color=(i*5 % 256, 0, 0))
        img.save(img_path, 'JPEG')
        images.append(img_path)

    return images


@pytest.fixture
def directory_structure(temp_dir):
    """Cria estrutura de diretórios complexa para testes."""
    root = temp_dir / "root"
    root.mkdir()

    # Cria pastas com diferentes características
    (root / "PECA001").mkdir()
    (root / "PECA002").mkdir()
    (root / "Peça-Especial@123").mkdir()
    (root / "Empty").mkdir()

    # Adiciona imagens em algumas pastas
    for i in range(5):
        img = Image.new('RGB', (100, 100))
        img.save(root / "PECA001" / f"img{i}.jpg")

    for i in range(3):
        img = Image.new('RGB', (100, 100))
        img.save(root / "PECA002" / f"img{i}.jpg")

    return root


@pytest.fixture
def cache_instance():
    """Cria instância limpa de DirectoryCache."""
    # Tenta importar de diferentes nomes possíveis
    try:
        # Tenta com underscores (nome Python válido)
        from visualizador_pecas_v8_1_COMPLETO import DirectoryCache
        return DirectoryCache(ttl_seconds=300)
    except ImportError:
        try:
            # Tenta com pontos (nome original)
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "visualizador", 
                "visualizador_pecas_v8.1_COMPLETO.py"
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return module.DirectoryCache(ttl_seconds=300)
        except:
            pass
        pytest.skip("DirectoryCache not available")


@pytest.fixture
def config_manager():
    """Cria instância de ConfigManager para testes."""
    try:
        from visualizador_pecas_v8_1_COMPLETO import ConfigManager
        import tempfile
        config_file = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
        config_file.close()
        cm = ConfigManager(config_file.name)
        yield cm
        os.unlink(config_file.name)
    except ImportError:
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "visualizador", 
                "visualizador_pecas_v8.1_COMPLETO.py"
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                config_file = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
                config_file.close()
                cm = module.ConfigManager(config_file.name)
                yield cm
                os.unlink(config_file.name)
                return
        except:
            pass
        pytest.skip("ConfigManager not available")


# Markers personalizados
def pytest_configure(config):
    config.addinivalue_line("markers", "slow: marca testes lentos (>1s)")
    config.addinivalue_line("markers", "stress: marca testes de carga")
    config.addinivalue_line("markers", "integration: marca testes de integração")
    config.addinivalue_line("markers", "unit: marca testes unitários")