"""EIP-191 signature verification for wallet authentication."""
from __future__ import annotations

from eth_account import Account
from eth_account.messages import encode_defunct


class SignatureVerifier:
    """Verifies EIP-191 signed messages from Web3 wallets."""

    @staticmethod
    def verify_signature(message: str, signature: str, expected_address: str) -> bool:
        """
        Verify that a message was signed by the expected wallet address.

        Args:
            message: The original message that was signed (typically the nonce)
            signature: The signature hex string (with or without 0x prefix)
            expected_address: The wallet address that should have signed (with or without 0x prefix)

        Returns:
            True if signature is valid and matches expected address, False otherwise
        """
        try:
            # Normalize addresses
            expected_address = expected_address.lower()
            if expected_address.startswith("0x"):
                expected_address = expected_address[2:]
            else:
                expected_address = expected_address

            # Normalize signature
            if isinstance(signature, str):
                if signature.startswith("0x"):
                    signature = signature
                else:
                    signature = "0x" + signature

            # Create message using EIP-191 standard
            message_hash = encode_defunct(text=message)

            # Recover the signer address
            recovered_address = Account.recover_message(message_hash, signature=signature)
            recovered_address = recovered_address.lower()

            # Compare addresses
            return recovered_address == expected_address
        except Exception:
            # Any error in signature verification should return False
            return False
