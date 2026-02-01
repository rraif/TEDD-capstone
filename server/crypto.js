const crypto = require('crypto');

//do we got the key ?
if(!process.env.ENCRYPTION_KEY) {
    throw new Error("encryption key missing in .env");
}

const KEY = Buffer.from(process.env.ENCRYPTION_KEY, 'hex');
const ALGORITHM = 'chacha20-poly1305';

function encrypt(text){
    if(!text) return text;

    //nonce 96 bits (12 bytes)
    const iv = crypto.randomBytes(12)

    //cipher (AEAD produces 16 byte authentication tag so thats why)
    const cipher = crypto.createCipheriv(ALGORITHM, KEY, iv, {authTagLength: 16});

    //encrypt text
    let encrypted = cipher.update(text, 'utf8', 'hex');
    encrypted += cipher.final('hex');

    //authentication tag (integrity)
    const tag = cipher.getAuthTag();

    //nonce: tag: content
    //the ciphertext is sent with the nonce and the auth tag, essential for the receiver to decrypt
    return `${iv.toString('hex')}:${tag.toString('hex')}:${encrypted}`;
}

function decrypt(hash){
    if (!hash) return hash;

    try {
        //split the encrypted message
        const [ivHex, tagHex, encryptedHex] = hash.split(':');

        //convert to buffers (?)
        const iv = Buffer.from(ivHex, 'hex');
        const tag = Buffer.from(tagHex, 'hex');

        //decipherer
        const decipher = crypto.createDecipheriv(ALGORITHM, KEY, iv, { authTagLength: 16});
        decipher.setAuthTag(tag);

        //decrypt
        let decrypted = decipher.update(encryptedHex, 'hex', 'utf8');
        decrypted += decipher.final('utf8')

        return decrypted;
    } catch (err) {
        console.error("decryption failed");
        return null
    }
}

module.exports = {encrypt, decrypt};