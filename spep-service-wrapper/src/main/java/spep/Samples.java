package spep;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.io.PrintStream;
import javax.ws.rs.BadRequestException;
import javax.ws.rs.Consumes;
import javax.ws.rs.GET;
import javax.ws.rs.POST;
import javax.ws.rs.Path;
import javax.ws.rs.PathParam;
import javax.ws.rs.QueryParam;
import javax.ws.rs.Produces;

@Path("samples")
public class Samples {
    
    // @todo I dislike some of the naming conventions mixing camel-case and underscores
    @JsonIgnoreProperties(ignoreUnknown = true) 
    public static class Sample {
        @JsonProperty("sebiaSerumCurve")
        public String sebiaSerumCurveHex;
        @JsonProperty("sebiaSerumGelControlCurve")
        public String sebiaSerumGelControlCurveHex;
        @JsonProperty("sebiaSerumCurve_intArr")
        public Integer[] sebiaSerumCurveInt;
        @JsonProperty("sebiaSerumGelControlCurve_intArr")
        public Integer[] sebiaSerumGelControlCurveInt;
        @JsonProperty("gamma_region_cutoff")
        public Integer gammaRegionCutoff;
        @JsonProperty("prediction")
        public Integer prediction;
	@JsonProperty("scikitLearnModelName")
	public String scikitLearnModelName;
        public Sample() {
        }
        public Sample(String model) {
            this.scikitLearnModelName = model;
        }
    }

    @GET
    @Produces("application/json")
    public Sample getJson(@QueryParam("model") String model) throws IOException {

        if(model == null || model.length() == 0) { model = "euh-immunology-v1.0"; }
        if(!"euh-immunology-v1.0".equals(model)) { throw new RuntimeException("Currently, only model 'euh-immunology-v1.0' is supported."); }

        return new Sample(model);

    }

    @GET
    @Path("{sampleCurve}/{controlCurve}")
    @Produces("application/json")
    public Sample getJson(@PathParam("sampleCurve") String sampleCurve, @PathParam("controlCurve") String controlCurve, @QueryParam("model") String model) throws IOException, InterruptedException {

        if(model == null || model.length() == 0) { model = "euh-immunology-v1.0"; }
        if(!"euh-immunology-v1.0".equals(model)) { throw new RuntimeException("Currently, only model 'euh-immunology-v1.0' is supported."); }

        Sample sample = new Sample(model);
        sample.sebiaSerumCurveHex = sampleCurve;
        sample.sebiaSerumGelControlCurveHex = controlCurve;
        sample = postJson(sample, model);

        return sample;

    }
    
    @POST
    @Consumes("application/json")
    @Produces("application/json")
    public Sample postJson(Sample sample, @QueryParam("model") String model) throws IOException, InterruptedException {

        if(model == null || model.length() == 0) { model = "euh-immunology-v1.0"; }
        if(!"euh-immunology-v1.0".equals(model)) { throw new RuntimeException("Currently, only model 'euh-immunology-v1.0' is supported."); }

        File csvFile = File.createTempFile("sample", ".csv");
        PrintStream csvPrintStream = new PrintStream(csvFile);
        csvPrintStream.println(String.format("%s,%s", "sebiaSerumCurve", "sebiaSerumGelControlCurve"));
        csvPrintStream.println(String.format("%s,%s", sample.sebiaSerumCurveHex, sample.sebiaSerumGelControlCurveHex));
        csvPrintStream.close();
        String commandLine = String.format(
            "cd /home/ec2-user/spep-paraprotein-frequency-screen && python3 paraprotein_screen.py %s",
            csvFile.getAbsoluteFile()
        );
        ProcessBuilder pb = new ProcessBuilder(new String[] {"sh"});
        pb.redirectErrorStream(true);
        Process p = pb.start();
        try (BufferedWriter pWriter = new BufferedWriter(new OutputStreamWriter(p.getOutputStream()))) {
            pWriter.write(commandLine);
        }
        BufferedReader pReader = new BufferedReader(new InputStreamReader(p.getInputStream()));
        StringBuffer pSb = new StringBuffer();
        String pLine;
        while ((pLine = pReader.readLine()) != null) {
            pSb.append(pLine);
        }
        pReader.close();
        int exitCode = p.waitFor();
        csvFile.delete();
        
        if(exitCode != 0) {
            throw new BadRequestException();
        }

        ObjectMapper om = new ObjectMapper();
        // Jackson rejects the quotation marks around the integer arrays, so I am stripping them
        Sample[] samples = om.readValue(pSb.toString().replaceAll("\"\\[", "\\[").replaceAll("\\]\"", "\\]"), Sample[].class);

	samples[0].scikitLearnModelName = model;
        return samples[0];

    }

}
