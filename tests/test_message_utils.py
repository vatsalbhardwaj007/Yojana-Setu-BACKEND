"""Tests for message splitting utility."""

from whatsapp.message_utils import split_message, WHATSAPP_TEXT_MAX_LENGTH


class TestSplitMessage:
    def test_short_message_unchanged(self):
        msg = "Hello, this is a short message."
        result = split_message(msg)
        assert result == [msg]

    def test_empty_string(self):
        result = split_message("")
        assert result == [""]

    def test_exact_limit(self):
        msg = "a" * WHATSAPP_TEXT_MAX_LENGTH
        result = split_message(msg)
        assert len(result) == 1
        assert result[0] == msg

    def test_one_over_limit(self):
        msg = "a" * (WHATSAPP_TEXT_MAX_LENGTH + 1)
        result = split_message(msg)
        assert len(result) == 2
        assert len(result[0]) == WHATSAPP_TEXT_MAX_LENGTH
        assert len(result[1]) == 1

    def test_splits_at_newline(self):
        line1 = "Line one content here\n"
        line2 = "Line two content here\n"
        msg = line1 + line2 + "d" * (WHATSAPP_TEXT_MAX_LENGTH - len(line1) - len(line2) + 100)
        result = split_message(msg)
        # Should split at a newline boundary, not mid-text
        assert len(result) >= 2
        for chunk in result:
            assert len(chunk) <= WHATSAPP_TEXT_MAX_LENGTH
        # Reassembled should equal original
        assert "".join(result) == msg

    def test_hard_split_when_no_newlines(self):
        msg = "x" * 5000
        result = split_message(msg)
        assert len(result) == 2
        assert len(result[0]) == WHATSAPP_TEXT_MAX_LENGTH
        assert len(result[1]) == 5000 - WHATSAPP_TEXT_MAX_LENGTH

    def test_multiple_splits(self):
        msg = ("a" * 2000 + "\n") * 3
        result = split_message(msg, max_length=4096)
        # 3 lines of ~2001 chars each = ~6003 total, needs 2 chunks
        assert len(result) >= 2
        assert "".join(result) == msg

    def test_all_chunks_within_limit(self):
        # Simulate a very long tutorial message
        steps = []
        for i in range(25):
            steps.append(f"Step {i+1}: This is a detailed step description.\n" + "d" * 200 + "\n")
        msg = "".join(steps)
        result = split_message(msg, max_length=4096)
        for i, chunk in enumerate(result):
            assert len(chunk) <= WHATSAPP_TEXT_MAX_LENGTH, f"Chunk {i} exceeds limit: {len(chunk)}"
        assert "".join(result) == msg

    def test_preserves_newline_at_split_point(self):
        # Line that fills most of the limit, then a newline, then more text
        filler = "a" * (WHATSAPP_TEXT_MAX_LENGTH - 5)
        msg = filler + "\nNext part"
        result = split_message(msg)
        assert len(result) == 2
        assert result[0].endswith("\n")
        assert result[1] == "Next part"

    def test_single_long_line_hard_split(self):
        msg = "a" * 10000
        result = split_message(msg)
        for chunk in result:
            assert len(chunk) <= WHATSAPP_TEXT_MAX_LENGTH
        assert "".join(result) == msg

    def test_custom_max_length(self):
        msg = "abcdef"
        result = split_message(msg, max_length=3)
        assert result == ["abc", "def"]

    def test_custom_max_length_with_newline(self):
        msg = "ab\ncdef"
        result = split_message(msg, max_length=4)
        assert result[0] == "ab\n"
        assert result[1] == "cdef"
