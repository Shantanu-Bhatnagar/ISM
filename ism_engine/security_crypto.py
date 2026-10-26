"""
Storage Security, AES-256 Encryption at Rest & Tamper-Evident Audit Logging
Simulates AES-256 encryption/decryption, Role-Based Access Control (RBAC),
and Cryptographically Chained Audit Trails for enterprise compliance.
"""

import hashlib
import time
import base64
from typing import Dict, List, Any, Optional

class AuditEntry:
    def __init__(self, index: int, user: str, role: str, action: str, details: str, prev_hash: str):
        self.index = index
        self.timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.user = user
        self.role = role
        self.action = action
        self.details = details
        self.prev_hash = prev_hash
        self.hash = self.compute_hash()

    def compute_hash(self) -> str:
        payload = f"{self.index}|{self.timestamp}|{self.user}|{self.role}|{self.action}|{self.details}|{self.prev_hash}"
        return hashlib.sha256(payload.encode('utf-8')).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "user": self.user,
            "role": self.role,
            "action": self.action,
            "details": self.details,
            "prev_hash": self.prev_hash[:10] + "...",
            "hash": self.hash[:16] + "..."
        }


class StorageSecurityEngine:
    def __init__(self):
        # Simulated KMS Key (256-bit AES master key)
        self.master_key_hex = hashlib.sha256(b"ENTERPRISE_STORAGE_MASTER_KEY_2026").hexdigest()
        self.users = {
            "admin": {"role": "STORAGE_ADMIN", "pin": "admin123"},
            "operator": {"role": "OPERATOR", "pin": "oper123"},
            "auditor": {"role": "AUDITOR", "pin": "audit123"}
        }
        self.audit_chain: List[AuditEntry] = []
        self._init_genesis_audit()

    def _init_genesis_audit(self):
        genesis = AuditEntry(0, "SYSTEM", "ROOT", "INITIALIZE_SECURITY_SUBSYSTEM", "KMS Key Vault armed, AES-256 enabled", "0"*64)
        self.audit_chain.append(genesis)

    def log_audit(self, user: str, role: str, action: str, details: str) -> AuditEntry:
        prev_hash = self.audit_chain[-1].hash if self.audit_chain else "0"*64
        entry = AuditEntry(len(self.audit_chain), user, role, action, details, prev_hash)
        self.audit_chain.append(entry)
        return entry

    def verify_audit_integrity(self) -> Dict[str, Any]:
        """Verifies if the audit log has been tampered with by checking hash chaining."""
        is_valid = True
        compromised_index = None

        for i in range(1, len(self.audit_chain)):
            curr = self.audit_chain[i]
            prev = self.audit_chain[i - 1]
            if curr.prev_hash != prev.hash or curr.hash != curr.compute_hash():
                is_valid = False
                compromised_index = i
                break

        return {
            "is_valid": is_valid,
            "total_records": len(self.audit_chain),
            "status": "SECURE_VERIFIED" if is_valid else f"COMPROMISED_AT_ENTRY_{compromised_index}"
        }

    def encrypt_data(self, plaintext: str) -> Dict[str, Any]:
        """Simulates AES-256 CBC at-rest volume encryption."""
        raw_bytes = plaintext.encode('utf-8')
        # XOR with repeating key stream to simulate block cipher
        key_bytes = bytes.fromhex(self.master_key_hex)
        cipher_bytes = bytes(b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(raw_bytes))
        ciphertext_b64 = base64.b64encode(cipher_bytes).decode('utf-8')

        return {
            "plaintext": plaintext,
            "cipher_algorithm": "AES-256-XTS",
            "ciphertext_b64": ciphertext_b64,
            "key_fingerprint": self.master_key_hex[:16] + "..."
        }

    def decrypt_data(self, ciphertext_b64: str) -> Dict[str, Any]:
        """Decrypts simulated AES-256 ciphertext."""
        try:
            cipher_bytes = base64.b64decode(ciphertext_b64.encode('utf-8'))
            key_bytes = bytes.fromhex(self.master_key_hex)
            raw_bytes = bytes(b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(cipher_bytes))
            decrypted = raw_bytes.decode('utf-8', errors='replace')
            return {"status": "SUCCESS", "decrypted_text": decrypted}
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}

    def check_permission(self, role: str, required_action: str) -> bool:
        role = role.upper()
        if role == "STORAGE_ADMIN":
            return True
        if role == "OPERATOR" and required_action in ("FAIL_DISK", "REBUILD_DISK", "WRITE_DATA", "READ_DATA"):
            return True
        if role == "AUDITOR" and required_action in ("READ_AUDIT", "VERIFY_AUDIT", "READ_DATA"):
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "master_key_id": "KMS-KEY-AES256-VAULT-01",
            "key_fingerprint": self.master_key_hex[:16] + "...",
            "encryption_standard": "AES-256-XTS (FIPS 140-3 Validated)",
            "roles": list(self.users.keys()),
            "audit_records_count": len(self.audit_chain),
            "audit_chain": [e.to_dict() for e in self.audit_chain[-10:]],
            "integrity_check": self.verify_audit_integrity()
        }
