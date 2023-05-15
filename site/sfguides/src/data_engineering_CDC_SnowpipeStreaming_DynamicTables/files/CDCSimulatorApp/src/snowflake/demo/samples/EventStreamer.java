package snowflake.demo.samples;
import java.util.Properties;
import java.text.DecimalFormat;
import java.text.DecimalFormatSymbols;
import java.util.Locale;

// Sample data generator (Extend to specific use case)
public class EventStreamer  {
    private static final java.util.Random R=new java.util.Random();
    public static java.text.DecimalFormat NF_AMT = (DecimalFormat)DecimalFormat.getInstance(Locale.ENGLISH);
    public boolean DEBUG=false;

    public EventStreamer() {
    }

    public void setProperties(Properties p) throws Exception {
        String debug=p.getProperty("DEBUG");
        if(debug!=null) DEBUG=Boolean.parseBoolean(debug);
    }
    public EventStreamer(Properties p) throws Exception {
        setProperties(p);
    }

    public String getEvent(int transactionid) throws Exception {
        throw new Exception ("Developer should extend this class to make the event payload");
    }

    public static int randomInt(int low, int high){
        return R.nextInt(high-low) + low;
    }

    public static double randomDouble(int low, int high){
        return R.nextDouble()*(high-low) + low;
    }

    static {
        NF_AMT.setMinimumFractionDigits(2);
        NF_AMT.setMaximumFractionDigits(2);
        NF_AMT.setGroupingUsed(false);
        DecimalFormatSymbols otherSymbols = new DecimalFormatSymbols();
        otherSymbols.setDecimalSeparator('.');
        NF_AMT.setDecimalFormatSymbols(otherSymbols);
    }
}
