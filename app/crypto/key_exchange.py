from __future__ import annotations

import base64
from dataclasses import dataclass

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


@dataclass
class KeyExchange:
    """
    RSA kullanmadan Diffie-Hellman mantığıyla güvenli kanal kurar.

    Kullanım amacı mesajları şifrelemek değildir. Bu sınıf yalnızca bağlantıyı başlatan
    kişinin seçtiği Playfair oturum anahtarını güvenli biçimde karşı tarafa ulaştırmak
    için kullanılır.
    """

    private_key: x25519.X25519PrivateKey

    @classmethod
    def create(cls) -> "KeyExchange":
        return cls(private_key=x25519.X25519PrivateKey.generate())

    def public_key_text(self) -> str:
        public_bytes = self.private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        return base64.b64encode(public_bytes).decode("ascii")

    def build_cipher(self, peer_public_key_text: str) -> Fernet:
        peer_public_bytes = base64.b64decode(peer_public_key_text.encode("ascii"))
        peer_public_key = x25519.X25519PublicKey.from_public_bytes(peer_public_bytes)
        shared_secret = self.private_key.exchange(peer_public_key)

        # İki taraf aynı shared_secret değerine ulaşır. Bu değerden Fernet anahtarı türetilir.
        fernet_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b"encrypted-p2p-chat-session-key",
        ).derive(shared_secret)

        return Fernet(base64.urlsafe_b64encode(fernet_key))
