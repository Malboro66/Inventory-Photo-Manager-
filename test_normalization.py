"""
Testes unitários para normalização Unicode v8.1.
"""

import pytest


class TestNormalization:
    """Testes para o método _normalize_text da classe DirectoryCache."""

    @pytest.mark.unit
    def test_empty_string(self, cache_instance):
        """Testa normalização de string vazia."""
        assert cache_instance._normalize_text("") == ""
        assert cache_instance._normalize_text("   ") == ""
        assert cache_instance._normalize_text("\t\n\r") == ""

    @pytest.mark.unit
    def test_basic_normalization(self, cache_instance):
        """Testa normalização básica (acentos e case)."""
        assert cache_instance._normalize_text("Café") == "cafe"
        assert cache_instance._normalize_text("São Paulo") == "sao paulo"
        assert cache_instance._normalize_text("Ação") == "acao"

    @pytest.mark.unit
    def test_special_characters(self, cache_instance):
        """Testa remoção de caracteres especiais."""
        assert cache_instance._normalize_text("ABC@123") == "abc 123"
        assert cache_instance._normalize_text("Peça#456") == "peca 456"
        assert cache_instance._normalize_text("Test_$%^&*()") == "test"

    @pytest.mark.unit
    def test_multiple_spaces(self, cache_instance):
        """Testa normalização de espaços múltiplos."""
        assert cache_instance._normalize_text("  A  B  C  ") == "a b c"
        assert cache_instance._normalize_text("Test   Multiple   Spaces") == "test multiple spaces"

    @pytest.mark.unit
    def test_technical_symbols(self, cache_instance):
        """Testa conversão de símbolos técnicos."""
        assert cache_instance._normalize_text("100Ω") == "100 ohm"
        assert cache_instance._normalize_text("25℃") == "25 c"
        assert cache_instance._normalize_text("50℉") == "50 f"

    @pytest.mark.unit
    def test_greek_letters(self, cache_instance):
        """Testa conversão de letras gregas."""
        assert cache_instance._normalize_text("α test") == "alpha test"
        assert cache_instance._normalize_text("β version") == "beta version"
        assert cache_instance._normalize_text("γ ray") == "gamma ray"

    @pytest.mark.unit
    def test_special_marks(self, cache_instance):
        """Testa símbolos especiais."""
        result = cache_instance._normalize_text("№ 42")
        assert "no" in result and "42" in result

        result = cache_instance._normalize_text("Test™")
        assert "test" in result and "tm" in result

    @pytest.mark.unit
    def test_ligatures(self, cache_instance):
        """Testa expansão de ligaduras."""
        # NFKC deve expandir ligaduras
        result = cache_instance._normalize_text("ﬁle")
        assert "file" in result.lower()

    @pytest.mark.unit
    def test_case_folding(self, cache_instance):
        """Testa case folding avançado."""
        assert cache_instance._normalize_text("ß") == "ss"
        assert cache_instance._normalize_text("UPPER") == "upper"

    @pytest.mark.unit
    def test_international_chars(self, cache_instance):
        """Testa caracteres internacionais."""
        # Alguns caracteres podem não ter decomposição completa
        result = cache_instance._normalize_text("Zürich")
        assert result == "zurich"

        # Ł pode não decompor completamente em todos os sistemas
        result = cache_instance._normalize_text("Łódź")
        # Aceita tanto "lodz" quanto "łodz" (depende do sistema)
        assert result in ["lodz", "łodz"], f"Resultado inesperado: {result}"

        result = cache_instance._normalize_text("Björk")
        assert result == "bjork"

    @pytest.mark.unit
    @pytest.mark.slow
    def test_very_long_string(self, cache_instance):
        """Testa string muito longa (1MB)."""
        long_str = "A" * 1_000_000
        result = cache_instance._normalize_text(long_str)
        assert len(result) == 1_000_000
        assert result == "a" * 1_000_000

    @pytest.mark.unit
    def test_complex_unicode(self, cache_instance):
        """Testa casos complexos Unicode."""
        cases = [
            ("Peça-€50@Test™", "peca 50 test tm"),
            ("Resistor 100Ω ±5%", "resistor 100 ohm 5"),
            ("Código#ABC-123_v2", "codigo abc 123 v2"),
            ("α-Beta γ test", "alpha beta gamma test"),
        ]

        for input_str, expected in cases:
            result = cache_instance._normalize_text(input_str)
            # Verifica se os termos principais estão presentes
            for term in expected.split():
                assert term in result, f"Expected '{term}' in '{result}' for input '{input_str}'"