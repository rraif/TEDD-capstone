// server/test-crypto.js
require('dotenv').config(); // Load the ENCRYPTION_KEY from .env
const { encrypt, decrypt } = require('./crypto');

const originalText = "This is a secret message used to test ChaCha20-Poly1305";

console.log("1. Original Text:", originalText);

// Test Encryption
const encryptedText = encrypt(originalText);
console.log("\n2. Encrypted (Safe):", encryptedText);

// Test Decryption
const decryptedText = decrypt(encryptedText);
console.log("\n3. Decrypted (Back):", decryptedText);

// Verification
if (originalText === decryptedText) {
    console.log("\nmessage successfully decrypted");
} else {
    console.log("\nstrings dont match");
}