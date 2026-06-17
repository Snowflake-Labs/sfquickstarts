package snowflake.utils;
import java.security.Key;
import java.util.Base64;
import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;

public class TokenizeEncryptUtils {
// Helper Utility for AES256 encryption/decryption(Simple demonstration)
  private static String ALGORITHM = "AES";
  private static Key KEY;
  private String KEY_STRING;  // should get from secure key vault
  private static KeyGenerator KEYGENERATOR;
  private static Cipher CIPHER;
  private int TOKEN_KEY;

  public TokenizeEncryptUtils(String k,int token) throws Exception {
    this();
    setKey(k);
    TOKEN_KEY=token;
  }
  public TokenizeEncryptUtils() throws Exception {
    // Initialize Cipher
    CIPHER = Cipher.getInstance(ALGORITHM);
    if (KEYGENERATOR != null) KEY = KEYGENERATOR.generateKey();
    KEYGENERATOR = KeyGenerator.getInstance(ALGORITHM);
    KEY = KEYGENERATOR.generateKey();
    //TOKEN_KEY=token;
  }
  public String encrypt(String s) throws Exception {
    CIPHER.init(Cipher.ENCRYPT_MODE, KEY);
    return Base64.getEncoder().encodeToString(CIPHER.doFinal(s.getBytes("UTF-8")));
  }

  public String decrypt(String s) throws Exception {
    CIPHER.init(Cipher.DECRYPT_MODE, KEY);
    return new String(CIPHER.doFinal(Base64.getDecoder().decode(s)));
  }

  public String getKey() throws Exception {
    return KEY_STRING;
  }

  public String getKeyEncoded() throws Exception {
    return new String(KEY.getEncoded(),StandardCharsets.UTF_8);
  }



  //O90hS0k9qHdsMDkPe46ZcQ== (input)
  //TzkwaFMwazlxSGRzTURrUGU0NlpjUT09 (output, MEANINGLESS)
  public void setKey(String k) throws Exception {
      KEY_STRING=k;
      byte[] k0 = new String(k.toCharArray()).getBytes(StandardCharsets.UTF_8);
      SecretKeySpec secretKey = new SecretKeySpec(k0,ALGORITHM);
      KEY=secretKey;
  }

  public int getToken() throws Exception {
    return TOKEN_KEY;
  }

  public void setToken(int t) throws Exception {
    TOKEN_KEY=t;
  }

  public String tokenize(long id){
    return Long.toHexString(id*TOKEN_KEY).toString();
  }
}
