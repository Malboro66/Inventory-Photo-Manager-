"""
Testes de casos limites e edge cases.
"""

import pytest
from pathlib import Path
import threading
import time


class TestEdgeCases:
    """Testes para casos extremos e limites."""

    @pytest.mark.unit
    def test_cache_empty_directory_list(self, cache_instance):
        """Testa cache com lista vazia de diretórios."""
        cache_instance.set("/test", [])
        result = cache_instance.search("/test", "anything")
        assert result is None

    @pytest.mark.unit
    def test_cache_single_entry(self, cache_instance):
        """Testa cache com uma única entrada."""
        cache_instance.set("/test", [("DIR001", Path("/test/DIR001"))])
        result = cache_instance.search("/test", "DIR001")
        assert result is not None
        assert result[0] == "DIR001"

    @pytest.mark.slow
    def test_cache_10000_entries(self, cache_instance):
        """Testa cache com 10.000 entradas."""
        directories = [(f"DIR{i:05d}", Path(f"/path/{i}")) 
                      for i in range(10_000)]
        cache_instance.set("/test", directories)

        # Busca deve ser O(1)
        start = time.time()
        result = cache_instance.search("/test", "DIR05000")
        duration = time.time() - start

        assert result is not None
        assert result[0] == "DIR05000"
        assert duration < 0.005  # < 5ms (tolerância maior)

    @pytest.mark.unit
    def test_cache_ttl_expiration(self, cache_instance):
        """Testa expiração do TTL do cache."""
        cache = cache_instance.__class__(ttl_seconds=1)
        cache.set("/test", [("DIR001", Path("/test/DIR001"))])

        # Imediatamente deve funcionar
        assert cache.get("/test") is not None

        # Após TTL deve expirar
        time.sleep(1.1)
        assert cache.get("/test") is None

    @pytest.mark.unit
    def test_search_not_in_cache(self, cache_instance):
        """Testa busca em diretório não cacheado."""
        result = cache_instance.search("/nonexistent", "term")
        assert result is None

    @pytest.mark.unit
    def test_search_partial_match(self, cache_instance):
        """Testa busca parcial."""
        cache_instance.set("/test", [
            ("MOTOR-ABC-123", Path("/test/MOTOR-ABC-123")),
            ("BOMBA-XYZ-456", Path("/test/BOMBA-XYZ-456"))
        ])

        # Busca parcial deve funcionar
        result = cache_instance.search("/test", "ABC")
        assert result is not None
        assert "ABC" in result[0]

    @pytest.mark.unit
    def test_normalize_none_input(self, cache_instance):
        """Testa normalização com None."""
        result = cache_instance._normalize_text(None)
        assert result == ""

    @pytest.mark.unit
    def test_normalize_only_special_chars(self, cache_instance):
        """Testa normalização com apenas caracteres especiais."""
        result = cache_instance._normalize_text("@#$%^&*()")
        assert result == ""

    @pytest.mark.unit
    def test_cache_invalidate_specific(self, cache_instance):
        """Testa invalidação específica de cache."""
        cache_instance.set("/test1", [("DIR1", Path("/test1/DIR1"))])
        cache_instance.set("/test2", [("DIR2", Path("/test2/DIR2"))])

        cache_instance.invalidate("/test1")

        assert cache_instance.get("/test1") is None
        assert cache_instance.get("/test2") is not None

    @pytest.mark.unit
    def test_cache_invalidate_all(self, cache_instance):
        """Testa invalidação completa de cache."""
        cache_instance.set("/test1", [("DIR1", Path("/test1/DIR1"))])
        cache_instance.set("/test2", [("DIR2", Path("/test2/DIR2"))])

        cache_instance.invalidate()

        assert cache_instance.get("/test1") is None
        assert cache_instance.get("/test2") is None

    @pytest.mark.stress
    def test_concurrent_cache_access(self, cache_instance):
        """Testa acesso concorrente ao cache (thread safety)."""
        directories = [(f"DIR{i:03d}", Path(f"/test/DIR{i:03d}")) 
                      for i in range(100)]
        cache_instance.set("/test", directories)

        results = []
        errors = []

        def worker(term):
            try:
                for _ in range(10):  # 10 buscas por thread
                    result = cache_instance.search("/test", term)
                    results.append(result)
            except Exception as e:
                errors.append(e)

        # 20 threads simultâneas
        threads = [threading.Thread(target=worker, args=(f"DIR{i:03d}",))
                  for i in range(20)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 200  # 20 threads * 10 buscas

    @pytest.mark.unit
    def test_path_with_special_chars(self, cache_instance):
        """Testa path com caracteres especiais."""
        special_path = "/test/Peça-@#$%"
        cache_instance.set(special_path, [("DIR", Path(f"{special_path}/DIR"))])
        result = cache_instance.get(special_path)
        assert result is not None
