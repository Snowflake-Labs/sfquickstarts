package snowflake.demo;
import snowflake.demo.samples.*;
import java.io.FileInputStream;
import java.io.File;
import java.nio.file.Files;
import java.nio.charset.Charset;
import java.util.HashMap;
import java.util.Map;
import java.util.Base64;
import java.util.Properties;
import java.util.concurrent.TimeUnit;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.impl.SimpleLogger;
import java.lang.reflect.Field;
import net.snowflake.ingest.utils.Logging;
import net.snowflake.ingest.streaming.InsertValidationResponse;
import net.snowflake.ingest.streaming.OpenChannelRequest;
import net.snowflake.ingest.streaming.SnowflakeStreamingIngestChannel;
import net.snowflake.ingest.streaming.SnowflakeStreamingIngestClient;
import net.snowflake.ingest.streaming.SnowflakeStreamingIngestClientFactory;
import java.security.KeyFactory;
import java.security.PrivateKey;
import java.security.PublicKey;
import java.security.interfaces.RSAPrivateKey;
import java.security.spec.InvalidKeySpecException;
import java.security.spec.KeySpec;
import java.security.spec.PKCS8EncodedKeySpec;
import java.security.spec.X509EncodedKeySpec;

/**
 * Example on how to use the Streaming Ingest client APIs
 * Re-used for Event Agent-like Demonstration (Feb, 2023)
 *            Author:  Steven.Maser@snowflake.com
 *
 * <p>Please read the README.md file for detailed steps and expanding beyond this example
 *   https://github.com/snowflakedb/snowflake-ingest-java
 */
public class EventSimulatorClient {
  private static final String PROFILE_PATH = "./snowflake.properties";
  private static String EVENT_HELPER="snowflake.demo.samples.CDCEventStreamer";
  private static boolean DEBUG=false;
  private static int NUM_ROWS=100;  // default rows to insert into landing table
  private Logger LOGGER = new Logging(this.getClass()).getLogger();
  private static String SPEED="MAX";

  public static void main(String[] args) throws Exception {
    if(args!=null && args.length>0) SPEED=args[0];
    //Load profile from properties file
    Properties props=loadProfile();

    //Initialize Sample Data Stream Generator (RDBMS Log / CDC-based)
    EventStreamer ES= (EventStreamer) instantiate(EVENT_HELPER, EventStreamer.class);
    ES.setProperties(props);

    // Create a streaming ingest client
    try (SnowflakeStreamingIngestClient client =
        SnowflakeStreamingIngestClientFactory.builder("CLIENT").setProperties(props).build()) {

      // Create an open channel request on table T_STREAMINGINGEST
      OpenChannelRequest request1 =
          OpenChannelRequest.builder(props.getProperty("channel_name")+"_"+SPEED)
              .setDBName(props.getProperty("database"))
              .setSchemaName(props.getProperty("schema"))
              .setTableName(props.getProperty("table"))
              .setOnErrorOption(OpenChannelRequest.OnErrorOption.CONTINUE)
              .build();

      // Open a streaming ingest channel from the given client
      SnowflakeStreamingIngestChannel channel1 = client.openChannel(request1);

      // if just test, end here
      if(SPEED.equalsIgnoreCase("TEST")){
        System.out.println("   ** Successfully Connected, Test complete! **");
        System.exit(0);
      }
      // corresponds to the row number
      long startTime = System.nanoTime();
      for (int id = 1; id <= NUM_ROWS; id++) {
        // A Map will hold rowset (all columns)
        Map<String, Object> row = new HashMap<>();

        // Insert JSON payload into columnm(go slow for continuous)
        if(!SPEED.equalsIgnoreCase("MAX")) {
          if(id==0) {
            System.out.println();
            System.out.println(" *** SLOW=1,000/second   SLOOW=100/second    SLOOOW=10/second    SLOOOOW=1/second  ***");
            TimeUnit.SECONDS.sleep(5);
          }
          if(SPEED.equalsIgnoreCase("SLOW")) TimeUnit.MILLISECONDS.sleep(1);  // 1000/second
          else if(SPEED.equalsIgnoreCase("SLOOW")) TimeUnit.MILLISECONDS.sleep(10);  // 100/second
          else if(SPEED.equalsIgnoreCase("SLOOOW")) TimeUnit.MILLISECONDS.sleep(100);  // 10/second
          else if(SPEED.equalsIgnoreCase("SLOOOOW")) TimeUnit.MILLISECONDS.sleep(1000);  // 1/second
          else System.out.println("Speed Input Parameter unknown, ignored:  "+SPEED);
          System.out.print(id+" ");
        }
	      row.put("RECORD_CONTENT", ES.getEvent(id));  // one column

        InsertValidationResponse response = channel1.insertRow(row, String.valueOf(id));
        if (response.hasErrors()) {
          // Simply throw exception at first error
          throw response.getInsertErrors().get(0).getException();
        }
      }
      System.out.println("Rows Sent:  "+NUM_ROWS);
      System.out.println("Time to Send:  "+String.format("%.03f", (System.nanoTime() - startTime)*1.0/1000000000)+ " seconds");
      // Polling Snowflake to confirm delivery (using fetch offset token registered in Snowflake)
      int retryCount = 0;
      int maxRetries = 100;
      String expectedOffsetTokenInSnowflake=String.valueOf(NUM_ROWS);
      //String offsetTokenFromSnowflake = channel1.getLatestCommittedOffsetToken();
      for (String offsetTokenFromSnowflake = channel1.getLatestCommittedOffsetToken();offsetTokenFromSnowflake == null
          || !offsetTokenFromSnowflake.equals(expectedOffsetTokenInSnowflake);) {
        if(DEBUG) System.out.println("Offset:  "+offsetTokenFromSnowflake);
        Thread.sleep(NUM_ROWS/1000);
        offsetTokenFromSnowflake = channel1.getLatestCommittedOffsetToken();
        retryCount++;
        if (retryCount >= maxRetries) {
          System.out.println(
              String.format(
                  "Failed to look for required OffsetToken in Snowflake:%s after MaxRetryCounts:%s (%S)",
                  expectedOffsetTokenInSnowflake, maxRetries, offsetTokenFromSnowflake));
          System.exit(1);
        }
      }
      System.out.println("SUCCESSFULLY inserted " + NUM_ROWS + " rows");
      System.out.println("Total Time, including Confirmation:  "+String.format("%.03f", (System.nanoTime() - startTime)*1.0/1000000000)+ " seconds");
    }
  }

