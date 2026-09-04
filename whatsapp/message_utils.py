"""Message utilities for WhatsApp text message handling."""

WHATSAPP_TEXT_MAX_LENGTH = 4096


def split_message(text: str, max_length: int = WHATSAPP_TEXT_MAX_LENGTH) -> list[str]:
    """Split a text message into chunks that fit within WhatsApp's limit.

    Prefers splitting at newline boundaries. If a single line exceeds
    max_length, it is hard-split at the limit.

    Args:
        text: The full message text.
        max_length: Maximum characters per chunk (default 4096).

    Returns:
        List of message chunks, each <= max_length.
    """
    if not text:
        return [""]

    if len(text) <= max_length:
        return [text]

    chunks = []
    remaining = text

    while remaining:
        if len(remaining) <= max_length:
            chunks.append(remaining)
            break

        # Find the last newline within the limit
        split_at = remaining.rfind("\n", 0, max_length)

        if split_at > 0:
            # Split at the newline; include the newline in the current chunk
            chunks.append(remaining[: split_at + 1])
            remaining = remaining[split_at + 1 :]
        else:
            # No newline found — hard split at max_length
            chunks.append(remaining[:max_length])
            remaining = remaining[max_length:]

    return chunks
