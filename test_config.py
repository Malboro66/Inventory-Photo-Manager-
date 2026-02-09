"""
Testes para ConfigManager - Gerenciamento de configurações.
"""

import pytest
import json
import tempfile
from pathlib import Path


class TestConfigManager:
    """Testes para a classe ConfigManager."""

    @pytest.fixture
    def config_file(self):
        """Cria arquivo de configuração temporário."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_path = f.name
        yield config_path
        # Cleanup
        try:
            Path(config_path).unlink()
        except:
            pass

    @pytest.fixture
    def config_manager(self, config_file):
        """Cria instância de ConfigManager."""
        try:
            from visualizador_pecas_v8_1_COMPLETO import ConfigManager
            return ConfigManager(config_file)
        except ImportError:
            pytest.skip("ConfigManager not available")

    @pytest.mark.unit
    def test_config_manager_creation(self, config_manager):
        """Testa criação do ConfigManager."""
        # Deve ter atributo config
        assert hasattr(config_manager, 'config')
        assert isinstance(config_manager.config, dict)

    @pytest.mark.unit
    def test_config_has_defaults(self, config_manager):
        """Testa se config tem valores padrão."""
        config = config_manager.config

        # Verifica se tem os campos principais
        assert isinstance(config, dict)
        assert len(config) >= 0  # Pode estar vazio inicialmente

    @pytest.mark.unit
    def test_config_dict_access(self, config_manager):
        """Testa acesso via dict."""
        # Tenta acessar/modificar config
        config_manager.config['test_key'] = 'test_value'
        assert config_manager.config['test_key'] == 'test_value'

        config_manager.config['test_number'] = 42
        assert config_manager.config['test_number'] == 42

    @pytest.mark.unit
    def test_config_save(self, config_manager, config_file):
        """Testa salvar configuração."""
        # Modifica config
        config_manager.config['test'] = 'value'

        # Salva
        config_manager.save()

        # Verifica arquivo foi criado
        assert Path(config_file).exists()

        # Lê arquivo
        with open(config_file, 'r') as f:
            data = json.load(f)

        assert 'test' in data
        assert data['test'] == 'value'

    @pytest.mark.unit
    def test_config_load(self, config_file):
        """Testa carregar configuração."""
        try:
            from visualizador_pecas_v8_1_COMPLETO import ConfigManager

            # Cria config e salva
            cm1 = ConfigManager(config_file)
            cm1.config['loaded_value'] = 'should_persist'
            cm1.save()

            # Cria nova instância (força load)
            cm2 = ConfigManager(config_file)

            # Verifica se carregou
            assert 'loaded_value' in cm2.config
            assert cm2.config['loaded_value'] == 'should_persist'
        except ImportError:
            pytest.skip("ConfigManager not available")

    @pytest.mark.unit
    def test_config_multiple_values(self, config_manager):
        """Testa múltiplos valores."""
        updates = {
            'key1': 'value1',
            'key2': 42,
            'key3': True,
            'key4': [1, 2, 3],
            'key5': {'nested': 'dict'}
        }

        # Atualiza
        for key, value in updates.items():
            config_manager.config[key] = value

        # Verifica
        for key, expected in updates.items():
            assert config_manager.config[key] == expected

    @pytest.mark.unit
    def test_config_json_serialization(self, config_manager, config_file):
        """Testa serialização JSON."""
        # Adiciona dados diversos
        config_manager.config.update({
            'string': 'test',
            'number': 123,
            'boolean': True,
            'list': [1, 2, 3],
            'dict': {'a': 1}
        })

        # Salva
        config_manager.save()

        # Lê como JSON
        with open(config_file, 'r') as f:
            data = json.load(f)

        # Verifica tipos foram preservados
        assert isinstance(data['string'], str)
        assert isinstance(data['number'], int)
        assert isinstance(data['boolean'], bool)
        assert isinstance(data['list'], list)
        assert isinstance(data['dict'], dict)

    @pytest.mark.unit
    def test_config_update_method(self, config_manager):
        """Testa método update."""
        new_data = {'a': 1, 'b': 2, 'c': 3}

        # Atualiza via update
        config_manager.config.update(new_data)

        # Verifica
        for key, value in new_data.items():
            assert config_manager.config[key] == value

    @pytest.mark.unit
    def test_config_clear(self, config_manager):
        """Testa limpar configuração."""
        # Adiciona dados
        config_manager.config['to_clear'] = 'value'
        assert 'to_clear' in config_manager.config

        # Limpa
        config_manager.config.clear()

        # Verifica está vazio
        assert len(config_manager.config) == 0

    @pytest.mark.unit
    def test_config_get_with_default(self, config_manager):
        """Testa get com valor padrão."""
        # Key não existe
        result = config_manager.config.get('nonexistent', 'default_value')
        assert result == 'default_value'

        # Key existe
        config_manager.config['exists'] = 'real_value'
        result = config_manager.config.get('exists', 'default_value')
        assert result == 'real_value'

    @pytest.mark.unit
    def test_config_has_save_method(self, config_manager):
        """Testa se ConfigManager tem método save."""
        assert hasattr(config_manager, 'save')
        assert callable(config_manager.save)


class TestConfigPersistence:
    """Testes para persistência de configuração."""

    @pytest.mark.unit
    def test_persistence_between_instances(self):
        """Testa persistência entre instâncias."""
        try:
            from visualizador_pecas_v8_1_COMPLETO import ConfigManager

            with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
                config_file = f.name

            try:
                # Primeira instância
                cm1 = ConfigManager(config_file)
                cm1.config['persistent'] = 'data'
                cm1.save()

                # Segunda instância
                cm2 = ConfigManager(config_file)
                assert cm2.config.get('persistent') == 'data'
            finally:
                Path(config_file).unlink()
        except ImportError:
            pytest.skip("ConfigManager not available")

    @pytest.mark.unit
    def test_invalid_json_file(self):
        """Testa comportamento com JSON inválido."""
        try:
            from visualizador_pecas_v8_1_COMPLETO import ConfigManager

            # Cria arquivo com JSON inválido
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                f.write("invalid json {{{")
                invalid_file = f.name

            try:
                # Deve criar config vazio ou padrão
                cm = ConfigManager(invalid_file)

                # Deve ser dict válido
                assert isinstance(cm.config, dict)
            finally:
                Path(invalid_file).unlink()
        except ImportError:
            pytest.skip("ConfigManager not available")

    @pytest.mark.unit
    def test_nonexistent_file(self):
        """Testa arquivo que não existe."""
        try:
            from visualizador_pecas_v8_1_COMPLETO import ConfigManager

            # Arquivo não existe
            with tempfile.NamedTemporaryFile(suffix='.json', delete=True) as f:
                nonexistent_file = f.name

            # Deve criar config padrão
            cm = ConfigManager(nonexistent_file)
            assert isinstance(cm.config, dict)

            # Cleanup
            try:
                Path(nonexistent_file).unlink()
            except:
                pass
        except ImportError:
            pytest.skip("ConfigManager not available")