  private static Properties loadProfile() throws Exception {
    Properties props = new Properties();
    try {
      File f = new File(PROFILE_PATH);
      if (!f.exists()) throw new Exception("Unable to find profile file:  " + PROFILE_PATH);
      FileInputStream resource = new FileInputStream(PROFILE_PATH);
      props.load(resource);
      String num_rows=props.getProperty("NUM_ROWS");
      if(num_rows!=null) NUM_ROWS=Integer.parseInt(num_rows);
      String debug = props.getProperty("DEBUG");
      if (debug != null) DEBUG = Boolean.parseBoolean(debug);
      if (DEBUG) {
        for (Object key : props.keySet())
          System.out.println("  * DEBUG: " + key + ": " + props.getProperty(key.toString()));
      }
      else System.setProperty(org.slf4j.impl.SimpleLogger.DEFAULT_LOG_LEVEL_KEY, "ERROR");

      String helper=props.getProperty("EVENT_HELPER");
      if(helper!=null) EVENT_HELPER=helper;
      if (props.getProperty("private_key_file") != null) {
        String keyfile = props.getProperty("private_key_file");
        File key = new File(keyfile);
        if (!(key).exists()) throw new Exception("Unable to find key file:  " + keyfile);
        String pkey = readPrivateKey(key);
        props.setProperty("private_key", pkey);
      }
      props.setProperty("scheme","https");
      props.setProperty("port","443");
    } catch (Exception ex) {
      ex.printStackTrace();
      System.exit(-1);
    }
    return props;
  }

  public static <T> T instantiate(final String className, final Class<T> type) throws Exception {
    return type.cast(Class.forName(className).getDeclaredConstructor().newInstance());
  }

  private static String readPrivateKey(File file) throws Exception {
    String key = new String(Files.readAllBytes(file.toPath()), Charset.defaultCharset());
    String privateKeyPEM = key
            .replace("-----BEGIN PRIVATE KEY-----", "")
            .replaceAll(System.lineSeparator(), "")
            .replace("-----END PRIVATE KEY-----", "");
    if(DEBUG) {  // check key file is valid
      byte[] encoded = Base64.getDecoder().decode(privateKeyPEM);
      KeyFactory keyFactory = KeyFactory.getInstance("RSA");
      PKCS8EncodedKeySpec keySpec = new PKCS8EncodedKeySpec(encoded);
      RSAPrivateKey k = (RSAPrivateKey) keyFactory.generatePrivate(keySpec);
      System.out.println("* DEBUG: Provided Private Key is Valid:  ");
    }
    return privateKeyPEM;
  }
}

