from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Playfair6x6:
    """29 Türkçe harf + 7 karakter ile çalışan sade 6x6 Playfair sınıfı."""

    key: str

    # 29 harf + 7 karakter = 36 hücre.
    # ^ karakteri mesajda kullanılmayan teknik dolgu karakteridir.
    LETTERS = list("abcçdefgğhıijklmnoöprsştuüvyz")
    SYMBOLS = [" ", ".", ",", "?", "!", ":", "^"]
    CHARSET = LETTERS + SYMBOLS
    FILLER = "^"

    @staticmethod
    def turkish_lower(text: str) -> str:
        """Python'un varsayılan lower() davranışını Türkçe I/İ için düzeltir."""
        table = str.maketrans({
            "I": "ı",
            "İ": "i",
            "Ğ": "ğ",
            "Ü": "ü",
            "Ş": "ş",
            "Ö": "ö",
            "Ç": "ç",
        })
        return text.translate(table).lower()

    def normalize(self, text: str) -> str:
        """Metni matriste bulunan karakterlere indirger; boşluk ve noktalama korunur."""
        lowered = self.turkish_lower(text)
        return "".join(ch for ch in lowered if ch in self.CHARSET)

    def matrix(self) -> list[list[str]]:
        chars: list[str] = []

        for ch in self.normalize(self.key):
            if ch not in chars:
                chars.append(ch)

        for ch in self.CHARSET:
            if ch not in chars:
                chars.append(ch)

        return [chars[i:i + 6] for i in range(0, 36, 6)]

    def positions(self) -> dict[str, tuple[int, int]]:
        return {
            ch: (row_index, col_index)
            for row_index, row in enumerate(self.matrix())
            for col_index, ch in enumerate(row)
        }

    def make_pairs(self, text: str) -> list[tuple[str, str]]:
        """Playfair için metni ikili gruplara ayırır ve gerekli yerlere dolgu ekler."""
        cleaned = self.normalize(text)
        pairs: list[tuple[str, str]] = []
        i = 0

        while i < len(cleaned):
            first = cleaned[i]
            second = cleaned[i + 1] if i + 1 < len(cleaned) else self.FILLER

            if first == second:
                pairs.append((first, self.FILLER))
                i += 1
            else:
                pairs.append((first, second))
                i += 2

        return pairs

    def encrypt(self, plaintext: str) -> str:
        return self._convert(self.make_pairs(plaintext), step=1)

    def decrypt(self, ciphertext: str) -> str:
        cleaned = self.normalize(ciphertext)
        if len(cleaned) % 2 == 1:
            cleaned = cleaned[:-1]

        pairs = [(cleaned[i], cleaned[i + 1]) for i in range(0, len(cleaned), 2)]
        return self._remove_fillers(self._convert(pairs, step=-1))

    def _convert(self, pairs: list[tuple[str, str]], step: int) -> str:
        matrix = self.matrix()
        pos = self.positions()
        result: list[str] = []

        for first, second in pairs:
            r1, c1 = pos[first]
            r2, c2 = pos[second]

            if r1 == r2:
                result.append(matrix[r1][(c1 + step) % 6])
                result.append(matrix[r2][(c2 + step) % 6])
            elif c1 == c2:
                result.append(matrix[(r1 + step) % 6][c1])
                result.append(matrix[(r2 + step) % 6][c2])
            else:
                result.append(matrix[r1][c2])
                result.append(matrix[r2][c1])

        return "".join(result)

    def _remove_fillers(self, text: str) -> str:
        """Şifreleme sırasında eklenen dolgu karakterlerini temizler."""
        cleaned: list[str] = []
        i = 0

        while i < len(text):
            is_repeated_letter_filler = (
                i + 2 < len(text)
                and text[i] == text[i + 2]
                and text[i + 1] == self.FILLER
            )
            if is_repeated_letter_filler:
                cleaned.append(text[i])
                i += 2
            else:
                cleaned.append(text[i])
                i += 1

        return "".join(cleaned).rstrip(self.FILLER)

    def matrix_as_text(self) -> str:
        """Arayüzde boşluk hücresini görünür kılar."""
        def show(ch: str) -> str:
            return "␠" if ch == " " else ch

        return "\n".join("  ".join(show(ch) for ch in row) for row in self.matrix())
