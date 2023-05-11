package snowflake.demo.samples;
import snowflake.utils.TokenizeEncryptUtils;
import java.util.HashMap;
import java.util.ArrayList;
import java.time.Instant;
import java.util.Properties;


// Sample data generator (Transactional RDBMS Events)
public class CDCEventStreamer extends EventStreamer {
    private static ArrayList<String> S_TICKER = new ArrayList<>();
    HashMap<Integer,String[]> CLIENT_ORDERS;
    private TokenizeEncryptUtils CHELPER;
    private boolean SHOW_EVENTS=false;

    public CDCEventStreamer() throws Exception {
    }
    public CDCEventStreamer(Properties p) throws Exception {
        setProperties(p);
    }

    public void setProperties(Properties p) throws Exception {
        super.setProperties(p);
        CLIENT_ORDERS = new HashMap<>();
        String key=p.getProperty("AES_KEY");
        if(key==null) throw new Exception ("Property 'AES_KEY' is required" );
        String token=p.getProperty("TOKEN_KEY");
        if(token==null) throw new Exception ("Property 'TOKEN_KEY' is required" );
        String showevents=p.getProperty("SHOW_EVENTS");
        if(showevents!=null) SHOW_EVENTS=Boolean.parseBoolean(showevents);
        CHELPER=new TokenizeEncryptUtils(key,Integer.parseInt(token));
        if(DEBUG) System.out.println("*AES_KEY IS:  "+CHELPER.getKey());
        if(DEBUG) System.out.println("*AES_KEY-ENCODED IS:  "+CHELPER.getKeyEncoded());
        if(DEBUG) System.out.println("*TOKEN_KEY IS:  "+CHELPER.getToken());
    }

    public String getEvent(int transactionid) throws Exception {
        int client = randomInt(0, NUM_CLIENTS);
        long commit_epoch = Instant.now().toEpochMilli();  // simulated timestamp the event occurred in database
        String[] stockinfo = ((String) S_TICKER.get(randomInt(0, S_TICKER.size()))).split("\\|");
        String dbuser=(randomInt(0, 2) % 2 == 0 ? USERS[randomInt(0, TRANSACTIONTYPES.length )] : "algorithmic");
        String[] s = new String[6];
        String orderid_tokenized=null;
        String orderid_encrypted = null;
        String action = TRANSACTIONTYPES[randomInt(0, TRANSACTIONTYPES.length )];
        if (action=="INSERT" || CLIENT_ORDERS.size() == 0 || CLIENT_ORDERS.get(client) == null) {
            action = "INSERT";
            String sti0=String.format("%03d", transactionid);// short transaction id, to make sure unique primary key within same millisecond
            String sti1=sti0.substring(sti0.length() - 3);
            String sti=String.valueOf(commit_epoch) + sti1;
            long sti_long = Long.parseLong(sti);  // set format, 000-999
            orderid_tokenized = CHELPER.tokenize(sti_long);
            orderid_encrypted = CHELPER.encrypt(sti);
            s[0]=orderid_tokenized;
            s[1]=orderid_encrypted;
            s[2]=stockinfo[1];
            s[3]=""+(randomInt(0, 3) % 2 == 1 ? "LONG" : "SHORT");
            s[4]=""+randomInt(1, 1000);
            s[5]=""+NF_AMT.format(Double.parseDouble(stockinfo[2]) + randomDouble(-2, 2));
            CLIENT_ORDERS.put(client,s);
        }
        else {
            s = (String[]) CLIENT_ORDERS.get(client);
            orderid_tokenized = s[0];
            orderid_encrypted = s[1];
        }
        StringBuilder sb = new StringBuilder()
                .append("{")
                .append("\"object\":\"cdc_db_table_commit\",")
                .append("\"transaction\":{")
                .append("\"transaction_id\":" + transactionid + ",")
                .append("\"schema\":\"PROD\",")
                .append("\"table\":\"LIMIT_ORDERS\",")
                .append("\"action\":" + "\"" + action + "\",")
                .append("\"primaryKey_tokenized\":" + "\"" + orderid_tokenized + "\",")
                .append("\"dbuser\":" + "\"" + dbuser + "\",")
                .append("\"committed_at\":" + commit_epoch + ","); //epoch millisecond time used by source DB
        if (action == "INSERT") sb.append("\"record_before\":{},");
        else {
            sb.append("\"record_before\":{")
                    .append("\"orderid_encrypted\":\"" + orderid_encrypted + "\",")
                    .append("\"client\":" + client + ",")
                    .append("\"ticker\":\"" + s[2] + "\",")
                    .append("\"LongOrShort\":\"" + s[3] + "\",")
                    .append("\"Quantity\":" + s[4] + ",")
                    .append("\"Price\":" + s[5])
                    .append("},");
        }
        if (action == "DELETE") {
            CLIENT_ORDERS.remove(client);
            sb.append("\"record_after\":{}");
        } else {
            if (action == "UPDATE") {
                if (randomInt(1, 6) % 2 == 0) s[5] = NF_AMT.format(Double.parseDouble(s[5]) + randomDouble(-1, 1));
                else s[4] = "" + randomInt(1, 1000);
                CLIENT_ORDERS.replace(client, s);
            }
            sb.append("\"record_after\":{")
                    .append("\"orderid_encrypted\":\"" + s[1] + "\",")
                    .append("\"client\":" + client + ",")
                    .append("\"ticker\":\"" + s[2] + "\",")
                    .append("\"LongOrShort\":\"" + s[3] + "\",")
                    .append("\"Quantity\":" + s[4] + ",")
                    .append("\"Price\":" + s[5])
                    .append("}");
        }
        sb.append("}");
        sb.append("}");
        if(SHOW_EVENTS) System.out.println("ORDER:  "+orderid_tokenized);
        else if (DEBUG) System.out.println(sb);
        return sb.toString();
    }

    // Sample Data Static Values
    String[] TRANSACTIONTYPES={"INSERT","INSERT","INSERT","UPDATE","UPDATE","DELETE"};
    String[] USERS={"rsmith","mmouse","jsnow","fjohnson","areddy","jpatel","stiger","mgrover","cchau","janderson"};
    int NUM_CLIENTS=200;
    private static final String SSTRING = "3M Company|MMM|130;The American Express Company|AXP|155;Apple Inc.|AAPL|135;The Boeing Company|BA|215;Caterpillar Inc.|CAT|260;Chevron Corporation|CVX|175;Cisco Systems Inc.|CSCO|50;The Coca-Cola Company|KO|60;Dow Inc.|DD|75;Exxon Mobil Corporation|XOM|115;The Goldman Sachs Group, Inc.|GS|375;The Home Depot Inc.|HD|330;International Business Machines Corporation|IBM|145;Intel Corporation|INTC|30;Johnson & Johnson|JNJ|175;JPMorgan Chase & Co.|JPM|145;McDonald’s Corporation|MCD|270;Merck & Company, Inc.|MRK|110;Microsoft Corporation|MSFT|240;Nike, Inc.|NKE|130;Pfizer Inc.|PFE|50;Proctor & Gamble Co.|PG|150;The Travelers Companies, Inc.|TRV|195;UnitedHealth Group, Inc.|UNH|490;United Technologies Corporation|UTX|40;Verizon Communications Inc.|VZ|40;Visa Inc.|V|225;Walmart Inc.|WMT|145;Walgreens Boots Alliance, Inc.|WBA|35;The Walt Disney Company|DIS|100";
    static {
        for (String s : SSTRING.split(";")) S_TICKER.add(s);
    }
}
