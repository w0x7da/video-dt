"""Tokenizer wrapper: tiktoken, HuggingFace, or simple character-level fallback."""

import logging

logger = logging.getLogger(__name__)

# Special token IDs (reserved at the start of vocab)
_PAD_ID = 0
_BOS_ID = 1
_EOS_ID = 2


class TokenizerWrapper:
    """Unified tokenizer interface.

    Backends:
        - "tiktoken": Uses tiktoken cl100k_base (needs network on first use).
        - "huggingface": Uses HuggingFace AutoTokenizer.
        - "simple": Character-level tokenizer, fully offline (for testing/PoC).
    """

    def __init__(
        self,
        backend: str = "tiktoken",
        model_name: str = "cl100k_base",
    ) -> None:
        """Initialize the tokenizer.

        Args:
            backend: "tiktoken", "huggingface", or "simple".
            model_name: For tiktoken, the encoding name. For huggingface, the model name.
        """
        self.backend = backend
        self._pad_id = _PAD_ID
        self._bos_id = _BOS_ID
        self._eos_id = _EOS_ID

        if backend == "tiktoken":
            try:
                import tiktoken
                self._enc = tiktoken.get_encoding(model_name)
                self._vocab_size = self._enc.n_vocab + 3
                self._offset = 3  # Shift all tiktoken IDs by 3 to reserve 0,1,2
            except Exception as e:
                logger.warning(f"tiktoken failed ({e}), falling back to simple tokenizer")
                self.backend = "simple"
                self._vocab_size = 259  # 256 bytes + 3 special tokens
                self._offset = 3
        elif backend == "huggingface":
            from transformers import AutoTokenizer
            self._tok = AutoTokenizer.from_pretrained(model_name)
            if self._tok.pad_token is None:
                self._tok.pad_token = self._tok.eos_token
            self._vocab_size = self._tok.vocab_size
            self._pad_id = self._tok.pad_token_id
            self._bos_id = self._tok.bos_token_id or 1
            self._eos_id = self._tok.eos_token_id or 2
        elif backend == "simple":
            self._vocab_size = 259  # 256 bytes + 3 special tokens
            self._offset = 3
        else:
            raise ValueError(f"Unknown backend: {backend}. Use 'tiktoken', 'huggingface', or 'simple'.")

    @property
    def vocab_size(self) -> int:
        return self._vocab_size

    @property
    def pad_token_id(self) -> int:
        return self._pad_id

    @property
    def bos_token_id(self) -> int:
        return self._bos_id

    @property
    def eos_token_id(self) -> int:
        return self._eos_id

    def encode(
        self,
        text: str,
        add_bos: bool = False,
        add_eos: bool = False,
    ) -> list[int]:
        """Encode text to token IDs.

        Args:
            text: Input text string.
            add_bos: Prepend BOS token.
            add_eos: Append EOS token.

        Returns:
            List of token IDs.
        """
        if self.backend == "tiktoken":
            ids = [tid + self._offset for tid in self._enc.encode(text)]
        elif self.backend == "simple":
            ids = [b + self._offset for b in text.encode("utf-8")]
        else:
            ids = self._tok.encode(text, add_special_tokens=False)

        if add_bos:
            ids = [self._bos_id] + ids
        if add_eos:
            ids = ids + [self._eos_id]
        return ids

    def decode(self, ids: list[int]) -> str:
        """Decode token IDs back to text.

        Args:
            ids: List of token IDs.

        Returns:
            Decoded text string.
        """
        # Filter out special tokens
        special = {self._pad_id, self._bos_id, self._eos_id}
        if self.backend == "tiktoken":
            clean_ids = [tid - self._offset for tid in ids if tid not in special]
            return self._enc.decode(clean_ids)
        elif self.backend == "simple":
            clean_bytes = bytes(
                tid - self._offset for tid in ids
                if tid not in special and 0 <= tid - self._offset < 256
            )
            return clean_bytes.decode("utf-8", errors="replace")
        else:
            clean_ids = [tid for tid in ids if tid not in special]
            return self._tok.decode(clean_ids)

    def batch_encode(
        self,
        texts: list[str],
        max_length: int = 512,
        add_bos: bool = False,
        add_eos: bool = False,
    ) -> dict[str, list[list[int]]]:
        """Encode a batch of texts with padding.

        Args:
            texts: List of text strings.
            max_length: Maximum sequence length (truncate if longer).
            add_bos: Prepend BOS token.
            add_eos: Append EOS token.

        Returns:
            Dict with 'input_ids' and 'attention_mask' (lists of lists).
        """
        all_ids = []
        for text in texts:
            ids = self.encode(text, add_bos=add_bos, add_eos=add_eos)
            ids = ids[:max_length]
            all_ids.append(ids)

        # Pad to longest in batch
        max_len = max(len(ids) for ids in all_ids)
        padded_ids = []
        masks = []
        for ids in all_ids:
            pad_len = max_len - len(ids)
            padded_ids.append(ids + [self._pad_id] * pad_len)
            masks.append([1] * len(ids) + [0] * pad_len)

        return {"input_ids": padded_ids, "attention_mask": masks}
