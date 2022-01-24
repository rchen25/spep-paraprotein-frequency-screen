# spep-service-wrapper
A RESTful web service API for spep-paraprotein-frequency-screen.
These services wrap the Python methods in the main project and are implemented as a JAX-RS application deployed in a Java application server.

Build with maven (mvn package) and deploy the WAR file in your Java application server.
The demonstration implementation of the services at https://trddx.emory.edu/spep is deployed under Apache Tomcat.
