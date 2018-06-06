package io.sease.rre.server.deserializers;

import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.TreeNode;
import com.fasterxml.jackson.databind.DeserializationContext;
import com.fasterxml.jackson.databind.JsonDeserializer;
import io.sease.rre.core.domain.metrics.Metric;
import org.springframework.boot.jackson.JsonComponent;

import java.io.IOException;
import java.util.LinkedHashMap;

@JsonComponent("metrics")
public class MetricDeserializer extends JsonDeserializer<LinkedHashMap<String, Metric>> {
  
    @Override
    public LinkedHashMap<String, Metric> deserialize(JsonParser jsonParser, DeserializationContext deserializationContext) throws IOException,
            JsonProcessingException {
  
        TreeNode treeNode = jsonParser.getCodec().readTree(jsonParser);
        TreeNode favoriteColor =  treeNode.get("favoriteColor");
        return new LinkedHashMap<>();
        //return new StaticMetric("M", new BigDecimal(1.1));
    }
}