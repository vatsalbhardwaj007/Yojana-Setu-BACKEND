"""Tests for scheme data service."""

from whatsapp import scheme_service


class TestSchemeService:
    def test_scheme_count(self):
        count = scheme_service.scheme_count()
        assert count > 0
        assert count == 15

    def test_list_schemes(self):
        schemes = scheme_service.list_schemes()
        assert len(schemes) == 15
        for s in schemes:
            assert "scheme_code" in s
            assert "name" in s
            assert "description" in s
            assert "scheme_type" in s

    def test_get_scheme_names_indexed(self):
        indexed = scheme_service.get_scheme_names_indexed()
        assert len(indexed) == 15
        assert indexed[0]["index"] == 1
        assert indexed[-1]["index"] == 15

    def test_get_scheme_by_index(self):
        scheme = scheme_service.get_scheme_by_index(1)
        assert scheme is not None
        assert "name" in scheme

    def test_get_scheme_by_index_out_of_range(self):
        assert scheme_service.get_scheme_by_index(0) is None
        assert scheme_service.get_scheme_by_index(999) is None

    def test_get_scheme_code_by_index(self):
        code = scheme_service.get_scheme_code_by_index(1)
        assert code is not None
        assert isinstance(code, str)

    def test_get_scheme(self):
        schemes = scheme_service.list_schemes()
        first_code = schemes[0]["scheme_code"]
        scheme = scheme_service.get_scheme(first_code)
        assert scheme is not None
        assert scheme["scheme_code"] == first_code

    def test_get_scheme_not_found(self):
        assert scheme_service.get_scheme("nonexistent_scheme") is None

    def test_get_scheme_documents(self):
        schemes = scheme_service.list_schemes()
        first_code = schemes[0]["scheme_code"]
        docs = scheme_service.get_scheme_documents(first_code)
        assert isinstance(docs, list)

    def test_get_scheme_documents_not_found(self):
        docs = scheme_service.get_scheme_documents("nonexistent")
        assert docs == []

    def test_get_scheme_tutorial(self):
        schemes = scheme_service.list_schemes()
        first_code = schemes[0]["scheme_code"]
        steps = scheme_service.get_scheme_tutorial(first_code)
        assert isinstance(steps, list)

    def test_get_scheme_benefits(self):
        schemes = scheme_service.list_schemes()
        first_code = schemes[0]["scheme_code"]
        benefits = scheme_service.get_scheme_benefits(first_code)
        assert isinstance(benefits, list)

    def test_get_scheme_official_url(self):
        schemes = scheme_service.list_schemes()
        first_code = schemes[0]["scheme_code"]
        url = scheme_service.get_scheme_official_url(first_code)
        if url:
            assert url.startswith("http")

    def test_search_schemes(self):
        results = scheme_service.search_schemes("kisan")
        assert len(results) > 0
        assert any("Kisan" in r["name"] or "KISAN" in r["name"] for r in results)

    def test_search_schemes_no_match(self):
        results = scheme_service.search_schemes("xyznonexistent")
        assert results == []

    def test_all_schemes_have_required_fields(self):
        schemes = scheme_service.list_schemes()
        for s in schemes:
            full = scheme_service.get_scheme(s["scheme_code"])
            assert full is not None
            assert "scheme_code" in full
            assert "name" in full
            assert "description" in full
            assert "ministry" in full
            assert "department" in full
            assert "scheme_type" in full
            assert "status" in full
            assert "effective_from" in full
            assert "last_verified_at" in full

    def test_benefits_are_strings(self):
        schemes = scheme_service.list_schemes()
        for s in schemes:
            full = scheme_service.get_scheme(s["scheme_code"])
            benefits = full.get("benefits", [])
            for b in benefits:
                assert isinstance(b, str), f"Non-string benefit in {s['scheme_code']}: {b}"

    def test_scheme_code_matches_filename(self):
        import json
        from whatsapp.config import SCHEMES_DIR
        for path in sorted(SCHEMES_DIR.glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            assert data.get("scheme_code") == path.stem, (
                f"File {path.name} has scheme_code {data.get('scheme_code')}"
            )
