import io.vertx.core.Vertx;
import io.vertx.core.Handler;
import io.vertx.core.http.HttpConnection;
import java.lang.reflect.Field;
import java.net.Socket;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import org.hyperledger.besu.ethereum.api.jsonrpc.JsonRpcHttpService;

public class HttpLifecycleTest {
  static AtomicInteger counter;
  static void count(int expected) throws Exception {
    for (int i=0;i<100 && counter.get()!=expected;i++) Thread.sleep(10);
    if(counter.get()!=expected) throw new AssertionError("Expected "+expected+" HTTP connections, got "+counter.get());
  }
  public static void main(String[] args) throws Exception {
    // Constructor bypass is restricted to this disposable test: only the real connection handler is exercised.
    Field unsafeField = sun.misc.Unsafe.class.getDeclaredField("theUnsafe"); unsafeField.setAccessible(true);
    sun.misc.Unsafe unsafe = (sun.misc.Unsafe)unsafeField.get(null);
    var service = (JsonRpcHttpService)unsafe.allocateInstance(JsonRpcHttpService.class);
    Field field=JsonRpcHttpService.class.getDeclaredField("activeConnectionsCount"); field.setAccessible(true);
    counter=new AtomicInteger(); field.set(service,counter);
    field=JsonRpcHttpService.class.getDeclaredField("maxActiveConnections"); field.setAccessible(true); field.setInt(service,3);
    var method=JsonRpcHttpService.class.getDeclaredMethod("connectionHandler"); method.setAccessible(true);
    @SuppressWarnings("unchecked") Handler<HttpConnection> handler=(Handler<HttpConnection>)method.invoke(service);
    Vertx vertx=Vertx.vertx();
    var server=vertx.createHttpServer().connectionHandler(handler).requestHandler(req->req.response().end(io.vertx.core.buffer.Buffer.buffer(new byte[1024*1024])));
    try {
      server.listen(0,"127.0.0.1").toCompletionStage().toCompletableFuture().get(5,TimeUnit.SECONDS);
      int port=server.actualPort();
      for(int i=0;i<30;i++) {
        Socket socket=new Socket("127.0.0.1",port);
        socket.getOutputStream().write("GET / HTTP/1.1\r\nHost: localhost\r\n\r\n".getBytes());
        socket.getInputStream().read(new byte[512]); count(1); socket.close(); count(0);
      }
      for(int i=0;i<30;i++) {
        Socket socket=new Socket("127.0.0.1",port); socket.setSoLinger(true,0);
        socket.getOutputStream().write("GET / HTTP/1.1\r\nHost: localhost\r\n\r\n".getBytes());
        socket.getInputStream().read(new byte[512]); socket.close(); count(0);
      }
      System.out.println("PASS: 30 reset connections during large HTTP responses release all slots");
      List<Socket> held=new ArrayList<>();
      for(int i=0;i<3;i++) {
        Socket socket=new Socket("127.0.0.1",port);
        socket.getOutputStream().write("GET / HTTP/1.1\r\nHost: localhost\r\n\r\n".getBytes());
        socket.getInputStream().read(new byte[512]); held.add(socket);
      }
      count(3);
      for(int i=0;i<20;i++) {
        try(Socket rejected=new Socket("127.0.0.1",port)) {
          rejected.setSoTimeout(3000); rejected.getOutputStream().write("GET / HTTP/1.1\r\nHost: localhost\r\n\r\n".getBytes());
          try { if(rejected.getInputStream().read()!=-1) throw new AssertionError("HTTP limit bypassed"); } catch(java.net.SocketException expected){}
        }
        count(3);
      }
      for(Socket socket:held) socket.close(); count(0);
      System.out.println("PASS: HTTP disconnects release slots; 20 rejected connections retain count at limit; all slots recovered");
    } finally {server.close().toCompletionStage().toCompletableFuture().get(5,TimeUnit.SECONDS); vertx.close().toCompletionStage().toCompletableFuture().get(5,TimeUnit.SECONDS);}
  }
}
