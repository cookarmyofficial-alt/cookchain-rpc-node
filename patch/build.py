from pathlib import Path
import urllib.request
import hashlib
import subprocess
import os

root = Path(__file__).resolve().parent
url = 'https://raw.githubusercontent.com/besu-eth/besu/26.9.0/ethereum/api/src/main/java/org/hyperledger/besu/ethereum/api/jsonrpc/websocket/WebSocketService.java'
source = urllib.request.urlopen(url, timeout=30).read().decode()
assert hashlib.sha256(source.encode()).hexdigest() == '57f4566088e9b1c30f71c001515ae42304a7e445d0e8ce657f270784d81ed643', 'Upstream source differs from the reviewed source'
(root / 'WebSocketService.original.java').write_text(source)
print('Original source SHA256:', hashlib.sha256(source.encode()).hexdigest())
source = source.replace('import java.util.concurrent.CompletableFuture;', 'import java.util.concurrent.CompletableFuture;\nimport java.util.concurrent.ConcurrentHashMap;\nimport java.util.concurrent.atomic.AtomicBoolean;')
source = source.replace('private final AtomicInteger activeConnectionsCount = new AtomicInteger();', 'private final AtomicInteger activeConnectionsCount = new AtomicInteger();\n  private final ConcurrentHashMap<String, AtomicBoolean> connectionReleases = new ConcurrentHashMap<>();')
start = source.index('  private Handler<HttpConnection> connectionHandler() {')
end = source.index('  private Handler<HttpServerRequest> httpHandler()', start)
source = source[:start] + '''  private Handler<HttpConnection> connectionHandler() {
    return connection -> {
      int count;
      do {
        count = activeConnectionsCount.get();
        if (count >= maxActiveConnections) {
          LOG.warn("Rejecting new connection from {}. {}/{} max active connections limit reached.",
              connection.remoteAddress(), count, maxActiveConnections);
          connection.close();
          return;
        }
      } while (!activeConnectionsCount.compareAndSet(count, count + 1));

      final String key = connection.remoteAddress().toString();
      final AtomicBoolean released = new AtomicBoolean();
      connectionReleases.put(key, released);
      connection.closeHandler(ignored -> releaseConnection(key, released));
      if (connection instanceof io.vertx.core.net.impl.ConnectionBase base) {
        base.channel().closeFuture().addListener(ignored -> releaseConnection(key, released));
      }
    };
  }

  private void releaseConnection(final String key, final AtomicBoolean released) {
    if (released != null && released.compareAndSet(false, true)) {
      connectionReleases.remove(key, released);
      activeConnectionsCount.decrementAndGet();
    }
  }

''' + source[end:]
needle = '                final SocketAddress socketAddress = websocket.remoteAddress();'
assert source.count(needle) == 1
source = source.replace(needle, needle + '\n                final AtomicBoolean connectionReleased = connectionReleases.get(socketAddress.toString());')
needle = '                      LOG.debug(\n                          "Websocket Disconnected ({})", socketAddressAsString(socketAddress));'
assert source.count(needle) == 1
source = source.replace(needle, '                      releaseConnection(socketAddress.toString(), connectionReleased);\n' + needle)
(root / 'WebSocketService.java').write_text(source)
http_url = url.replace('websocket/WebSocketService.java','JsonRpcHttpService.java')
http = urllib.request.urlopen(http_url, timeout=30).read().decode()
(root / 'JsonRpcHttpService.original.java').write_text(http)
http = http.replace('import java.util.concurrent.atomic.AtomicInteger;', 'import java.util.concurrent.atomic.AtomicInteger;\nimport java.util.concurrent.atomic.AtomicBoolean;')
start = http.index('  private Handler<HttpConnection> connectionHandler() {')
end = http.index('  private Router buildRouter()', start)
http = http[:start] + '''  private Handler<HttpConnection> connectionHandler() {
    return connection -> {
      int count;
      do {
        count = activeConnectionsCount.get();
        if (count >= maxActiveConnections) {
          LOG.warn("Rejecting new connection from {}. Max {} active connections limit reached.", connection.remoteAddress(), maxActiveConnections);
          connection.close();
          return;
        }
      } while (!activeConnectionsCount.compareAndSet(count, count + 1));
      final AtomicBoolean released = new AtomicBoolean();
      final Runnable release = () -> {
        if (released.compareAndSet(false, true)) activeConnectionsCount.decrementAndGet();
      };
      connection.closeHandler(ignored -> release.run());
      if (connection instanceof io.vertx.core.net.impl.ConnectionBase base) {
        base.channel().closeFuture().addListener(ignored -> release.run());
      }
    };
  }

''' + http[end:]
(root / 'JsonRpcHttpService.java').write_text(http)
image = 'hyperledger/besu:26.9.0@sha256:fc1813d67d630d7660eea6ee555c01e73bfecda3e54d24f9484c1c4a52c6fcb0'
base = ['docker', 'run', '--rm', '--network', 'none', '--hostname', 'localhost', '--memory', '512m', '--cpus', '1', '--user', f'{os.getuid()}:{os.getgid()}', '-v', f'{root}:/work', '--entrypoint', '/opt/java/openjdk/bin/java', image]
compile_cmd = base.copy()
compile_cmd[compile_cmd.index('/opt/java/openjdk/bin/java')] = '/opt/java/openjdk/bin/javac'
subprocess.run(compile_cmd + ['-cp', '/opt/besu/lib/*', '-d', '/work/classes', '/work/WebSocketService.java', '/work/JsonRpcHttpService.java', '/work/LifecycleTest.java', '/work/HttpLifecycleTest.java'], check=True)
# The same lifecycle test must reproduce the fault on the original packaged class.
baseline = subprocess.run(base + ['-cp', '/opt/besu/lib/*:/work/classes', 'LifecycleTest'], capture_output=True, text=True)
(root / 'baseline-test.log').write_text(baseline.stdout + baseline.stderr)
assert baseline.returncode != 0 and 'Expected 0 active connections, got 1' in baseline.stderr, 'Original defect was not reproduced'
print('PASS: original Besu class reproduces the closed-WebSocket counter leak')
# Isolated container: no production data or keys, and no network outside its own loopback.
subprocess.run(base + ['-cp', '/work/classes:/opt/besu/lib/*', 'LifecycleTest'], check=True)
http_baseline = subprocess.run(base + ['-cp','/opt/besu/lib/*:/work/classes','HttpLifecycleTest'],capture_output=True,text=True)
(root / 'http-baseline-test.log').write_text(http_baseline.stdout+http_baseline.stderr)
print('HTTP original baseline exit:', http_baseline.returncode)
subprocess.run(base + ['-cp', '/work/classes:/opt/besu/lib/*', 'HttpLifecycleTest'], check=True)
