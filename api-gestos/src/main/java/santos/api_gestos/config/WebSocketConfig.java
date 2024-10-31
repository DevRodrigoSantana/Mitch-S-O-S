package santos.api_gestos.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.socket.config.annotation.EnableWebSocket;
import org.springframework.web.socket.config.annotation.WebSocketConfigurer;
import org.springframework.web.socket.config.annotation.WebSocketHandlerRegistry;
import santos.api_gestos.serveSocket.WebSocketHandlerOne;

@Configuration
@EnableWebSocket
public class WebSocketConfig implements WebSocketConfigurer {

    private final WebSocketHandlerOne webSocketHandlerOne;

    public WebSocketConfig(WebSocketHandlerOne webSocketHandlerOne) {
        this.webSocketHandlerOne = webSocketHandlerOne;
    }

    @Override
    public void registerWebSocketHandlers(WebSocketHandlerRegistry registry) {
        
        registry.addHandler(webSocketHandlerOne, "/ws1").setAllowedOrigins("*");
    }
}
