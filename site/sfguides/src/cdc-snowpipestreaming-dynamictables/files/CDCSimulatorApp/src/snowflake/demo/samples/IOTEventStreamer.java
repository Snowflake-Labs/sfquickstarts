package snowflake.demo.samples;
import java.io.File;
import java.io.BufferedReader;
import java.io.FileReader;
import java.util.HashMap;
import java.time.Instant;
import java.util.Properties;

// Sample data generator (IOT Device Events)
public class IOTEventStreamer  extends EventStreamer {
    private static HashMap<Integer,String[]> DATA = new HashMap<Integer,String[]>();
    private static HashMap<Integer,Integer> DEVICES = null;
    private boolean SHOW_EVENTS=false;
    private int NUM_DEVICES=100;
    private int LAST_DEVICE=1;

    public IOTEventStreamer() throws Exception {
    }

    public IOTEventStreamer(Properties p) throws Exception {
        setProperties(p);
    }

    public void setProperties(Properties p) throws Exception {
        super.setProperties(p);
        DEVICES = new HashMap<Integer,Integer>();
        String showevents=p.getProperty("SHOW_EVENTS");
        if(showevents!=null) SHOW_EVENTS=Boolean.parseBoolean(showevents);
        String file=p.getProperty("IOT_DATA_FILE");
        if(file==null) throw new Exception ("Parameter 'DATA_FILE' is required");
        File f =new File(file);
        if(!f.exists()) throw new Exception ("Data File '"+file+"' is not found");
        loadData(f);
    }

    public String getEvent(int transactionid) throws Exception {
        while (DEVICES.size()<NUM_DEVICES) DEVICES.put(LAST_DEVICE++,1); // always have 100 devices active
        int device=(Integer)DEVICES.keySet().toArray()[randomInt(0,DEVICES.size()-1)];  //select an active device at random
        int cycle=DEVICES.get(device); // get current cycle for this device

        // if device is at its failure point, remove it from service and replace with new
        if(cycle>DATA.size()-1) {
            DEVICES.remove(device);
            LAST_DEVICE++;
        }
        else DEVICES.replace(device,nextCycleNum(cycle)); //else increment the device's cycle
        long event_time = Instant.now().toEpochMilli();  // simulated timestamp the event occurred
        String[] v = (String[])DATA.get(cycle);
        StringBuilder sb = new StringBuilder()
                .append("{")
                  .append("\"UNIT_NUMBER\":"+v[0]+",")
                  .append("\"TIMESTAMP\":"+event_time+",")
                  .append("\"TIME_IN_CYCLES\":"+cycle+",")
                  .append("\"SETTING_1\":"+v[1]+",")
                  .append("\"SETTING_2\":"+v[2]+",")
                  .append("\"T2\":"+v[3]+",")
                  .append("\"T24\":"+v[4]+",")
                  .append("\"T30\":"+v[5]+",")
                  .append("\"T50\":"+v[6]+",")
                  .append("\"P2\":"+v[7]+",")
                  .append("\"P15\":"+v[8]+",")
                  .append("\"P30\":"+v[9]+",")
                  .append("\"NF\":"+v[10]+",")
                  .append("\"NC\":"+v[11]+",")
                  .append("\"EPR\":"+v[12]+",")
                  .append("\"PS30\":"+v[13]+",")
                  .append("\"PHI\":"+v[14]+",")
                  .append("\"NRF\":"+v[15]+",")
                  .append("\"NRC\":"+v[16]+",")
                  .append("\"BPR\":"+v[17]+",")
                  .append("\"FARB\":"+v[18]+",")
                  .append("\"HTBLEED\":"+v[19]+",")
                  .append("\"NF_DMD\":"+v[20]+",")
                  .append("\"PCNRF_DMD\":"+v[21])
                .append("}");
        if(SHOW_EVENTS) System.out.println("EVENT | DEVICE | CYCLE = "+transactionid+" | "+device+" | "+cycle);
        else if (DEBUG) System.out.println(sb);
        return sb.toString();
    }

    private static int nextCycleNum(int cycle){ // simulates shortened life than ideal
        int random=randomInt(1,100);
        if(random<=5) return cycle;
        else if (random>85 && cycle<=DATA.size()-2) return cycle+2;
        else return cycle+1;
    }

    private static void loadData(File f) throws Exception { // load IOT data file
        BufferedReader r = new BufferedReader(new FileReader(f));
        String line;
        while ((line = r.readLine()) != null) {
            String[] values = line.split(",");
            DATA.put(Integer.parseInt(values[0]), values);
        }
    }
}
