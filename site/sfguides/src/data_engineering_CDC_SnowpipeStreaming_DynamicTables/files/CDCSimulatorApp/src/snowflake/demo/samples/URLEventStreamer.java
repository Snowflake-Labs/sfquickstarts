package snowflake.demo.samples;
import java.util.Properties;
import java.net.URL;
import java.net.HttpURLConnection;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.BufferedReader;


// Sample data generator (Transactional RDBMS Events)
public class URLEventStreamer extends EventStreamer {
    private boolean SHOW_EVENTS=false;
    private URL EVENT_URL = null;

    public URLEventStreamer() throws Exception {
    }
    public URLEventStreamer(Properties p) throws Exception {
        setProperties(p);
    }

    public void setProperties(Properties p) throws Exception {
        super.setProperties(p);
        String showevents=p.getProperty("SHOW_EVENTS");
        if(showevents!=null) SHOW_EVENTS=Boolean.parseBoolean(showevents);
        String urlLocation=p.getProperty("HTTP_URL");
        if(urlLocation==null) throw new Exception ("Parameter 'HTTP_URL' is Required in Property file");
        if(DEBUG) System.out.println("HTTP_URL to Retrieve:  "+urlLocation);
        EVENT_URL = new URL(urlLocation);
    }

    public String getEvent(int transactionid) throws Exception {
        StringBuilder sb = new StringBuilder();
        String line;
        HttpURLConnection connection = (HttpURLConnection)EVENT_URL.openConnection();
        connection.setRequestMethod("GET");
        connection.setUseCaches(false);
        connection.connect();
        InputStream is = connection.getInputStream();
        if(SHOW_EVENTS) System.out.println("URL_RESPONSE_CODE:  "+connection.getResponseCode());
        BufferedReader rd = new BufferedReader(new InputStreamReader(is));
        while ((line = rd.readLine()) != null) sb.append(line);
        rd.close();
        if (DEBUG) System.out.println(sb);
        return sb.toString();
    }
}
