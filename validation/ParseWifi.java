import com.google.zxing.BarcodeFormat;
import com.google.zxing.Result;
import com.google.zxing.client.result.WifiParsedResult;
import com.google.zxing.client.result.WifiResultParser;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.Base64;

public class ParseWifi {
  static String encode(String value) {
    return value == null ? "-" : Base64.getEncoder().encodeToString(value.getBytes(StandardCharsets.UTF_8));
  }
  public static void main(String[] args) throws Exception {
    BufferedReader input = new BufferedReader(new InputStreamReader(System.in, StandardCharsets.UTF_8));
    String line;
    while ((line = input.readLine()) != null) {
      byte[] bytes = Base64.getDecoder().decode(line);
      Result raw = new Result(new String(bytes, StandardCharsets.UTF_8), bytes, null, BarcodeFormat.QR_CODE);
      WifiParsedResult result = new WifiResultParser().parse(raw);
      if (result == null) {
        System.out.println("INVALID");
      } else {
        System.out.println(encode(result.getSsid()) + "\t" + encode(result.getPassword()) + "\t"
            + encode(result.getNetworkEncryption()) + "\t" + result.isHidden() + "\t"
            + encode(result.getIdentity()) + "\t" + encode(result.getAnonymousIdentity()) + "\t"
            + encode(result.getEapMethod()) + "\t" + encode(result.getPhase2Method()));
      }
    }
  }
}
