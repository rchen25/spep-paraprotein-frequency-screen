package spep;

import javax.ws.rs.ApplicationPath;
import org.glassfish.jersey.server.ResourceConfig;
import org.glassfish.jersey.jackson.JacksonFeature;
import org.glassfish.jersey.media.multipart.MultiPartFeature;

@ApplicationPath("resources")
public class JerseyRestApplication extends ResourceConfig {
    public JerseyRestApplication() {
         packages("spep");
         register(JacksonFeature.class);
         register(JerseyMapperProvider.class);
         register(MultiPartFeature.class);
    }
}
