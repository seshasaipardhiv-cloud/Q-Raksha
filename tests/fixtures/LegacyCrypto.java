// Legacy Java crypto — CBOM test fixture
import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import java.security.*;
import java.security.spec.*;

public class LegacyCrypto {

    // RSA-2048 key pair — quantum vulnerable
    public KeyPair generateRSAKeyPair() throws Exception {
        KeyPairGenerator kpg = KeyPairGenerator.getInstance("RSA");
        kpg.initialize(2048);
        return kpg.generateKeyPair();
    }

    // ECDSA — quantum vulnerable
    public KeyPair generateECDSAKeyPair() throws Exception {
        KeyPairGenerator kpg = KeyPairGenerator.getInstance("EC");
        ECGenParameterSpec spec = new ECGenParameterSpec("secp256r1");
        kpg.initialize(spec);
        return kpg.generateKeyPair();
    }

    // MD5 — cryptographically broken
    public String md5Hash(String data) throws Exception {
        MessageDigest md = MessageDigest.getInstance("MD5");
        byte[] digest = md.digest(data.getBytes());
        return bytesToHex(digest);
    }

    // SHA-1 — deprecated
    public String sha1Hash(String data) throws Exception {
        MessageDigest md = MessageDigest.getInstance("SHA-1");
        byte[] digest = md.digest(data.getBytes());
        return bytesToHex(digest);
    }

    // DES — broken symmetric cipher
    public Cipher getDesCipher() throws Exception {
        return Cipher.getInstance("DES/ECB/PKCS5Padding");
    }

    // AES-ECB — pattern-leaking
    public Cipher getAesEcbCipher() throws Exception {
        return Cipher.getInstance("AES/ECB/PKCS5Padding");
    }

    private String bytesToHex(byte[] bytes) {
        StringBuilder sb = new StringBuilder();
        for (byte b : bytes) sb.append(String.format("%02x", b));
        return sb.toString();
    }
}
