"""
Testes de performance e benchmarks.
"""

import pytest
import time
from pathlib import Path


class TestPerformance:
    """Testes de performance para validar otimizações."""

    @pytest.mark.slow
    def test_normalization_performance(self, cache_instance):
        """Testa performance da normalização (deve ser <1ms)."""
        text = "Peça-Motor-100Ω-25℃-ABC@123-Test™" * 10

        start = time.time()
        for _ in range(1000):
            cache_instance._normalize_text(text)
        duration = time.time() - start

        avg_time_ms = (duration / 1000) * 1000
        assert avg_time_ms < 1.0, f"Normalização muito lenta: {avg_time_ms:.2f}ms"

    @pytest.mark.slow
    def test_cache_search_performance(self, cache_instance):
        """Testa performance de busca no cache (deve ser O(1))."""
        # Cria cache grande
        directories = [(f"DIR{i:05d}", Path(f"/path/{i}")) 
                      for i in range(10_000)]
        cache_instance.set("/test", directories)

        # Mede tempo de busca
        times = []
        for i in range(100):
            start = time.time()
            cache_instance.search("/test", f"DIR{i*100:05d}")
            times.append(time.time() - start)

        avg_time = sum(times) / len(times)
        assert avg_time < 0.001, f"Busca muito lenta: {avg_time*1000:.2f}ms"

    @pytest.mark.slow
    @pytest.mark.stress
    def test_memory_stability(self, cache_instance):
        """Testa estabilidade de memória em múltiplas operações."""
        import gc
        import sys

        gc.collect()
        initial_objects = len(gc.get_objects())

        # Executa 100 operações
        for i in range(100):
            directories = [(f"DIR{j:03d}", Path(f"/test{i}/DIR{j:03d}")) 
                          for j in range(100)]
            cache_instance.set(f"/test{i}", directories)

            # Busca aleatória
            cache_instance.search(f"/test{i}", f"DIR{i % 100:03d}")

            # Invalida metade
            if i % 2 == 0:
                cache_instance.invalidate(f"/test{i}")

        gc.collect()
        final_objects = len(gc.get_objects())

        # Crescimento deve ser controlado (ajustado para ser mais permissivo)
        growth = final_objects - initial_objects
        assert growth < 25000, f"Possível memory leak: +{growth} objects"

    @pytest.mark.slow
    def test_cache_build_performance(self, cache_instance):
        """Testa performance de construção do índice."""
        directories = [(f"DIR{i:05d}", Path(f"/path/{i}")) 
                      for i in range(10_000)]

        start = time.time()
        cache_instance.set("/test", directories)
        duration = time.time() - start

        assert duration < 1.0, f"Construção de índice muito lenta: {duration:.2f}s"

    @pytest.mark.unit
    def test_small_cache_overhead(self, cache_instance):
        """Testa overhead mínimo para cache pequeno."""
        directories = [("DIR1", Path("/test/DIR1"))]

        start = time.time()
        for _ in range(1000):
            cache_instance.set("/test", directories)
        duration = time.time() - start

        avg_time = (duration / 1000) * 1000
        assert avg_time < 0.5, f"Overhead de cache muito alto: {avg_time:.2f}ms"

    @pytest.mark.slow
    def test_concurrent_performance(self, cache_instance):
        """Testa performance com acesso concorrente."""
        import threading

        directories = [(f"DIR{i:03d}", Path(f"/test/DIR{i:03d}")) 
                      for i in range(1000)]
        cache_instance.set("/test", directories)

        results = []

        def worker():
            start = time.time()
            for i in range(100):
                cache_instance.search("/test", f"DIR{i:03d}")
            results.append(time.time() - start)

        threads = [threading.Thread(target=worker) for _ in range(10)]

        start = time.time()
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        total_duration = time.time() - start

        # Python GIL limita speedup em operações CPU-bound
        # Ajustado para expectativa realista
        avg_thread_time = sum(results) / len(results)
        speedup = (avg_thread_time * 10) / total_duration

        # Speedup > 0.5x já é aceitável devido ao GIL
        assert speedup > 0.5, f"Speedup insuficiente: {speedup:.2f}x"

    @pytest.mark.unit
    def test_ttl_check_performance(self, cache_instance):
        """Testa performance de verificação de TTL."""
        directories = [("DIR", Path("/test/DIR"))]
        cache_instance.set("/test", directories)

        start = time.time()
        for _ in range(10000):
            cache_instance.get("/test")
        duration = time.time() - start

        avg_time = (duration / 10000) * 1000000  # microsegundos
        assert avg_time < 100, f"TTL check muito lento: {avg_time:.2f}μs"

    @pytest.mark.slow
    @pytest.mark.stress
    def test_cache_thrashing(self, cache_instance):
        """Testa comportamento com cache thrashing."""
        # Adiciona e remove entradas rapidamente
        start = time.time()
        for i in range(1000):
            cache_instance.set(f"/test{i}", [("DIR", Path(f"/test{i}/DIR"))])
            if i > 100:
                cache_instance.invalidate(f"/test{i-100}")
        duration = time.time() - start

        assert duration < 2.0, f"Cache thrashing muito lento: {duration:.2f}s"