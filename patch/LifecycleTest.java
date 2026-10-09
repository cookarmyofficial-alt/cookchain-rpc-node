import io.vertx.core.Vertx;
import java.lang.reflect.Proxy;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.WebSocket;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import org.hyperledger.besu.ethereum.api.jsonrpc.websocket.WebSocketConfiguration;
import org.hyperledger.besu.ethereum.api.jsonrpc.websocket.WebSocketService;
import org.hyperledger.besu.plugin.services.MetricsSystem;

public class LifecycleTest {
  static AtomicInteger counter;
  static void count(int expected) throws Exception {
    for (int i = 0; i < 100 && counter.get() != expected; i++) Thread.sleep(20);
    if (counter.get() != expected) throw new AssertionError("Expected " + expected + " active connections, got " + counter.get());
  }
  public static void main(String[] args) throws Exception {
    Vertx vertx = Vertx.vertx();
    WebSocketConfiguration config = WebSocketConfiguration.createDefault();
    config.setHost("127.0.0.1"); config.setPort(0); config.setMaxActiveConnections(3);
    config.setHostsAllowlist(List.of("127.0.0.1", "localhost"));
    MetricsSystem metrics = (MetricsSystem) Proxy.newProxyInstance(MetricsSystem.class.getClassLoader(), new Class<?>[]{MetricsSystem.class}, (p, m, a) -> null);
    WebSocketService service = new WebSocketService(vertx, config, null, Optional.empty(), metrics);
    var field = WebSocketService.class.getDeclaredField("activeConnectionsCount"); field.setAccessible(true);
    counter = (AtomicInteger) field.get(service);
    try (HttpClient client = HttpClient.newHttpClient()) {
      service.start().get(10, TimeUnit.SECONDS);
      URI uri = URI.create("ws://127.0.0.1:" + service.socketAddress().getPort());
      WebSocket.Listener listener = new WebSocket.Listener(){};
      for (int i = 0; i < 30; i++) {
        WebSocket ws = client.newWebSocketBuilder().buildAsync(uri, listener).get(5, TimeUnit.SECONDS);
        count(1); ws.sendClose(1000, "test").get(5, TimeUnit.SECONDS); count(0);
      }
      System.out.println("PASS: 30 sequential upgraded connections close without counter drift");
      List<WebSocket> held = new ArrayList<>();
      for (int i = 0; i < 3; i++) held.add(client.newWebSocketBuilder().buildAsync(uri, listener).get(5, TimeUnit.SECONDS));
      count(3);
      for (int i = 0; i < 5; i++) {
        try { client.newWebSocketBuilder().buildAsync(uri, listener).get(5, TimeUnit.SECONDS); throw new AssertionError("Limit bypassed"); }
        catch (java.util.concurrent.ExecutionException expected) { count(3); }
      }
      held.forEach(WebSocket::abort); count(0);
      System.out.println("PASS: rejected connections do not increase count; abrupt close releases all slots");
      WebSocket finalWs = client.newWebSocketBuilder().buildAsync(uri, listener).get(5, TimeUnit.SECONDS);
      count(1); finalWs.abort(); count(0);
      System.out.println("PASS: connections remain available after reaching the cap");
    } finally { service.stop().get(10, TimeUnit.SECONDS); vertx.close().toCompletionStage().toCompletableFuture().get(10, TimeUnit.SECONDS); }
  }
}
